from __future__ import annotations

import re
from typing import Dict, List, Tuple

from pydantic import BaseModel, Field

from app.config import DOCUMENT_TYPES, GEMINI_API_KEY, GEMINI_MODEL

# Transparent weighted keyword & structural signals for each specialized pipeline
CLASSIFICATION_RULES: Dict[str, List[Tuple[str, float, str]]] = {
    "blood_test": [
        (r"\b(complete blood count|cbc|hemogram|hematology)\b", 3.2, "CBC / Hematology header"),
        (r"\b(hemoglobin|hgb|hb|hematocrit|hct|rbc|wbc|platelet|mcv|mch|mchc)\b", 1.8, "Blood cell panel analytes"),
        (r"\b(lipid panel|cholesterol|triglycerides|hdl|ldl|vldl)\b", 2.0, "Lipid panel analytes"),
        (r"\b(hba1c|fasting glucose|blood glucose|creatinine|egfr|bun|alt|ast|sgpt|sgot|bilirubin|tsh|t3|t4|serum|plasma|venous)\b", 1.6, "Serum biochemistry markers"),
        (r"\b(reference range|ref\.?\s*interval|biological ref)\b", 1.2, "Printed laboratory reference intervals"),
    ],
    "urine_test": [
        (r"\b(urinalysis|urine routine|urine examination|urine culture|urine analysis|routine urine)\b", 3.8, "Urinalysis report header"),
        (r"\b(specific gravity|urine ph|urobilinogen|leukocyte esterase|nitrite|ketones|pus cells|epithelial cells|casts|crystals|microalbumin)\b", 2.1, "Urine microscopy/dipstick markers"),
        (r"\b(urine\s+protein|urine\s+glucose|urine\s+color|appearance.*clear|turbidity)\b", 1.8, "Physical/chemical urine parameters"),
    ],
    "prescription": [
        (r"\b(rx|prescription|dispense|refills?|sig:|take\s+\d+|tab\.|cap\.|syrup|tablet|capsule|ointment)\b", 2.6, "Prescription directive / formulation"),
        (r"\b(mg|mcg|ml)\b.*\b(once daily|twice daily|thrice daily|od|bd|tid|qid|hs|sos|prn|q\d+h|after food|before food)\b", 3.0, "Medication dosage & dosing frequency"),
        (r"\b(prescribed by|dr\.|reg\.?\s*no|dea|pharmacy|dispensed)\b", 1.4, "Prescriber / pharmacy metadata"),
    ],
    "radiology": [
        (r"\b(radiology|imaging report|ultrasound|sonography|ct scan|computed tomography|mri|magnetic resonance|x-ray|radiograph|mammogram|pet-ct)\b", 3.5, "Imaging modality / radiology header"),
        (r"\b(findings:|impression:|technique:|comparison:|indication:)\b", 2.3, "Structured radiologist report sections"),
        (r"\b(no acute|unremarkable|parenchyma|pleural effusion|consolidation|cardiomegaly|opacity|radiologist|dictated by)\b", 1.8, "Radiological terminology"),
    ],
    "discharge_summary": [
        (r"\b(discharge summary|hospital discharge|inpatient summary|discharge diagnosis|discharge medications)\b", 4.0, "Discharge summary header"),
        (r"\b(date of admission|admission date|date of discharge|discharge date|hospital course|condition at discharge)\b", 2.5, "Inpatient admission/discharge timeline"),
        (r"\b(follow-up instructions|return precautions|procedures performed|attending physician)\b", 1.8, "Post-discharge care plan"),
    ],
    "clinical_notes": [
        (r"\b(clinical note|progress note|consultation note|outpatient note|soap note|office visit|history of present illness|hpi)\b", 3.5, "Clinical consultation header"),
        (r"\b(chief complaint|cc:|vital signs|bp:|hr:|spo2|temp:|physical exam|assessment and plan|a/p:)\b", 2.2, "Clinical exam / vitals / SOAP structure"),
        (r"\b(review of systems|past medical history|social history|allergies:)\b", 1.5, "Patient clinical history sections"),
    ],
}


class GeminiClassificationSchema(BaseModel):
    document_type: str = Field(
        description="One of: blood_test, urine_test, prescription, radiology, discharge_summary, clinical_notes, other"
    )
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_signals: List[str] = Field(default_factory=list)


def classify_document(text: str, filename: str = "") -> dict:
    """Transparent hybrid document classification returning predicted type, confidence, and evidence signals."""
    combined = f"{filename}\n{text}".lower()
    raw_scores: Dict[str, float] = {doc_type: 0.0 for doc_type in DOCUMENT_TYPES}
    matched_signals: Dict[str, List[str]] = {doc_type: [] for doc_type in DOCUMENT_TYPES}

    for doc_type, rules in CLASSIFICATION_RULES.items():
        for pattern, weight, label in rules:
            matches = re.findall(pattern, combined, flags=re.IGNORECASE)
            if matches:
                # Cap repeated matches so one noisy word doesn't dominate
                boost = weight * min(1.0 + 0.2 * (len(matches) - 1), 1.8)
                raw_scores[doc_type] += boost
                matched_signals[doc_type].append(f"{label} ({len(matches)}x)")

    total = sum(raw_scores.values())
    if total <= 0.1:
        predicted = "other"
        confidence = 0.45
        candidate_scores = {k: 0.0 for k in DOCUMENT_TYPES}
        candidate_scores["other"] = 1.0
        signals = ["No strong domain-specific headers or markers detected; classified as general medical document."]
    else:
        sorted_types = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
        predicted, top_score = sorted_types[0]
        second_score = sorted_types[1][1] if len(sorted_types) > 1 else 0.0
        margin = (top_score - second_score) / max(top_score, 1.0)
        share = top_score / total
        confidence = round(min(0.98, max(0.45, 0.45 * share + 0.35 * margin + min(top_score / 8.0, 0.2))), 3)
        candidate_scores = {
            k: round(v / total, 3) for k, v in raw_scores.items()
        }
        signals = matched_signals.get(predicted, []) or ["Matched structural clinical indicators."]

    # Optional Gemini verification when server-side API key is configured and text is available
    if GEMINI_API_KEY and len(text.strip()) >= 30:
        try:
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                "Classify this medical document into exactly one of: "
                "blood_test, urine_test, prescription, radiology, discharge_summary, clinical_notes, other. "
                "Provide confidence 0.0-1.0 and 2-4 concise evidence signals directly observed in the text.\n\n"
                f"Document text:\n{text[:4500]}"
            )
            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": GeminiClassificationSchema.model_json_schema(),
                },
            )
            if interaction.output_text:
                parsed = GeminiClassificationSchema.model_validate_json(interaction.output_text)
                if parsed.document_type in DOCUMENT_TYPES:
                    # Blend transparent deterministic signals with Gemini classification
                    if parsed.document_type == predicted:
                        confidence = round(min(0.99, (confidence + parsed.confidence) / 2 + 0.05), 3)
                    elif parsed.confidence >= 0.78 and confidence < 0.72:
                        predicted = parsed.document_type
                        confidence = round(parsed.confidence, 3)
                    if parsed.reasoning_signals:
                        signals = list(dict.fromkeys(signals + parsed.reasoning_signals))[:6]
        except Exception:
            # Keep deterministic classification cleanly on API failure
            pass

    return {
        "predicted_type": predicted,
        "final_type": predicted,
        "confidence": confidence,
        "is_manual_override": False,
        "signals": signals,
        "candidate_scores": candidate_scores,
    }
