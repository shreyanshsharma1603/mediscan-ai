from __future__ import annotations

import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.config import GEMINI_API_KEY, GEMINI_MODEL, MEDICAL_DISCLAIMER, SUPPORTED_LANGUAGES


class GeminiGlossaryItem(BaseModel):
    term: str
    plain_definition: str


class GeminiFindingExplanation(BaseModel):
    item_name: str
    explanation: str
    uncertainty_note: str = ""


class GeminiExplanationResponse(BaseModel):
    plain_summary: str
    key_takeaways: List[str]
    finding_explanations: List[GeminiFindingExplanation]
    terminology_glossary: List[GeminiGlossaryItem]
    questions_for_doctor: List[str]
    uncertainty_notes: List[str]


class GeminiQACitation(BaseModel):
    page: int
    snippet: str


class GeminiQAResponse(BaseModel):
    answer: str
    citations: List[GeminiQACitation]
    information_unavailable: bool = False


LOCALIZED_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "summary_prefix": "Plain-language overview of your {doc_type} document",
        "no_diag": "Note: An out-of-range measurement is a statistical flag against the printed reference interval, not a diagnosis.",
        "unavailable": "This information is not available in the uploaded medical document.",
        "verify_prompt": "Verify extracted values marked for review against the original document.",
        "q1": "What do the out-of-range or flagged measurements mean in the context of my overall health history?",
        "q2": "Should any of these tests be repeated or followed up on a specific schedule?",
        "q3": "Are any of my current medications, diet, or hydration status affecting these numbers?",
    },
    "hi": {
        "summary_prefix": "आपके {doc_type} दस्तावेज़ का सरल भाषा में सारांश",
        "no_diag": "नोट: संदर्भ सीमा से बाहर का मान केवल मुद्रित संदर्भ सीमा की तुलना है, यह किसी बीमारी का निदान नहीं है।",
        "unavailable": "यह जानकारी अपलोड किए गए मेडिकल दस्तावेज़ में उपलब्ध नहीं है।",
        "verify_prompt": "समीक्षा के लिए चिह्नित मानों को मूल रिपोर्ट से मिलाएं।",
        "q1": "मेरे समग्र स्वास्थ्य इतिहास के संदर्भ में संदर्भ सीमा से बाहर के मानों का क्या अर्थ है?",
        "q2": "क्या इनमें से किसी जांच को दोहराने या आगे फॉलो-अप की आवश्यकता है?",
        "q3": "क्या मेरी वर्तमान दवाएं या आहार इन परिणामों को प्रभावित कर सकते हैं?",
    },
    "bn": {
        "summary_prefix": "আপনার {doc_type} নথির সহজ ভাষায় সারসংক্ষেপ",
        "no_diag": "দ্রষ্টব্য: রেফারেন্স সীমার বাইরের মান কেবল মুদ্রিত সীমার সাথে তুলনা, এটি কোনো রোগ নির্ণয় নয়।",
        "unavailable": "এই তথ্যটি আপলোড করা মেডিকেল নথিতে উপলব্ধ নয়।",
        "verify_prompt": "পর্যালোচনার জন্য চিহ্নিত মানগুলি মূল নথির সাথে যাচাই করুন।",
        "q1": "আমার সামগ্রিক স্বাস্থ্য ইতিহাসের প্রেক্ষাপটে সীমার বাইরের মানগুলির অর্থ কী?",
        "q2": "এই পরীক্ষাগুলির মধ্যে কোনোটি পুনরায় করার বা ফলো-আপের প্রয়োজন আছে কি?",
        "q3": "আমার বর্তমান ওষুধ বা খাদ্যাভ্যাস কি এই ফলাফলগুলিকে প্রভাবিত করতে পারে?",
    },
    "ta": {
        "summary_prefix": "உங்கள் {doc_type} ஆவணத்தின் எளிய மொழி விளக்கம்",
        "no_diag": "குறிப்பு: குறிப்பு வரம்பிற்கு வெளியே உள்ள மதிப்பு என்பது அச்சிடப்பட்ட வரம்புடன் ஒப்பிடப்பட்ட குறிப்பாகும்; இது நோய் கண்டறிதல் அல்ல.",
        "unavailable": "இந்தத் தகவல் பதிவேற்றப்பட்ட மருத்துவ ஆவணத்தில் இல்லை.",
        "verify_prompt": "சரிபார்ப்பிற்காக குறிக்கப்பட்ட மதிப்புகளை அசல் அறிக்கையுடன் ஒப்பிட்டு பார்க்கவும்.",
        "q1": "எனது ஒட்டுமொத்த உடல்நிலை வரலாற்றின் அடிப்படையில் வரம்பிற்கு வெளியே உள்ள மதிப்புகளின் அர்த்தம் என்ன?",
        "q2": "இந்தப் பரிசோதனைகளில் எதையும் மீண்டும் செய்ய வேண்டுமா அல்லது பின்தொடர வேண்டுமா?",
        "q3": "எனது தற்போதைய மருந்துகள் அல்லது உணவு முறை இந்த முடிவுகளைப் பாதிக்குமா?",
    },
    "te": {
        "summary_prefix": "మీ {doc_type} పత్రం యొక్క సులభమైన వివరణ",
        "no_diag": "గమనిక: రిఫరెన్స్ పరిధి వెలుపల ఉన్న విలువ ముద్రించిన పరిధితో పోలిక మాత్రమే, ఇది వ్యాధి నిర్ధారణ కాదు.",
        "unavailable": "ఈ సమాచారం అప్‌లోడ్ చేసిన వైద్య పత్రంలో అందుబాటులో లేదు.",
        "verify_prompt": "సమీక్ష కోసం గుర్తించబడిన విలువలను అసలు నివేదికతో సరిపోల్చండి.",
        "q1": "నా మొత్తం ఆరోగ్య చరిత్ర నేపథ్యంలో పరిధి వెలుపల ఉన్న విలువల అర్థం ఏమిటి?",
        "q2": "ఈ పరీక్షలలో దేనినైనా మళ్ళీ చేయాలా లేదా తదుపరి పర్యవేక్షణ అవసరమా?",
        "q3": "నా ప్రస్తుత మందులు లేదా ఆహారపు అలవాట్లు ఈ ఫలితాలను ప్రభావితం చేస్తాయా?",
    },
    "mr": {
        "summary_prefix": "तुमच्या {doc_type} दस्तऐवजाचा सोप्या भाषेतील सारांश",
        "no_diag": "टीप: संदर्भ मर्यादेबाहेरील मूल्य ही केवळ छापील मर्यादेशी तुलना आहे; हे आजाराचे निदान नाही.",
        "unavailable": "ही माहिती अपलोड केलेल्या वैद्यकीय दस्तऐवजात उपलब्ध नाही.",
        "verify_prompt": "पडताळणीसाठी चिन्हांकित केलेली मूल्ये मूळ अहवालाशी तपासा.",
        "q1": "माझ्या एकूण आरोग्य इतिहासाच्या संदर्भात मर्यादेबाहेरील मूल्यांचा अर्थ काय आहे?",
        "q2": "यापैकी कोणतीही चाचणी पुन्हा करण्याची किंवा पाठपुराव्याची गरज आहे का?",
        "q3": "माझी सध्याची औषधे किंवा आहार यांचा या निकालांवर परिणाम होऊ शकतो का?",
    },
    "es": {
        "summary_prefix": "Resumen en lenguaje sencillo de su documento ({doc_type})",
        "no_diag": "Nota: Un valor fuera del rango de referencia es una comparación con el intervalo impreso, no un diagnóstico.",
        "unavailable": "Esta información no está disponible en el documento médico cargado.",
        "verify_prompt": "Verifique los valores marcados para revisión con el documento original.",
        "q1": "¿Qué significan los valores fuera del rango de referencia dentro de mi historial médico general?",
        "q2": "¿Es necesario repetir alguna de estas pruebas o programar un seguimiento?",
        "q3": "¿Mis medicamentos actuales o mi dieta podrían influir en estos resultados?",
    },
    "fr": {
        "summary_prefix": "Résumé en langage simple de votre document ({doc_type})",
        "no_diag": "Remarque : Une valeur hors de l'intervalle de référence est une comparaison statistique et non un diagnostic.",
        "unavailable": "Cette information n'est pas disponible dans le document médical importé.",
        "verify_prompt": "Vérifiez les valeurs signalées pour révision par rapport au document original.",
        "q1": "Que signifient les valeurs hors de l'intervalle de référence dans le contexte de mon dossier médical ?",
        "q2": "Certains de ces examens doivent-ils être répétés ou suivis ultérieurement ?",
        "q3": "Mes traitements actuels ou mon alimentation peuvent-ils influencer ces résultats ?",
    },
}

MEDICAL_GLOSSARY = {
    "hemoglobin": "A protein in red blood cells that carries oxygen from the lungs to tissues.",
    "wbc": "White blood cells are immune system cells measured to monitor immune and inflammatory activity.",
    "platelet": "Cell fragments in blood that assist with normal clotting.",
    "hba1c": "A measurement reflecting average blood glucose levels over roughly the past 2–3 months.",
    "creatinine": "A waste product filtered by the kidneys, commonly measured to help assess kidney filtration.",
    "tsh": "Thyroid-stimulating hormone, produced by the pituitary gland to regulate thyroid hormone output.",
    "alt": "Alanine aminotransferase, an enzyme found primarily in liver cells.",
    "ast": "Aspartate aminotransferase, an enzyme measured alongside liver and muscle markers.",
    "ldl": "Low-density lipoprotein cholesterol, often tracked in cardiovascular risk panels.",
    "hdl": "High-density lipoprotein cholesterol, involved in transporting cholesterol back to the liver.",
    "specific gravity": "A measure of how concentrated urine particles are compared with water.",
    "impression": "The radiologist's concise summary of the key written observations from the imaging study.",
}


def generate_analysis_explanation(
    doc_type: str,
    raw_text: str,
    entities: List[dict],
    lab_findings: List[dict],
    ocr_warnings: List[str],
    language: str = "en",
) -> dict:
    lang = language if language in SUPPORTED_LANGUAGES else "en"
    lang_name = SUPPORTED_LANGUAGES[lang]
    loc = LOCALIZED_STRINGS[lang]

    # Try live Gemini API first when configured server-side
    if GEMINI_API_KEY and len(raw_text.strip()) >= 20:
        try:
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            compact_labs = [
                {
                    "test": f["test_name"],
                    "value": f["value_raw"],
                    "unit": f.get("unit"),
                    "ref": f.get("ref_text"),
                    "status": f["status"],
                    "needs_verification": f["needs_verification"],
                }
                for f in lab_findings[:25]
            ]
            compact_meds = [
                {
                    "medicine": e["name"],
                    "dosage": e.get("dosage"),
                    "frequency": e.get("frequency"),
                    "needs_verification": e.get("needs_verification"),
                }
                for e in entities
                if e["entity_type"] == "medication"
            ][:15]
            compact_obs = [
                {"title": e["name"], "detail": e.get("observation")}
                for e in entities
                if e["entity_type"] not in {"date", "lab_test", "medication"}
            ][:15]

            prompt = (
                f"Generate a patient-friendly medical document explanation in {lang_name} ({lang}).\n"
                "STRICT HEALTHCARE SAFETY RULES:\n"
                "1. NEVER diagnose a disease or state that the patient has a condition.\n"
                "2. NEVER prescribe medication or recommend changing dosages.\n"
                "3. Preserve original medical terminology, numerical values, and units verbatim.\n"
                "4. Express appropriate uncertainty and highlight any items flagged for verification.\n"
                "5. If document type is 'radiology', base explanations strictly on the written radiologist report, NOT imaging pixels.\n\n"
                f"Document Type: {doc_type}\n"
                f"OCR Warnings: {ocr_warnings}\n"
                f"Extracted Lab Findings: {compact_labs}\n"
                f"Extracted Medications: {compact_meds}\n"
                f"Extracted Observations: {compact_obs}\n"
                f"Source Text Excerpt:\n{raw_text[:7000]}"
            )
            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": GeminiExplanationResponse.model_json_schema(),
                },
            )
            if interaction.output_text:
                parsed = GeminiExplanationResponse.model_validate_json(interaction.output_text)
                return {
                    "language": lang,
                    "ai_provider": f"gemini:{GEMINI_MODEL}",
                    "plain_summary": parsed.plain_summary,
                    "key_takeaways": parsed.key_takeaways,
                    "finding_explanations": [x.model_dump() for x in parsed.finding_explanations],
                    "terminology_glossary": [x.model_dump() for x in parsed.terminology_glossary],
                    "questions_for_doctor": parsed.questions_for_doctor,
                    "uncertainty_notes": parsed.uncertainty_notes,
                    "safety_disclaimer": MEDICAL_DISCLAIMER,
                }
        except Exception:
            pass

    # Deterministic structured literacy fallback when Gemini API key is not configured
    abnormal = [f for f in lab_findings if f["status"] in {"below_range", "above_range"}]
    within = [f for f in lab_findings if f["status"] == "within_range"]
    no_ref = [f for f in lab_findings if f["status"] == "reference_unavailable"]
    verify_items = [f for f in lab_findings if f["needs_verification"]] + [
        e for e in entities if e.get("needs_verification") and e["entity_type"] != "lab_test"
    ]
    meds = [e for e in entities if e["entity_type"] == "medication"]
    obs = [e for e in entities if e["entity_type"] not in {"date", "lab_test", "medication"}]

    doc_label = doc_type.replace("_", " ")
    summary_parts = [f"{loc['summary_prefix'].format(doc_type=doc_label)}."]
    if lab_findings:
        summary_parts.append(
            f"Extracted {len(lab_findings)} laboratory measurement(s): "
            f"{len(within)} within printed range, {len(abnormal)} outside printed range, "
            f"and {len(no_ref)} without a printed reference interval."
        )
    if meds:
        summary_parts.append(
            f"Identified {len(meds)} medication entry/entries with printed dosage details preserved verbatim."
        )
    if obs:
        summary_parts.append(f"Captured {len(obs)} clinical or written report observation(s).")
    summary_parts.append(loc["no_diag"])

    takeaways: List[str] = []
    for f in abnormal[:5]:
        direction = "above" if f["status"] == "above_range" else "below"
        unit_str = f" {f['unit']}" if f.get("unit") else ""
        ref_str = f" (printed ref: {f['ref_text']})" if f.get("ref_text") else ""
        takeaways.append(
            f"{f['test_name']}: {f['value_raw']}{unit_str} is {direction} the printed reference interval{ref_str}."
        )
    for m in meds[:4]:
        takeaways.append(
            f"Medication listed: {m['name']} {m.get('dosage') or ''} ({m.get('frequency') or 'frequency requires verification'})."
        )
    if not takeaways:
        takeaways.append("All parsed structured metrics are ready for review alongside the original source text.")

    finding_exps: List[dict] = []
    for f in lab_findings[:12]:
        unit_str = f" {f['unit']}" if f.get("unit") else ""
        ref_str = f" compared with the printed reference range of {f['ref_text']}" if f.get("ref_text") else " (no printed reference range found)"
        exp = (
            f"Measured {f['test_name']} at {f['value_raw']}{unit_str}{ref_str}. "
            f"Status: {f['status'].replace('_', ' ')}."
        )
        uncert = f.get("verification_reason") or (
            "Individual baseline factors can affect lab values; discuss interpretation with your clinician."
            if f["status"] in {"below_range", "above_range"}
            else None
        )
        finding_exps.append(
            {
                "item_name": f"{f['test_name']} ({f['value_raw']}{unit_str})",
                "explanation": exp,
                "uncertainty_note": uncert,
            }
        )

    glossary: List[dict] = []
    lower_text = raw_text.lower()
    for term_key, definition in MEDICAL_GLOSSARY.items():
        if term_key in lower_text:
            glossary.append({"term": term_key.upper() if len(term_key) <= 5 else term_key.title(), "plain_definition": definition})

    uncertainty_notes = list(ocr_warnings)
    if verify_items:
        uncertainty_notes.append(
            f"{len(verify_items)} extracted item(s) flagged for manual verification against the source text. {loc['verify_prompt']}"
        )
    if doc_type == "radiology":
        uncertainty_notes.append(
            "Analysis is strictly limited to the written radiologist report text; underlying medical imaging pixels were not analyzed."
        )

    return {
        "language": lang,
        "ai_provider": "structured_fallback (set GEMINI_API_KEY for live Gemini explanations)",
        "plain_summary": " ".join(summary_parts),
        "key_takeaways": takeaways,
        "finding_explanations": finding_exps,
        "terminology_glossary": glossary[:8],
        "questions_for_doctor": [loc["q1"], loc["q2"], loc["q3"]],
        "uncertainty_notes": uncertainty_notes,
        "safety_disclaimer": MEDICAL_DISCLAIMER,
    }


def answer_document_question(
    question: str,
    doc_type: str,
    raw_text: str,
    pages: List[dict],
    lab_findings: List[dict],
    entities: List[dict],
    language: str = "en",
) -> dict:
    """Grounded Document Assistant: answers strictly from extracted source text or reports unavailability."""
    lang = language if language in SUPPORTED_LANGUAGES else "en"
    lang_name = SUPPORTED_LANGUAGES[lang]
    loc = LOCALIZED_STRINGS[lang]

    if GEMINI_API_KEY and len(raw_text.strip()) >= 15:
        try:
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"You are MediScan AI's grounded Medical Document Assistant. Answer in {lang_name} ({lang}).\n"
                "STRICT GROUNDING & SAFETY RULES:\n"
                "1. Answer ONLY using facts explicitly present in the document text below.\n"
                "2. If the answer is NOT in the document, set information_unavailable=true and clearly state that the information is not available in the uploaded document.\n"
                "3. NEVER invent medical facts, diagnose conditions, or recommend treatments/dosage changes.\n"
                "4. Cite exact page numbers and short verbatim snippets.\n"
                "5. Preserve original medical terminology, numbers, and units.\n\n"
                f"Document Type: {doc_type}\n"
                f"Question: {question}\n\n"
                f"Document Source Text:\n{raw_text[:12000]}"
            )
            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": GeminiQAResponse.model_json_schema(),
                },
            )
            if interaction.output_text:
                parsed = GeminiQAResponse.model_validate_json(interaction.output_text)
                return {
                    "answer": parsed.answer,
                    "citations": [c.model_dump() for c in parsed.citations],
                    "information_unavailable": parsed.information_unavailable,
                    "language": lang,
                    "ai_provider": f"gemini:{GEMINI_MODEL}",
                    "safety_disclaimer": MEDICAL_DISCLAIMER,
                }
        except Exception:
            pass

    # Deterministic grounded keyword & entity lookup
    q_tokens = [
        tok for tok in re.findall(r"[a-z0-9]+", question.lower())
        if len(tok) > 2 and tok not in {"what", "when", "where", "which", "does", "this", "that", "with", "from", "have", "mean", "about", "report", "document", "value", "normal"}
    ]

    matched_citations: List[dict] = []
    matched_lines: List[str] = []

    for f in lab_findings:
        hay = f"{f['test_name']} {f['canonical_test_key']}".lower()
        if any(tok in hay for tok in q_tokens):
            unit_str = f" {f['unit']}" if f.get("unit") else ""
            ref_str = f" (printed ref: {f['ref_text']})" if f.get("ref_text") else " (no reference range printed)"
            matched_lines.append(
                f"{f['test_name']}: {f['value_raw']}{unit_str}{ref_str} — {f['status'].replace('_', ' ')}."
            )
            matched_citations.append(
                {"page": f["source_page"], "snippet": f.get("source_snippet") or f["test_name"]}
            )

    for e in entities:
        if e["entity_type"] == "lab_test":
            continue
        hay = f"{e['name']} {e.get('observation') or ''} {e.get('dosage') or ''}".lower()
        if any(tok in hay for tok in q_tokens):
            detail = e.get("observation") or f"{e.get('dosage') or ''} {e.get('frequency') or ''}".strip() or e.get("value") or ""
            matched_lines.append(f"{e['name']}: {detail}")
            matched_citations.append(
                {"page": e["source_page"], "snippet": e.get("source_snippet") or e["name"]}
            )

    if not matched_lines and q_tokens:
        for page in pages:
            pnum = page.get("page_number", 1)
            for line in str(page.get("text", "")).splitlines():
                low = line.lower()
                if sum(1 for tok in q_tokens if tok in low) >= 1 and len(line.strip()) > 6:
                    matched_lines.append(line.strip())
                    matched_citations.append({"page": pnum, "snippet": line.strip()[:200]})
                if len(matched_lines) >= 4:
                    break

    # Deduplicate citations
    seen_snip = set()
    dedup_citations = []
    for c in matched_citations:
        key = (c["page"], c["snippet"])
        if key not in seen_snip:
            seen_snip.add(key)
            dedup_citations.append(c)

    if not matched_lines:
        return {
            "answer": f"{loc['unavailable']} Please verify whether the uploaded pages contain that specific detail or consult your healthcare provider.",
            "citations": [],
            "information_unavailable": True,
            "language": lang,
            "ai_provider": "grounded_source_lookup",
            "safety_disclaimer": MEDICAL_DISCLAIMER,
        }

    answer_text = "Based strictly on the uploaded document:\n• " + "\n• ".join(matched_lines[:5])
    return {
        "answer": answer_text,
        "citations": dedup_citations[:5],
        "information_unavailable": False,
        "language": lang,
        "ai_provider": "grounded_source_lookup",
        "safety_disclaimer": MEDICAL_DISCLAIMER,
    }
