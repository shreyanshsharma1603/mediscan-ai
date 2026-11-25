from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from app.config import DOCUMENT_TYPES, MEDICAL_DISCLAIMER, SUPPORTED_LANGUAGES, UPLOAD_DIR
from app.database import db_session, parse_json_field, utc_now_iso
from app.services.classifier import classify_document
from app.services.explainer import generate_analysis_explanation
from app.services.extractor import extract_medical_entities
from app.services.ocr_engine import OCRPage, extract_document_text


def _store_entities_and_labs(
    conn,
    document_id: str,
    user_id: str,
    entities: list[dict],
    lab_findings: list[dict],
) -> None:
    now = utc_now_iso()
    conn.execute("DELETE FROM extracted_entities WHERE document_id = ? AND user_id = ?", (document_id, user_id))
    conn.execute("DELETE FROM laboratory_findings WHERE document_id = ? AND user_id = ?", (document_id, user_id))

    for ent in entities:
        conn.execute(
            """
            INSERT INTO extracted_entities (
                id, document_id, user_id, entity_type, name, value, unit, reference_range,
                date_value, dosage, frequency, duration, observation, source_page,
                source_snippet, confidence, needs_verification, verification_reason,
                verified_by_user, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                ent["id"],
                document_id,
                user_id,
                ent["entity_type"],
                ent["name"],
                ent.get("value"),
                ent.get("unit"),
                ent.get("reference_range"),
                ent.get("date_value"),
                ent.get("dosage"),
                ent.get("frequency"),
                ent.get("duration"),
                ent.get("observation"),
                int(ent.get("source_page", 1)),
                ent.get("source_snippet", ""),
                float(ent.get("confidence", 0.8)),
                1 if ent.get("needs_verification") else 0,
                ent.get("verification_reason"),
                now,
            ),
        )

    for lab in lab_findings:
        conn.execute(
            """
            INSERT INTO laboratory_findings (
                id, document_id, user_id, test_name, canonical_test_key, value_numeric,
                value_raw, unit, canonical_unit, ref_low, ref_high, ref_text, status,
                deviation_pct, source_page, source_snippet, confidence, needs_verification,
                verification_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lab["id"],
                document_id,
                user_id,
                lab["test_name"],
                lab["canonical_test_key"],
                lab.get("value_numeric"),
                lab["value_raw"],
                lab.get("unit"),
                lab.get("canonical_unit"),
                lab.get("ref_low"),
                lab.get("ref_high"),
                lab.get("ref_text"),
                lab["status"],
                lab.get("deviation_pct"),
                int(lab.get("source_page", 1)),
                lab.get("source_snippet", ""),
                float(lab.get("confidence", 0.8)),
                1 if lab.get("needs_verification") else 0,
                lab.get("verification_reason"),
                now,
            ),
        )


def process_uploaded_document(
    user: dict,
    original_filename: str,
    ext: str,
    mime_type: str,
    content: bytes,
    language: Optional[str] = None,
    override_report_date: Optional[str] = None,
) -> str:
    doc_id = str(uuid.uuid4())
    user_dir = UPLOAD_DIR / user["id"]
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_path = user_dir / f"{doc_id}{ext}"
    stored_path.write_bytes(content)

    ocr = extract_document_text(stored_path, mime_type)
    if not ocr.ok:
        # Clean up temporary file if validation/OCR failed fatally
        if stored_path.exists():
            stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=ocr.error or "Failed to extract readable medical text from the uploaded file.",
        )

    classification = classify_document(ocr.raw_text, original_filename)
    extraction = extract_medical_entities(
        pages=ocr.pages,
        raw_text=ocr.raw_text,
        doc_type=classification["final_type"],
        quality_score=ocr.quality_score,
    )
    report_date = override_report_date or extraction.get("report_date")
    lang = language if language in SUPPORTED_LANGUAGES else user.get("preferred_language", "en")
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    analysis = generate_analysis_explanation(
        doc_type=classification["final_type"],
        raw_text=ocr.raw_text,
        entities=extraction["entities"],
        lab_findings=extraction["lab_findings"],
        ocr_warnings=ocr.warnings,
        language=lang,
    )

    now = utc_now_iso()
    retention_days = int(user.get("retention_days") or 30)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=retention_days)).isoformat()

    pages_serialized = [
        {
            "page_number": p.page_number,
            "method": p.method,
            "text": p.text,
            "avg_confidence": p.avg_confidence,
        }
        for p in ocr.pages
    ]

    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO medical_documents (
                id, user_id, original_filename, stored_path, mime_type, file_size_bytes,
                page_count, report_date, ocr_engine, ocr_quality_score, ocr_quality_status,
                ocr_warnings_json, raw_ocr_text, pages_json, expires_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                user["id"],
                original_filename,
                str(stored_path),
                mime_type,
                len(content),
                ocr.page_count,
                report_date,
                ocr.engine,
                ocr.quality_score,
                ocr.quality_status,
                json.dumps(ocr.warnings),
                ocr.raw_text,
                json.dumps(pages_serialized),
                expires_at,
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO document_classifications (
                id, document_id, user_id, predicted_type, final_type, confidence,
                is_manual_override, signals_json, candidate_scores_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                doc_id,
                user["id"],
                classification["predicted_type"],
                classification["final_type"],
                classification["confidence"],
                json.dumps(classification["signals"]),
                json.dumps(classification["candidate_scores"]),
                now,
            ),
        )
        _store_entities_and_labs(
            conn,
            doc_id,
            user["id"],
            extraction["entities"],
            extraction["lab_findings"],
        )
        conn.execute(
            """
            INSERT INTO analysis_history (
                id, document_id, user_id, language, ai_provider, summary_json, disclaimer, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                doc_id,
                user["id"],
                lang,
                analysis["ai_provider"],
                json.dumps(analysis),
                MEDICAL_DISCLAIMER,
                now,
            ),
        )

    return doc_id


def reprocess_classification_override(
    user: dict,
    document_id: str,
    new_type: str,
    language: str,
) -> None:
    if new_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid document classification type")

    with db_session() as conn:
        doc_row = conn.execute(
            "SELECT * FROM medical_documents WHERE id = ? AND user_id = ?",
            (document_id, user["id"]),
        ).fetchone()
        if not doc_row:
            raise HTTPException(status_code=404, detail="Medical document not found")

        pages_raw = parse_json_field(doc_row["pages_json"], [])
        pages = [
            OCRPage(
                page_number=p["page_number"],
                method=p["method"],
                text=p["text"],
                avg_confidence=p["avg_confidence"],
            )
            for p in pages_raw
        ]
        ocr_warnings = parse_json_field(doc_row["ocr_warnings_json"], [])
        extraction = extract_medical_entities(
            pages=pages,
            raw_text=doc_row["raw_ocr_text"],
            doc_type=new_type,
            quality_score=float(doc_row["ocr_quality_score"]),
        )
        analysis = generate_analysis_explanation(
            doc_type=new_type,
            raw_text=doc_row["raw_ocr_text"],
            entities=extraction["entities"],
            lab_findings=extraction["lab_findings"],
            ocr_warnings=ocr_warnings,
            language=language,
        )
        now = utc_now_iso()
        conn.execute(
            """
            UPDATE document_classifications
            SET final_type = ?, is_manual_override = 1, updated_at = ?
            WHERE document_id = ? AND user_id = ?
            """,
            (new_type, now, document_id, user["id"]),
        )
        _store_entities_and_labs(
            conn,
            document_id,
            user["id"],
            extraction["entities"],
            extraction["lab_findings"],
        )
        conn.execute(
            """
            INSERT INTO analysis_history (
                id, document_id, user_id, language, ai_provider, summary_json, disclaimer, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                document_id,
                user["id"],
                language,
                analysis["ai_provider"],
                json.dumps(analysis),
                MEDICAL_DISCLAIMER,
                now,
            ),
        )


def fetch_document_detail(user_id: str, document_id: str, language: Optional[str] = None) -> dict:
    with db_session() as conn:
        doc = conn.execute(
            "SELECT * FROM medical_documents WHERE id = ? AND user_id = ?",
            (document_id, user_id),
        ).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Medical document not found")

        cls_row = conn.execute(
            "SELECT * FROM document_classifications WHERE document_id = ? AND user_id = ?",
            (document_id, user_id),
        ).fetchone()
        entities = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM extracted_entities WHERE document_id = ? AND user_id = ? ORDER BY source_page ASC, created_at ASC",
                (document_id, user_id),
            ).fetchall()
        ]
        labs = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM laboratory_findings WHERE document_id = ? AND user_id = ? ORDER BY source_page ASC, created_at ASC",
                (document_id, user_id),
            ).fetchall()
        ]

        target_lang = language if language in SUPPORTED_LANGUAGES else None
        analysis_row = None
        if target_lang:
            analysis_row = conn.execute(
                "SELECT * FROM analysis_history WHERE document_id = ? AND user_id = ? AND language = ? ORDER BY created_at DESC LIMIT 1",
                (document_id, user_id, target_lang),
            ).fetchone()
        if not analysis_row:
            analysis_row = conn.execute(
                "SELECT * FROM analysis_history WHERE document_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT 1",
                (document_id, user_id),
            ).fetchone()

    ocr_warnings = parse_json_field(doc["ocr_warnings_json"], [])
    pages = parse_json_field(doc["pages_json"], [])
    classification = {
        "predicted_type": cls_row["predicted_type"] if cls_row else "other",
        "final_type": cls_row["final_type"] if cls_row else "other",
        "confidence": cls_row["confidence"] if cls_row else 0.5,
        "is_manual_override": bool(cls_row["is_manual_override"]) if cls_row else False,
        "signals": parse_json_field(cls_row["signals_json"], []) if cls_row else [],
        "candidate_scores": parse_json_field(cls_row["candidate_scores_json"], {}) if cls_row else {},
    }

    for e in entities:
        e["needs_verification"] = bool(e["needs_verification"])
        e["verified_by_user"] = bool(e["verified_by_user"])
    for f in labs:
        f["needs_verification"] = bool(f["needs_verification"])

    analysis = parse_json_field(analysis_row["summary_json"], None) if analysis_row else None
    if target_lang and (not analysis or analysis.get("language") != target_lang):
        analysis = generate_analysis_explanation(
            doc_type=classification["final_type"],
            raw_text=doc["raw_ocr_text"],
            entities=entities,
            lab_findings=labs,
            ocr_warnings=ocr_warnings,
            language=target_lang,
        )
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO analysis_history (
                    id, document_id, user_id, language, ai_provider, summary_json, disclaimer, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    document_id,
                    user_id,
                    target_lang,
                    analysis["ai_provider"],
                    json.dumps(analysis),
                    MEDICAL_DISCLAIMER,
                    utc_now_iso(),
                ),
            )

    abnormal_count = sum(1 for f in labs if f["status"] in {"below_range", "above_range"})
    verify_count = sum(1 for f in labs if f["needs_verification"]) + sum(
        1 for e in entities if e["needs_verification"] and e["entity_type"] != "lab_test"
    )
    med_count = sum(1 for e in entities if e["entity_type"] == "medication")

    return {
        "id": doc["id"],
        "original_filename": doc["original_filename"],
        "mime_type": doc["mime_type"],
        "file_size_bytes": doc["file_size_bytes"],
        "page_count": doc["page_count"],
        "report_date": doc["report_date"],
        "ocr_engine": doc["ocr_engine"],
        "ocr_quality_score": doc["ocr_quality_score"],
        "ocr_quality_status": doc["ocr_quality_status"],
        "ocr_warnings": ocr_warnings,
        "classification": classification,
        "lab_count": len(labs),
        "abnormal_count": abnormal_count,
        "verification_needed_count": verify_count,
        "medication_count": med_count,
        "expires_at": doc["expires_at"],
        "created_at": doc["created_at"],
        "raw_ocr_text": doc["raw_ocr_text"],
        "pages": pages,
        "entities": entities,
        "lab_findings": labs,
        "analysis": analysis,
    }
