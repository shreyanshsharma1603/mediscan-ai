from __future__ import annotations

import io
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import MEDICAL_DISCLAIMER


def build_doctor_summary_payload(
    user: dict,
    doc: dict,
    classification: dict,
    entities: List[dict],
    lab_findings: List[dict],
    analysis: dict,
    language: str = "en",
) -> dict:
    extracted_values = [
        {
            "test_name": f["test_name"],
            "value": f["value_raw"],
            "unit": f.get("unit") or "-",
            "reference_range": f.get("ref_text") or "Not printed",
            "status": f["status"],
            "page": f["source_page"],
            "needs_verification": f["needs_verification"],
        }
        for f in lab_findings
    ]

    medications = [
        {
            "medicine_name": e["name"],
            "dosage": e.get("dosage") or "-",
            "frequency": e.get("frequency") or "Verify schedule",
            "duration": e.get("duration") or "-",
            "page": e["source_page"],
            "needs_verification": e["needs_verification"],
        }
        for e in entities
        if e["entity_type"] == "medication"
    ]

    radiology_sections = [
        {
            "section": e["name"],
            "detail": e.get("observation") or "",
            "page": e["source_page"],
        }
        for e in entities
        if e["entity_type"] in {"radiology_finding", "radiology_impression"}
    ]

    uncertainties = list(doc.get("ocr_warnings") or [])
    for f in lab_findings:
        if f["needs_verification"] and f.get("verification_reason"):
            uncertainties.append(f"{f['test_name']}: {f['verification_reason']}")
    for e in entities:
        if e.get("needs_verification") and e.get("verification_reason") and e["entity_type"] != "lab_test":
            uncertainties.append(f"{e['name']}: {e['verification_reason']}")

    return {
        "document_id": doc["id"],
        "patient_name": user["full_name"],
        "document_type": classification["final_type"],
        "report_date": doc.get("report_date") or doc.get("created_at", "")[:10],
        "language": language,
        "concise_clinical_summary": analysis.get("plain_summary", ""),
        "extracted_values": extracted_values,
        "medications": medications,
        "radiology_sections": radiology_sections,
        "uncertainties_for_verification": list(dict.fromkeys(uncertainties)),
        "questions_for_clinician": analysis.get("questions_for_doctor", []),
        "safety_disclaimer": MEDICAL_DISCLAIMER,
    }


def render_doctor_summary_pdf(summary: dict) -> bytes:
    """Generate a clean, clinician-ready PDF summary using ReportLab."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MediTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "MediH2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0F766E"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "MediBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
    )
    disclaimer_style = ParagraphStyle(
        "MediDisclaimer",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    story: List[Any] = []
    story.append(Paragraph("MediScan AI — Clinician Discussion Summary", title_style))
    meta = (
        f"<b>Patient:</b> {summary['patient_name']} &nbsp;|&nbsp; "
        f"<b>Document Type:</b> {summary['document_type'].replace('_', ' ').title()} &nbsp;|&nbsp; "
        f"<b>Report Date:</b> {summary.get('report_date') or 'Not specified'}"
    )
    story.append(Paragraph(meta, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Document Overview", h2_style))
    story.append(Paragraph(summary["concise_clinical_summary"] or "No summary generated.", body_style))

    if summary["extracted_values"]:
        story.append(Paragraph("Extracted Laboratory Measurements", h2_style))
        rows = [["Test", "Value", "Unit", "Printed Ref Range", "Status"]]
        for item in summary["extracted_values"][:30]:
            rows.append(
                [
                    str(item["test_name"])[:32],
                    str(item["value"]),
                    str(item["unit"]),
                    str(item["reference_range"])[:24],
                    str(item["status"]).replace("_", " "),
                ]
            )
        tbl = Table(rows, colWidths=[1.85 * inch, 0.85 * inch, 0.9 * inch, 1.55 * inch, 1.5 * inch])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tbl)

    if summary["medications"]:
        story.append(Paragraph("Extracted Medications (Printed Source)", h2_style))
        m_rows = [["Medicine", "Dosage", "Frequency", "Duration"]]
        for med in summary["medications"]:
            m_rows.append(
                [
                    str(med["medicine_name"]),
                    str(med["dosage"]),
                    str(med["frequency"]),
                    str(med["duration"]),
                ]
            )
        mtbl = Table(m_rows, colWidths=[2.0 * inch, 1.2 * inch, 2.2 * inch, 1.25 * inch])
        mtbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(mtbl)

    if summary["radiology_sections"]:
        story.append(Paragraph("Radiology Report Text Sections", h2_style))
        for rsec in summary["radiology_sections"][:12]:
            story.append(Paragraph(f"<b>{rsec['section']}:</b> {rsec['detail']}", body_style))

    if summary["uncertainties_for_verification"]:
        story.append(Paragraph("Items Flagged for Verification", h2_style))
        for u in summary["uncertainties_for_verification"][:12]:
            story.append(Paragraph(f"• {u}", body_style))

    if summary["questions_for_clinician"]:
        story.append(Paragraph("Questions for Clinician Discussion", h2_style))
        for q in summary["questions_for_clinician"]:
            story.append(Paragraph(f"• {q}", body_style))

    story.append(Spacer(1, 14))
    story.append(Paragraph(f"<b>Medical Safety Notice:</b> {summary['safety_disclaimer']}", disclaimer_style))

    doc.build(story)
    return buf.getvalue()
