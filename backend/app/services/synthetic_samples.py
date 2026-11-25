from __future__ import annotations

import io
from typing import List, Tuple

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def _make_text_pdf(lines: List[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER
    y = height - 54
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, lines[0])
    y -= 22
    c.setFont("Helvetica", 10)
    for line in lines[1:]:
        if y < 56:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 54
        c.drawString(50, y, line)
        y -= 16
    c.save()
    return buf.getvalue()


def generate_synthetic_sample_files() -> List[Tuple[str, str, str, bytes, str]]:
    """Create clearly labeled synthetic medical documents (PDF) for demo & verification."""
    blood_jan = _make_text_pdf(
        [
            "SYNTHETIC DEMO LAB REPORT - COMPLETE BLOOD COUNT & METABOLIC PANEL",
            "Patient: Synthetic Demo Patient | Age: 34 | Report Date: 2026-01-15",
            "Sample Type: Venous Blood | Lab ID: SYN-2026-0115",
            "",
            "Test Name               Result      Unit        Reference Range",
            "Hemoglobin              11.8        g/dL        13.5 - 17.5",
            "WBC                     6.4         10^3/uL     4.5 - 11.0",
            "Platelet Count          240         10^3/uL     150 - 450",
            "Fasting Glucose         114         mg/dL       70 - 99",
            "HbA1c                   6.1         %           4.0 - 5.6",
            "Total Cholesterol       218         mg/dL       < 200",
            "LDL Cholesterol         142         mg/dL       < 100",
            "HDL Cholesterol         46          mg/dL       > 40",
            "Serum Creatinine        0.95        mg/dL       0.7 - 1.3",
            "TSH                     2.8         mIU/L       0.4 - 4.0",
            "",
            "Disclaimer: Synthetic test report generated for MediScan AI software demonstration.",
        ]
    )

    blood_apr = _make_text_pdf(
        [
            "SYNTHETIC DEMO LAB REPORT - FOLLOW-UP BLOOD TEST PANEL",
            "Patient: Synthetic Demo Patient | Age: 34 | Report Date: 2026-04-20",
            "Sample Type: Venous Blood | Lab ID: SYN-2026-0420",
            "",
            "Test Name               Result      Unit        Reference Range",
            "Hemoglobin              13.7        g/dL        13.5 - 17.5",
            "WBC                     6.1         10^3/uL     4.5 - 11.0",
            "Platelet Count          255         10^3/uL     150 - 450",
            "Fasting Glucose         96          mg/dL       70 - 99",
            "HbA1c                   5.7         %           4.0 - 5.6",
            "Total Cholesterol       188         mg/dL       < 200",
            "LDL Cholesterol         112         mg/dL       < 100",
            "HDL Cholesterol         51          mg/dL       > 40",
            "Serum Creatinine        0.92        mg/dL       0.7 - 1.3",
            "Vitamin D               24          ng/mL",
            "",
            "Disclaimer: Synthetic test report generated for MediScan AI software demonstration.",
        ]
    )

    prescription_pdf = _make_text_pdf(
        [
            "SYNTHETIC DEMO OUTPATIENT PRESCRIPTION (Rx)",
            "Clinic: Harborview Synthetic Health | Date: 2026-04-22",
            "Prescriber: Dr. A. Rivera, MD | Reg No: SYN-88412",
            "",
            "Rx:",
            "1. Tab. Metformin 500 mg - once daily after food for 30 days",
            "2. Tab. Atorvastatin 10 mg - once daily at bedtime for 30 days",
            "3. Cap. Cholecalciferol 60000 IU - once weekly for 8 weeks",
            "4. Tab. Ferrous Ascorbate 100 mg - OD",
            "",
            "Follow-up in 6 weeks with repeat fasting lipid and HbA1c panel.",
            "Disclaimer: Synthetic prescription for software demonstration only.",
        ]
    )

    radiology_pdf = _make_text_pdf(
        [
            "SYNTHETIC DEMO RADIOLOGY REPORT - CHEST RADIOGRAPH (PA VIEW)",
            "Exam Date: 2026-03-10 | Modality: X-Ray Chest | Dictated by: Dr. K. Patel, Radiologist",
            "Indication: Mild persistent dry cough for 2 weeks.",
            "Technique: Frontal PA and lateral chest radiograph.",
            "",
            "Findings:",
            "The lungs are clear bilaterally without focal consolidation, pleural effusion, or pneumothorax.",
            "Cardiomediastinal silhouette is normal in size and contour.",
            "Bony thorax and visualized upper abdomen are unremarkable.",
            "",
            "Impression:",
            "No acute cardiopulmonary abnormality identified on this chest radiograph.",
            "",
            "Note: Written radiologist report only. Synthetic demo data.",
        ]
    )

    return [
        ("Synthetic_Blood_Panel_Jan2026.pdf", ".pdf", "application/pdf", blood_jan, "2026-01-15"),
        ("Synthetic_Blood_Panel_Apr2026.pdf", ".pdf", "application/pdf", blood_apr, "2026-04-20"),
        ("Synthetic_Prescription_Apr2026.pdf", ".pdf", "application/pdf", prescription_pdf, "2026-04-22"),
        ("Synthetic_Radiology_ChestXRay_Mar2026.pdf", ".pdf", "application/pdf", radiology_pdf, "2026-03-10"),
    ]
