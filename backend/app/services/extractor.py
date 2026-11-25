from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.services.lab_analyzer import (
    canonicalize_test_name,
    canonicalize_unit,
    evaluate_lab_finding,
)
from app.services.ocr_engine import OCRPage


class GeminiExtractedLab(BaseModel):
    test_name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    source_page: int = 1
    source_snippet: str = ""
    confidence: float = 0.85


class GeminiExtractedMedication(BaseModel):
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    source_page: int = 1
    source_snippet: str = ""
    confidence: float = 0.85
    uncertainty_reason: Optional[str] = None


class GeminiExtractedObservation(BaseModel):
    category: str = Field(description="e.g., radiology_finding, radiology_impression, clinical_observation, diagnosis_note, vital_sign, follow_up")
    title: str
    detail: str
    source_page: int = 1
    source_snippet: str = ""
    confidence: float = 0.85


class GeminiExtractionBundle(BaseModel):
    report_date: Optional[str] = Field(default=None, description="ISO YYYY-MM-DD if found, otherwise original date string")
    dates_found: List[str] = Field(default_factory=list)
    lab_findings: List[GeminiExtractedLab] = Field(default_factory=list)
    medications: List[GeminiExtractedMedication] = Field(default_factory=list)
    observations: List[GeminiExtractedObservation] = Field(default_factory=list)


DATE_PATTERNS = [
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"),
    re.compile(
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
        re.IGNORECASE,
    ),
]

COMMON_UNIT_PATTERN = (
    r"(?:g/dL|gm/dL|g/L|mg/dL|mmol/L|umol/L|µmol/L|U/L|IU/L|mIU/L|uIU/mL|µIU/mL|mEq/L|"
    r"ng/mL|pg/mL|cells/uL|cells/µL|10\^3/uL|x10\^3/uL|10\^3/µL|10\^9/L|x10\^9/L|"
    r"10\^6/uL|10\^12/L|million/uL|lakhs/cumm|mL/min/1\.73m2|/HPF|HPF|fL|pg|%)"
)

LAB_LINE_RE = re.compile(
    rf"^(?P<name>[A-Za-z][A-Za-z0-9\s\-\(\)/,\.%]+?)\s*[:\-|]?\s+"
    rf"(?P<val>(?:[<>]=?\s*)?\d[\d,]*(?:\.\d+)?)\s*"
    rf"(?:(?:\b(?:High|Low|H|L|Abnormal)\b)\s*)?"
    rf"(?:\(?\s*(?P<unit>{COMMON_UNIT_PATTERN})\s*\)?)?\s*"
    rf"(?:(?:\b(?:High|Low|H|L|Abnormal)\b)\s*)?"
    rf"(?:[|(\[]?\s*(?:Ref(?:\.|erence)?\s*(?:Range|Interval)?\s*[:=]?\s*)?"
    rf"(?P<ref>(?:\d+(?:\.\d+)?\s*(?:-|–|—|to)\s*\d+(?:\.\d+)?|(?:<=|<|>=|>|up to)\s*\d+(?:\.\d+)?))(?:\s*[)\]])?)?$",
    re.IGNORECASE,
)

MED_LINE_RE = re.compile(
    r"^(?:\d+[\.\)]\s*|Rx\s*[:\-]?\s*)?(?:Tab\.?|Tablet|Cap\.?|Capsule|Syr\.?|Syrup|Inj\.?|Drops|Cream|Inhaler)?\s*"
    r"(?P<name>[A-Za-z][A-Za-z0-9\-\s]{2,40}?)\s+"
    r"(?P<dose>\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|IU|%)(?:\s*/\s*\d+\s*(?:mg|ml))?)"
    r"(?:\s*[-–,]?\s*(?P<rest>.*))?$",
    re.IGNORECASE,
)

FREQ_PATTERN = re.compile(
    r"\b(once daily|twice daily|thrice daily|three times daily|every \d+ hours|at bedtime|"
    r"morning|evening|with food|after food|before food|OD|BD|BID|TID|QID|HS|SOS|PRN|q\d+h)\b",
    re.IGNORECASE,
)

DURATION_PATTERN = re.compile(
    r"\b(?:for\s+)?(\d+\s*(?:day|days|week|weeks|month|months))\b",
    re.IGNORECASE,
)


def _normalize_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    from datetime import datetime

    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def _extract_dates(pages: List[OCRPage]) -> List[Dict[str, Any]]:
    results = []
    seen = set()
    for page in pages:
        for line in page.text.splitlines():
            for pat in DATE_PATTERNS:
                for m in pat.finditer(line):
                    val = m.group(1).strip()
                    norm = _normalize_date(val)
                    if norm and norm not in seen:
                        seen.add(norm)
                        results.append(
                            {
                                "date": norm,
                                "raw": val,
                                "page": page.page_number,
                                "snippet": line.strip()[:220],
                            }
                        )
    return results


def _deterministic_extract(pages: List[OCRPage], doc_type: str) -> dict:
    dates = _extract_dates(pages)
    report_date = dates[0]["date"] if dates else None

    labs: List[dict] = []
    meds: List[dict] = []
    observations: List[dict] = []

    skip_headers = {
        "patient name", "age", "sex", "gender", "date", "report date", "collected",
        "referred by", "lab no", "patient id", "mrn", "page", "test name", "result",
        "reference range", "units", "phone", "address", "hospital", "clinic",
    }

    current_section = "general"

    for page in pages:
        lines = [ln.strip() for ln in page.text.splitlines() if ln.strip()]
        for line in lines:
            lower = line.lower()

            # Track section headings for radiology / discharge / clinical notes
            if re.match(r"^(findings|impression|technique|indication|conclusion|assessment|plan|chief complaint|vital signs|hospital course|discharge medications|follow-up|medications)\s*:?", lower):
                current_section = re.sub(r":.*$", "", lower).strip()

            # 1. Extract lab analytes (especially for blood_test, urine_test, discharge_summary, clinical_notes)
            if doc_type in {"blood_test", "urine_test", "discharge_summary", "clinical_notes", "other"}:
                m = LAB_LINE_RE.match(line)
                if m:
                    name = m.group("name").strip(" :-\t|")
                    if (
                        len(name) >= 2
                        and name.lower() not in skip_headers
                        and not any(h in name.lower() for h in ("page ", "phone", "fax", "zip", "reg no", "mrn"))
                    ):
                        val_raw = m.group("val").strip()
                        unit = m.group("unit").strip() if m.group("unit") else None
                        ref_text = m.group("ref").strip() if m.group("ref") else None
                        # Avoid capturing dates like 12-05-2026 as lab findings
                        if not re.match(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$", val_raw):
                            labs.append(
                                {
                                    "test_name": name,
                                    "value": val_raw,
                                    "unit": unit,
                                    "reference_range": ref_text,
                                    "source_page": page.page_number,
                                    "source_snippet": line[:240],
                                    "confidence": round(page.avg_confidence, 3),
                                }
                            )
                            continue

                # Also handle qualitative urine dipstick lines (e.g., "Urine Protein: Negative", "Ketones: Trace")
                if doc_type == "urine_test":
                    qual_m = re.match(
                        r"^(?P<name>[A-Za-z][A-Za-z0-9\s\-/]{2,35})\s*[:\-]\s*(?P<val>Negative|Positive|Trace|Normal|Clear|Turbid|Pale Yellow|Yellow|Amber|[1-4]\+)\b(?P<rest>.*)$",
                        line,
                        flags=re.IGNORECASE,
                    )
                    if qual_m:
                        observations.append(
                            {
                                "category": "urine_parameter",
                                "title": qual_m.group("name").strip(),
                                "detail": f"{qual_m.group('val').strip()} {qual_m.group('rest').strip()}".strip(),
                                "source_page": page.page_number,
                                "source_snippet": line[:240],
                                "confidence": round(page.avg_confidence, 3),
                            }
                        )

            # 2. Extract medications (for prescription, discharge_summary, clinical_notes)
            if doc_type in {"prescription", "discharge_summary", "clinical_notes", "other"}:
                mm = MED_LINE_RE.match(line)
                if mm:
                    med_name = mm.group("name").strip(" .:-")
                    dose = mm.group("dose").strip()
                    rest = (mm.group("rest") or "").strip()
                    freq_matches = FREQ_PATTERN.findall(rest)
                    freq = ", ".join(dict.fromkeys(freq_matches)) if freq_matches else None
                    dur_m = DURATION_PATTERN.search(rest)
                    duration = dur_m.group(1) if dur_m else None
                    uncertainty = None
                    if not freq:
                        uncertainty = "Dosing frequency not clearly recognized on this line; verify with original prescription."
                    meds.append(
                        {
                            "medicine_name": med_name,
                            "dosage": dose,
                            "frequency": freq,
                            "duration": duration,
                            "instructions": rest if rest else None,
                            "source_page": page.page_number,
                            "source_snippet": line[:240],
                            "confidence": round(page.avg_confidence, 3),
                            "uncertainty_reason": uncertainty,
                        }
                    )
                    continue

            # 3. Radiology & clinical/discharge observations
            if doc_type == "radiology":
                if any(
                    k in current_section
                    for k in ("finding", "impression", "conclusion", "technique", "indication")
                ) and not re.match(r"^(findings|impression|technique|indication|conclusion)\s*:?$", lower):
                    cat = "radiology_impression" if "impression" in current_section or "conclusion" in current_section else "radiology_finding"
                    observations.append(
                        {
                            "category": cat,
                            "title": current_section.title(),
                            "detail": line,
                            "source_page": page.page_number,
                            "source_snippet": line[:240],
                            "confidence": round(page.avg_confidence, 3),
                        }
                    )
            elif doc_type in {"discharge_summary", "clinical_notes"}:
                if any(
                    k in current_section
                    for k in ("chief complaint", "vital", "assessment", "plan", "hospital course", "follow-up")
                ) and len(line) > 12:
                    observations.append(
                        {
                            "category": current_section.replace(" ", "_"),
                            "title": current_section.title(),
                            "detail": line,
                            "source_page": page.page_number,
                            "source_snippet": line[:240],
                            "confidence": round(page.avg_confidence, 3),
                        }
                    )

    return {
        "report_date": report_date,
        "dates": dates,
        "labs": labs,
        "medications": meds,
        "observations": observations,
    }


def extract_medical_entities(
    pages: List[OCRPage],
    raw_text: str,
    doc_type: str,
    quality_score: float,
) -> dict:
    """Specialized extraction pipeline with source page & snippet provenance."""
    det = _deterministic_extract(pages, doc_type)
    report_date = det["report_date"]
    labs_raw = det["labs"]
    meds_raw = det["medications"]
    obs_raw = det["observations"]
    dates = det["dates"]

    # When GEMINI_API_KEY is configured, enhance extraction via Gemini structured output
    if GEMINI_API_KEY and len(raw_text.strip()) >= 25:
        try:
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"You are a medical document information extraction system for a '{doc_type}' document.\n"
                "Rules:\n"
                "1. Extract ONLY facts explicitly printed in the text.\n"
                "2. NEVER invent missing reference ranges, units, dosages, or diagnoses.\n"
                "3. For radiology documents, extract findings and impressions ONLY from the written radiologist text.\n"
                "4. For every extracted item, include exact source_page and verbatim source_snippet from the text.\n\n"
                f"OCR Text:\n{raw_text[:12000]}"
            )
            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": GeminiExtractionBundle.model_json_schema(),
                },
            )
            if interaction.output_text:
                bundle = GeminiExtractionBundle.model_validate_json(interaction.output_text)
                if bundle.report_date:
                    report_date = _normalize_date(bundle.report_date)
                if bundle.lab_findings:
                    labs_raw = [item.model_dump() for item in bundle.lab_findings]
                if bundle.medications:
                    meds_raw = [item.model_dump() for item in bundle.medications]
                if bundle.observations:
                    obs_raw = [item.model_dump() for item in bundle.observations]
        except Exception:
            pass

    entities: List[dict] = []
    lab_findings: List[dict] = []

    for d in dates[:6]:
        entities.append(
            {
                "id": str(uuid.uuid4()),
                "entity_type": "date",
                "name": "Document Date",
                "value": d["date"],
                "date_value": d["date"],
                "source_page": d["page"],
                "source_snippet": d["snippet"],
                "confidence": 0.9,
                "needs_verification": False,
                "verification_reason": None,
            }
        )

    for lab in labs_raw:
        test_name = str(lab.get("test_name", "")).strip()
        if not test_name:
            continue
        val_raw = str(lab.get("value", "")).strip()
        unit = lab.get("unit")
        ref_range = lab.get("reference_range")
        src_page = int(lab.get("source_page") or 1)
        snippet = str(lab.get("source_snippet") or "")
        conf = float(lab.get("confidence") or quality_score or 0.8)
        eff_conf = min(conf, max(quality_score, 0.4))

        canonical_key, canonical_display = canonicalize_test_name(test_name)
        canonical_unit = canonicalize_unit(unit)
        eval_res = evaluate_lab_finding(val_raw, unit, ref_range, confidence=eff_conf)

        lab_id = str(uuid.uuid4())
        lab_findings.append(
            {
                "id": lab_id,
                "test_name": test_name,
                "canonical_test_key": canonical_key,
                "value_numeric": eval_res["value_numeric"],
                "value_raw": val_raw,
                "unit": unit,
                "canonical_unit": canonical_unit,
                "ref_low": eval_res["ref_low"],
                "ref_high": eval_res["ref_high"],
                "ref_text": ref_range,
                "status": eval_res["status"],
                "deviation_pct": eval_res["deviation_pct"],
                "source_page": src_page,
                "source_snippet": snippet,
                "confidence": round(eff_conf, 3),
                "needs_verification": eval_res["needs_verification"],
                "verification_reason": eval_res["verification_reason"],
            }
        )
        entities.append(
            {
                "id": str(uuid.uuid4()),
                "entity_type": "lab_test",
                "name": canonical_display if canonical_display else test_name,
                "value": val_raw,
                "unit": unit,
                "reference_range": ref_range,
                "source_page": src_page,
                "source_snippet": snippet,
                "confidence": round(eff_conf, 3),
                "needs_verification": eval_res["needs_verification"],
                "verification_reason": eval_res["verification_reason"],
            }
        )

    for med in meds_raw:
        med_name = str(med.get("medicine_name", "")).strip()
        if not med_name:
            continue
        conf = float(med.get("confidence") or quality_score or 0.8)
        uncert = med.get("uncertainty_reason")
        needs_ver = bool(uncert) or conf < 0.75 or not med.get("dosage")
        if needs_ver and not uncert:
            uncert = "Verify medicine name, strength, and dosing schedule against the physical prescription."
        entities.append(
            {
                "id": str(uuid.uuid4()),
                "entity_type": "medication",
                "name": med_name,
                "value": med.get("dosage"),
                "dosage": med.get("dosage"),
                "frequency": med.get("frequency"),
                "duration": med.get("duration"),
                "observation": med.get("instructions"),
                "source_page": int(med.get("source_page") or 1),
                "source_snippet": str(med.get("source_snippet") or ""),
                "confidence": round(conf, 3),
                "needs_verification": needs_ver,
                "verification_reason": uncert,
            }
        )

    for obs in obs_raw:
        entities.append(
            {
                "id": str(uuid.uuid4()),
                "entity_type": str(obs.get("category") or "clinical_observation"),
                "name": str(obs.get("title") or "Observation"),
                "observation": str(obs.get("detail") or ""),
                "source_page": int(obs.get("source_page") or 1),
                "source_snippet": str(obs.get("source_snippet") or ""),
                "confidence": round(float(obs.get("confidence") or quality_score or 0.8), 3),
                "needs_verification": quality_score < 0.65,
                "verification_reason": "Low scan quality; verify wording against source report." if quality_score < 0.65 else None,
            }
        )

    return {
        "report_date": report_date,
        "entities": entities,
        "lab_findings": lab_findings,
    }
