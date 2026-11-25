from __future__ import annotations

import base64
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import GEMINI_API_KEY, GEMINI_MODEL, OCR_BINARY_PATH


@dataclass
class OCRPage:
    page_number: int
    method: str
    text: str
    avg_confidence: float


@dataclass
class OCRResult:
    ok: bool
    engine: str
    page_count: int
    pages: List[OCRPage] = field(default_factory=list)
    raw_text: str = ""
    quality_score: float = 0.0
    quality_status: str = "good"
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


def _assess_image_quality(file_path: Path) -> tuple[float, List[str]]:
    """Inspect resolution, contrast, and edge sharpness using Pillow."""
    warnings: List[str] = []
    score = 1.0
    try:
        with Image.open(file_path) as img:
            img.verify()
        with Image.open(file_path) as img:
            width, height = img.size
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            stddev = stat.stddev[0] if stat.stddev else 0.0
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_energy = edge_stat.mean[0] if edge_stat.mean else 0.0

            if width < 450 or height < 450:
                warnings.append(
                    f"Low image resolution ({width}x{height}px). Higher resolution (>= 800px) improves medical OCR accuracy."
                )
                score -= 0.25
            if stddev < 16.0:
                warnings.append(
                    "Very low contrast or mostly blank image detected. Text extraction may be incomplete."
                )
                score -= 0.35
            if edge_energy < 4.0:
                warnings.append(
                    "Image appears blurry or lacks sharp text edges. Please verify extracted numbers carefully."
                )
                score -= 0.25
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError(f"Corrupted or unreadable image file: {exc}") from exc

    return max(0.05, min(1.0, score)), warnings


def _run_pypdf_fallback(file_path: Path) -> OCRResult:
    try:
        reader = PdfReader(str(file_path))
    except (PdfReadError, Exception) as exc:
        return OCRResult(
            ok=False,
            engine="pypdf",
            page_count=0,
            error=f"Malformed or unreadable PDF document: {exc}",
        )

    if reader.is_encrypted:
        return OCRResult(
            ok=False,
            engine="pypdf",
            page_count=len(reader.pages),
            error="Password-protected PDFs cannot be processed automatically. Please upload an unlocked PDF.",
        )

    pages: List[OCRPage] = []
    for idx, page in enumerate(reader.pages):
        txt = (page.extract_text() or "").strip()
        pages.append(
            OCRPage(
                page_number=idx + 1,
                method="pdf_text",
                text=txt,
                avg_confidence=0.98 if len(txt) >= 30 else 0.25,
            )
        )

    combined = "\n\n".join(
        f"--- Page {p.page_number} ---\n{p.text}" for p in pages if p.text
    ).strip()

    warnings: List[str] = []
    if len(combined) < 25:
        warnings.append(
            "Little or no readable text was extracted from this PDF. If it is a scanned document, ensure the scan is clear and upright."
        )
        return OCRResult(
            ok=True,
            engine="pypdf",
            page_count=len(pages),
            pages=pages,
            raw_text=combined,
            quality_score=0.2,
            quality_status="poor_quality_scan",
            warnings=warnings,
        )

    return OCRResult(
        ok=True,
        engine="pypdf",
        page_count=len(pages),
        pages=pages,
        raw_text=combined,
        quality_score=0.96,
        quality_status="good",
        warnings=warnings,
    )


def extract_document_text(file_path: Path, mime_type: str) -> OCRResult:
    """Extract text with page numbers from PDF, JPG, JPEG, or PNG."""
    warnings: List[str] = []
    image_quality = 1.0

    if mime_type in {"image/jpeg", "image/jpg", "image/png"}:
        try:
            image_quality, img_warnings = _assess_image_quality(file_path)
            warnings.extend(img_warnings)
        except ValueError as exc:
            return OCRResult(ok=False, engine="pillow_check", page_count=0, error=str(exc))
    elif mime_type == "application/pdf":
        # Validate PDF structure upfront via pypdf
        try:
            reader = PdfReader(str(file_path))
            if reader.is_encrypted:
                return OCRResult(
                    ok=False,
                    engine="pypdf_validation",
                    page_count=len(reader.pages),
                    error="Encrypted PDFs are not supported. Please provide an unencrypted medical report.",
                )
            if len(reader.pages) == 0:
                return OCRResult(
                    ok=False,
                    engine="pypdf_validation",
                    page_count=0,
                    error="The PDF contains zero pages.",
                )
        except Exception as exc:
            return OCRResult(
                ok=False,
                engine="pypdf_validation",
                page_count=0,
                error=f"Malformed or corrupted PDF file: {exc}",
            )

    if OCR_BINARY_PATH.exists():
        try:
            proc = subprocess.run(
                [str(OCR_BINARY_PATH), str(file_path)],
                capture_output=True,
                text=True,
                timeout=45,
            )
            if proc.stdout.strip():
                payload = json.loads(proc.stdout.strip())
                if not payload.get("ok"):
                    gem_res = _run_gemini_vision_ocr(file_path, mime_type, warnings, image_quality)
                    if gem_res is not None:
                        return gem_res
                    err_detail = payload.get("error") or "OCR processing failed."
                    if warnings:
                        err_detail = f"{err_detail} ({' '.join(warnings)})"
                    return OCRResult(
                        ok=False,
                        engine="apple_vision_pdfkit",
                        page_count=0,
                        error=err_detail,
                    )
                pages = [
                    OCRPage(
                        page_number=int(p["page_number"]),
                        method=str(p["method"]),
                        text=str(p["text"]).strip(),
                        avg_confidence=float(p["avg_confidence"]),
                    )
                    for p in payload.get("pages", [])
                ]
                # If PDF embedded text extraction yielded very thin text on a digital PDF, check pypdf too
                if mime_type == "application/pdf" and all(len(p.text) < 20 for p in pages):
                    pypdf_res = _run_pypdf_fallback(file_path)
                    if pypdf_res.ok and len(pypdf_res.raw_text) > sum(len(p.text) for p in pages):
                        return pypdf_res

                combined = "\n\n".join(
                    f"--- Page {p.page_number} ---\n{p.text}" for p in pages if p.text
                ).strip()
                avg_conf = (
                    sum(p.avg_confidence for p in pages) / len(pages) if pages else 0.0
                )
                quality_score = round(min(avg_conf, image_quality), 3)

                if len(combined) < 20:
                    warnings.append(
                        "Very little text could be recognized from this scan. Please upload a clearer, well-lit image or digital PDF."
                    )
                    quality_status = "poor_quality_scan"
                elif quality_score < 0.65 or len(warnings) >= 2:
                    warnings.append(
                        "Scan quality is below optimal threshold; extracted medical values should be manually verified against the source image."
                    )
                    quality_status = "fair"
                else:
                    quality_status = "good"

                return OCRResult(
                    ok=True,
                    engine="apple_vision_pdfkit",
                    page_count=int(payload.get("page_count", len(pages))),
                    pages=pages,
                    raw_text=combined,
                    quality_score=quality_score,
                    quality_status=quality_status,
                    warnings=warnings,
                )
        except subprocess.TimeoutExpired:
            warnings.append("Native OCR timed out; falling back to PDF parser.")
        except Exception as exc:
            warnings.append(f"Native OCR fallback triggered: {exc}")

    if mime_type == "application/pdf":
        return _run_pypdf_fallback(file_path)

    return OCRResult(
        ok=False,
        engine="unavailable",
        page_count=0,
        error="OCR engine unavailable for image processing.",
    )


def _run_gemini_vision_ocr(file_path: Path, mime_type: str, existing_warnings: List[str], image_quality: float) -> Optional[OCRResult]:
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        b64_data = base64.b64encode(file_path.read_bytes()).decode("ascii")
        block_type = "document" if mime_type == "application/pdf" else "image"
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=[
                {
                    "type": "text",
                    "text": (
                        "Perform verbatim OCR on this medical document. Transcribe all visible text, "
                        "numbers, units, and reference intervals accurately, preserving line breaks. "
                        "If the image is unreadable or blank, state 'UNREADABLE_SCAN'."
                    ),
                },
                {"type": block_type, "data": b64_data, "mime_type": mime_type},
            ],
        )
        text = (interaction.output_text or "").strip()
        if not text or "UNREADABLE_SCAN" in text:
            return OCRResult(
                ok=False,
                engine=f"gemini_vision:{GEMINI_MODEL}",
                page_count=1,
                error="Poor-quality or unreadable scan: no legible medical text was detected.",
            )
        warnings = list(existing_warnings)
        quality_status = "good" if image_quality >= 0.7 else "fair"
        return OCRResult(
            ok=True,
            engine=f"gemini_vision:{GEMINI_MODEL}",
            page_count=1,
            pages=[OCRPage(page_number=1, method="gemini_vision_ocr", text=text, avg_confidence=0.92)],
            raw_text=f"--- Page 1 ---\n{text}",
            quality_score=round(min(0.92, image_quality), 3),
            quality_status=quality_status,
            warnings=warnings,
        )
    except Exception:
        return None
