from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("mediscan_test")
    os.environ["MEDISCAN_DATA_DIR"] = str(tmp_dir / "data")
    os.environ["MEDISCAN_UPLOAD_DIR"] = str(tmp_dir / "uploads")
    os.environ["MEDISCAN_DB_PATH"] = str(tmp_dir / "data" / "test.db")
    os.environ["GEMINI_API_KEY"] = ""

    from app.database import init_db
    from app.main import app

    init_db(Path(os.environ["MEDISCAN_DB_PATH"]))
    with TestClient(app) as c:
        yield c


def _make_pdf(lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    y = LETTER[1] - 54
    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(50, y, line)
        y -= 18
    c.save()
    return buf.getvalue()


def _make_lab_png(lines: list[str], size=(1100, 700), bg="white", fg="black") -> bytes:
    img = Image.new("RGB", size, color=bg)
    draw = ImageDraw.Draw(img)
    y = 40
    for line in lines:
        draw.text((40, y), line, fill=fg)
        y += 32
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _register_and_token(client: TestClient, email: str, name: str = "Test Patient") -> str:
    res = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": name,
            "preferred_language": "en",
            "consent_accepted": True,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def test_health_and_consent_required(client: TestClient):
    h = client.get("/api/health")
    assert h.status_code == 200
    data = h.json()
    assert data["status"] == "ok"
    assert set(data["supported_languages"].keys()) == {"en", "hi", "bn", "ta", "te", "mr", "es", "fr"}

    bad_reg = client.post(
        "/api/auth/register",
        json={
            "email": "noconsent@example.com",
            "password": "Password123!",
            "full_name": "No Consent",
            "preferred_language": "en",
            "consent_accepted": False,
        },
    )
    assert bad_reg.status_code == 400


def test_malformed_and_unsupported_uploads(client: TestClient):
    token = _register_and_token(client, "malformed@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Unsupported extension
    r1 = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"consent_confirmed": "true"},
    )
    assert r1.status_code == 400

    # Empty file
    r2 = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("empty.pdf", b"", "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert r2.status_code == 400

    # Fake PDF missing %PDF-
    r3 = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("fake.pdf", b"NOT A REAL PDF", "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert r3.status_code == 400

    # Corrupted PDF with %PDF- header
    r4 = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("corrupt.pdf", b"%PDF-1.4\ncorrupted-bytes", "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert r4.status_code == 422


def test_poor_quality_blank_image_warning(client: TestClient):
    token = _register_and_token(client, "ocrpoor@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Poor-quality / sparse text PDF triggers poor_quality_scan status & warning
    sparse_pdf = _make_pdf(["..." ])
    res_pdf = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("sparse_scan.pdf", sparse_pdf, "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert res_pdf.status_code == 201
    body_pdf = res_pdf.json()
    assert body_pdf["ocr_quality_status"] in {"poor_quality_scan", "fair"}
    assert len(body_pdf["ocr_warnings"]) > 0

    # 2. Low-resolution blank PNG either surfaces warning (201) or actionable scan error (422)
    blank_png = _make_lab_png([], size=(300, 300), bg=(240, 240, 240))
    res_img = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("blurry_blank.png", blank_png, "image/png")},
        data={"consent_confirmed": "true"},
    )
    assert res_img.status_code in {201, 422}
    if res_img.status_code == 201:
        body_img = res_img.json()
        assert body_img["ocr_quality_status"] in {"poor_quality_scan", "fair"}
        assert len(body_img["ocr_warnings"]) > 0
    else:
        assert "resolution" in res_img.json()["detail"].lower() or "ocr" in res_img.json()["detail"].lower()


def test_multidoc_pipelines_lab_analysis_and_override(client: TestClient):
    token = _register_and_token(client, "pipelines@example.com", "Alex Mercer")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Blood test PDF (includes test without ref range to ensure it is NOT invented)
    blood_pdf = _make_pdf(
        [
            "COMPLETE BLOOD COUNT (CBC) - BLOOD TEST REPORT",
            "Report Date: 2026-02-01",
            "Hemoglobin    11.5    g/dL    13.5 - 17.5",
            "WBC           12.8    10^3/uL 4.5 - 11.0",
            "Platelet Count 250    10^3/uL 150 - 450",
            "Vitamin D     22      ng/mL",
        ]
    )
    res_blood = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("blood_feb.pdf", blood_pdf, "application/pdf")},
        data={"consent_confirmed": "true", "language": "hi"},
    )
    assert res_blood.status_code == 201, res_blood.text
    bdoc = res_blood.json()
    assert bdoc["classification"]["final_type"] == "blood_test"
    assert bdoc["analysis"]["language"] == "hi"

    labs_by_key = {l["canonical_test_key"]: l for l in bdoc["lab_findings"]}
    assert labs_by_key["hemoglobin"]["status"] == "below_range"
    assert labs_by_key["wbc_count"]["status"] == "above_range"
    assert labs_by_key["platelet_count"]["status"] == "within_range"
    assert labs_by_key["vitamin_d"]["status"] == "reference_unavailable"
    assert labs_by_key["vitamin_d"]["ref_low"] is None
    assert labs_by_key["vitamin_d"]["ref_high"] is None

    # 2. Urine test PDF
    urine_pdf = _make_pdf(
        [
            "URINE ROUTINE EXAMINATION / URINALYSIS",
            "Report Date: 2026-02-03",
            "Specific Gravity   1.020   1.005 - 1.030",
            "Urine pH           6.0     4.5 - 8.0",
            "Urine Protein: Negative",
        ]
    )
    res_urine = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("urine_feb.pdf", urine_pdf, "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert res_urine.status_code == 201
    assert res_urine.json()["classification"]["final_type"] == "urine_test"

    # 3. Prescription PDF
    rx_pdf = _make_pdf(
        [
            "OUTPATIENT PRESCRIPTION - Rx",
            "Date: 2026-02-05",
            "1. Tab. Metformin 500 mg - twice daily after food for 30 days",
            "2. Cap. Omeprazole 20 mg",
        ]
    )
    res_rx = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("rx.pdf", rx_pdf, "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert res_rx.status_code == 201
    rx_doc = res_rx.json()
    assert rx_doc["classification"]["final_type"] == "prescription"
    meds = [e for e in rx_doc["entities"] if e["entity_type"] == "medication"]
    assert len(meds) >= 2
    assert any(m["needs_verification"] for m in meds)  # Omeprazole missing frequency triggers uncertainty

    # 4. Radiology report PDF + manual classification override
    rad_pdf = _make_pdf(
        [
            "RADIOLOGY REPORT - CHEST X-RAY",
            "Date: 2026-02-10",
            "Findings:",
            "Lungs are clear with no focal consolidation or pleural effusion.",
            "Impression:",
            "No acute cardiopulmonary abnormality.",
        ]
    )
    res_rad = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("chest_xray.pdf", rad_pdf, "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert res_rad.status_code == 201
    rad_doc = res_rad.json()
    assert rad_doc["classification"]["final_type"] == "radiology"

    override = client.patch(
        f"/api/documents/{rad_doc['id']}/classification",
        headers=headers,
        json={"document_type": "clinical_notes"},
    )
    assert override.status_code == 200
    assert override.json()["classification"]["final_type"] == "clinical_notes"
    assert override.json()["classification"]["is_manual_override"] is True

    # 5. Grounded Q&A Assistant: available vs unavailable
    qa_ok = client.post(
        f"/api/documents/{bdoc['id']}/qa",
        headers=headers,
        json={"question": "What was my Hemoglobin value?", "language": "en"},
    )
    assert qa_ok.status_code == 200
    assert qa_ok.json()["information_unavailable"] is False
    assert "11.5" in qa_ok.json()["answer"]

    qa_missing = client.post(
        f"/api/documents/{bdoc['id']}/qa",
        headers=headers,
        json={"question": "What was my troponin cardiac marker result?", "language": "es"},
    )
    assert qa_missing.status_code == 200
    assert qa_missing.json()["information_unavailable"] is True

    # 6. Doctor Summary & PDF export
    ds_pdf = client.get(f"/api/documents/{bdoc['id']}/doctor-summary/pdf", headers=headers)
    assert ds_pdf.status_code == 200
    assert ds_pdf.headers["content-type"] == "application/pdf"
    assert ds_pdf.content.startswith(b"%PDF-")


def test_comparison_unit_safety_timeline_and_authorization(client: TestClient):
    token_a = _register_and_token(client, "usera@example.com", "User A")
    token_b = _register_and_token(client, "userb@example.com", "User B")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    pdf_1 = _make_pdf(
        [
            "BLOOD TEST REPORT",
            "Date: 2026-01-10",
            "Hb                11.8    g/dL    13.5 - 17.5",
            "Fasting Glucose   110     mg/dL   70 - 99",
        ]
    )
    pdf_2 = _make_pdf(
        [
            "BLOOD TEST REPORT",
            "Date: 2026-03-10",
            "Hemoglobin        13.9    g/dL    13.5 - 17.5",
            "Fasting Glucose   5.2     mmol/L  3.9 - 5.5",
        ]
    )
    d1 = client.post(
        "/api/documents/upload",
        headers=headers_a,
        files={"file": ("jan.pdf", pdf_1, "application/pdf")},
        data={"consent_confirmed": "true"},
    ).json()
    d2 = client.post(
        "/api/documents/upload",
        headers=headers_a,
        files={"file": ("mar.pdf", pdf_2, "application/pdf")},
        data={"consent_confirmed": "true"},
    ).json()

    cmp_res = client.post(
        "/api/insights/compare",
        headers=headers_a,
        json={"doc_a_id": d1["id"], "doc_b_id": d2["id"]},
    )
    assert cmp_res.status_code == 200, cmp_res.text
    cmp_body = cmp_res.json()
    matched_keys = {m["canonical_test_key"] for m in cmp_body["matched_tests"]}
    incompatible_names = {i["test_name_a"].lower() for i in cmp_body["incompatible_tests"]}
    assert "hemoglobin" in matched_keys
    assert any("glucose" in name for name in incompatible_names)  # mg/dL vs mmol/L NEVER falsely compared!

    # Timeline should show Hemoglobin trend (same unit g/dL) and NOT Glucose (incompatible units)
    tl_res = client.get("/api/insights/timeline", headers=headers_a)
    assert tl_res.status_code == 200
    trend_keys = {t["canonical_test_key"] for t in tl_res.json()["comparable_trends"]}
    assert "hemoglobin" in trend_keys
    assert "fasting_glucose" not in trend_keys

    # Strict cross-user authorization check: User B must NOT access User A's document
    assert client.get(f"/api/documents/{d1['id']}", headers=headers_b).status_code == 404
    assert client.get(f"/api/documents/{d1['id']}/file", headers=headers_b).status_code == 404
    assert client.delete(f"/api/documents/{d1['id']}", headers=headers_b).status_code == 404
    assert client.get(f"/api/documents/{d1['id']}/doctor-summary/pdf", headers=headers_b).status_code == 404


def test_synthetic_demo_multilingual_discharge_and_deletion(client: TestClient):
    token = _register_and_token(client, "fullflow@example.com", "Full Flow User")
    headers = {"Authorization": f"Bearer {token}"}

    # Load synthetic demo kit (4 documents)
    demo_res = client.post("/api/documents/load-synthetic-demo", headers=headers)
    assert demo_res.status_code == 200, demo_res.text
    demo_docs = demo_res.json()
    assert len(demo_docs) == 4

    # Verify all 8 languages generate valid analysis payloads
    sample_id = demo_docs[0]["id"]
    for lang in ["en", "hi", "bn", "ta", "te", "mr", "es", "fr"]:
        lang_doc = client.get(f"/api/documents/{sample_id}?language={lang}", headers=headers)
        assert lang_doc.status_code == 200
        assert lang_doc.json()["analysis"]["language"] == lang
        assert lang_doc.json()["analysis"]["safety_disclaimer"]

    # Prescription reader endpoint
    rx_list = client.get("/api/insights/prescriptions", headers=headers)
    assert rx_list.status_code == 200
    assert len(rx_list.json()["medications"]) >= 3

    # Discharge summary classification & extraction
    discharge_pdf = _make_pdf(
        [
            "HOSPITAL DISCHARGE SUMMARY",
            "Admission Date: 2026-01-02 | Discharge Date: 2026-01-05",
            "Hospital Course:",
            "Patient admitted for dehydration and monitored with IV fluids.",
            "Discharge Medications:",
            "1. Tab. Pantoprazole 40 mg - once daily before breakfast for 14 days",
            "Follow-Up Instructions:",
            "Follow up with primary physician in 7 days.",
        ]
    )
    dis_res = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("discharge.pdf", discharge_pdf, "application/pdf")},
        data={"consent_confirmed": "true"},
    )
    assert dis_res.status_code == 201
    assert dis_res.json()["classification"]["final_type"] == "discharge_summary"

    # Update retention & language preferences
    pref_res = client.patch(
        "/api/auth/preferences",
        headers=headers,
        json={"preferred_language": "es", "retention_days": 14},
    )
    assert pref_res.status_code == 200
    assert pref_res.json()["preferred_language"] == "es"
    assert pref_res.json()["retention_days"] == 14

    # Delete account & verify token no longer resolves
    del_res = client.delete("/api/auth/account", headers=headers)
    assert del_res.status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
