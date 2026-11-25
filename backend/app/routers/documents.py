from __future__ import annotations

import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response

from app.config import SUPPORTED_LANGUAGES
from app.database import cleanup_expired_documents, db_session, parse_json_field, utc_now_iso
from app.schemas import (
    ClassificationOverrideRequest,
    DoctorSummaryOut,
    DocumentDetailOut,
    DocumentSummaryOut,
    EntityVerifyRequest,
    QARequest,
    QAResponseOut,
)
from app.security import get_current_user, validate_uploaded_bytes
from app.services.explainer import answer_document_question
from app.services.pdf_export import build_doctor_summary_payload, render_doctor_summary_pdf
from app.services.pipeline import (
    fetch_document_detail,
    process_uploaded_document,
    reprocess_classification_override,
)
from app.services.synthetic_samples import generate_synthetic_sample_files

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentDetailOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
    consent_confirmed: bool = Form(default=False),
    current_user: dict = Depends(get_current_user),
):
    if not consent_confirmed and not current_user.get("consent_accepted"):
        raise HTTPException(
            status_code=400,
            detail="Consent confirmation is required before processing medical documents.",
        )

    content = await file.read()
    ext, mime_type = validate_uploaded_bytes(file.filename or "", content)

    doc_id = process_uploaded_document(
        user=current_user,
        original_filename=file.filename or f"document{ext}",
        ext=ext,
        mime_type=mime_type,
        content=content,
        language=language or current_user["preferred_language"],
    )
    return fetch_document_detail(current_user["id"], doc_id, language or current_user["preferred_language"])


@router.post("/load-synthetic-demo", response_model=List[DocumentSummaryOut])
def load_synthetic_demo_reports(current_user: dict = Depends(get_current_user)):
    """Generate and process clearly labeled synthetic medical reports for hackathon demonstrations."""
    samples = generate_synthetic_sample_files()
    created_ids: List[str] = []
    for filename, ext, mime_type, content, report_date in samples:
        doc_id = process_uploaded_document(
            user=current_user,
            original_filename=filename,
            ext=ext,
            mime_type=mime_type,
            content=content,
            language=current_user["preferred_language"],
            override_report_date=report_date,
        )
        created_ids.append(doc_id)

    return [
        {k: v for k, v in fetch_document_detail(current_user["id"], did).items() if k not in {"raw_ocr_text", "pages", "entities", "lab_findings", "analysis"}}
        for did in created_ids
    ]


@router.get("", response_model=List[DocumentSummaryOut])
def list_documents(current_user: dict = Depends(get_current_user)):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT d.*,
                   c.predicted_type, c.final_type, c.confidence, c.is_manual_override,
                   c.signals_json, c.candidate_scores_json,
                   (SELECT COUNT(*) FROM laboratory_findings l WHERE l.document_id = d.id AND l.user_id = d.user_id) AS lab_count,
                   (SELECT COUNT(*) FROM laboratory_findings l WHERE l.document_id = d.id AND l.user_id = d.user_id AND l.status IN ('below_range', 'above_range')) AS abnormal_count,
                   (SELECT COUNT(*) FROM laboratory_findings l WHERE l.document_id = d.id AND l.user_id = d.user_id AND l.needs_verification = 1)
                     + (SELECT COUNT(*) FROM extracted_entities e WHERE e.document_id = d.id AND e.user_id = d.user_id AND e.needs_verification = 1 AND e.entity_type != 'lab_test') AS verification_needed_count,
                   (SELECT COUNT(*) FROM extracted_entities e WHERE e.document_id = d.id AND e.user_id = d.user_id AND e.entity_type = 'medication') AS medication_count
            FROM medical_documents d
            LEFT JOIN document_classifications c ON c.document_id = d.id AND c.user_id = d.user_id
            WHERE d.user_id = ?
            ORDER BY COALESCE(d.report_date, substr(d.created_at, 1, 10)) DESC, d.created_at DESC
            """,
            (current_user["id"],),
        ).fetchall()

    results = []
    for r in rows:
        results.append(
            {
                "id": r["id"],
                "original_filename": r["original_filename"],
                "mime_type": r["mime_type"],
                "file_size_bytes": r["file_size_bytes"],
                "page_count": r["page_count"],
                "report_date": r["report_date"],
                "ocr_engine": r["ocr_engine"],
                "ocr_quality_score": r["ocr_quality_score"],
                "ocr_quality_status": r["ocr_quality_status"],
                "ocr_warnings": parse_json_field(r["ocr_warnings_json"], []),
                "classification": {
                    "predicted_type": r["predicted_type"] or "other",
                    "final_type": r["final_type"] or "other",
                    "confidence": r["confidence"] if r["confidence"] is not None else 0.5,
                    "is_manual_override": bool(r["is_manual_override"]),
                    "signals": parse_json_field(r["signals_json"], []),
                    "candidate_scores": parse_json_field(r["candidate_scores_json"], {}),
                },
                "lab_count": r["lab_count"],
                "abnormal_count": r["abnormal_count"],
                "verification_needed_count": r["verification_needed_count"],
                "medication_count": r["medication_count"],
                "expires_at": r["expires_at"],
                "created_at": r["created_at"],
            }
        )
    return results


@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document(
    document_id: str,
    language: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    return fetch_document_detail(
        current_user["id"],
        document_id,
        language or current_user["preferred_language"],
    )


@router.get("/{document_id}/file")
def get_document_file(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    with db_session() as conn:
        row = conn.execute(
            "SELECT stored_path, mime_type, original_filename FROM medical_documents WHERE id = ? AND user_id = ?",
            (document_id, current_user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Medical document not found")

    file_path = Path(row["stored_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored document file not found")

    return FileResponse(
        path=str(file_path),
        media_type=row["mime_type"],
        filename=row["original_filename"],
    )


@router.patch("/{document_id}/classification", response_model=DocumentDetailOut)
def override_classification(
    document_id: str,
    req: ClassificationOverrideRequest,
    current_user: dict = Depends(get_current_user),
):
    reprocess_classification_override(
        user=current_user,
        document_id=document_id,
        new_type=req.document_type,
        language=current_user["preferred_language"],
    )
    return fetch_document_detail(current_user["id"], document_id, current_user["preferred_language"])


@router.patch("/{document_id}/entities/{entity_id}/verify")
def verify_entity(
    document_id: str,
    entity_id: str,
    req: EntityVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    with db_session() as conn:
        res = conn.execute(
            "UPDATE extracted_entities SET verified_by_user = ?, needs_verification = ? WHERE id = ? AND document_id = ? AND user_id = ?",
            (1 if req.verified else 0, 0 if req.verified else 1, entity_id, document_id, current_user["id"]),
        )
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Extracted entity not found")
    return {"ok": True, "entity_id": entity_id, "verified_by_user": req.verified}


@router.post("/{document_id}/qa", response_model=QAResponseOut)
def ask_document_assistant(
    document_id: str,
    req: QARequest,
    current_user: dict = Depends(get_current_user),
):
    lang = req.language if req.language in SUPPORTED_LANGUAGES else current_user["preferred_language"]
    detail = fetch_document_detail(current_user["id"], document_id, lang)
    ans = answer_document_question(
        question=req.question,
        doc_type=detail["classification"]["final_type"],
        raw_text=detail["raw_ocr_text"],
        pages=detail["pages"],
        lab_findings=detail["lab_findings"],
        entities=detail["entities"],
        language=lang,
    )
    qa_id = str(uuid.uuid4())
    now = utc_now_iso()
    import json

    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO qa_messages (
                id, document_id, user_id, question, answer, citations_json,
                information_unavailable, language, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                qa_id,
                document_id,
                current_user["id"],
                req.question,
                ans["answer"],
                json.dumps(ans["citations"]),
                1 if ans["information_unavailable"] else 0,
                lang,
                now,
            ),
        )

    return QAResponseOut(
        id=qa_id,
        question=req.question,
        answer=ans["answer"],
        citations=ans["citations"],
        information_unavailable=ans["information_unavailable"],
        language=lang,
        ai_provider=ans["ai_provider"],
        safety_disclaimer=ans["safety_disclaimer"],
        created_at=now,
    )


@router.get("/{document_id}/qa", response_model=List[QAResponseOut])
def get_document_qa_history(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    # Verify document ownership first
    with db_session() as conn:
        doc = conn.execute(
            "SELECT id FROM medical_documents WHERE id = ? AND user_id = ?",
            (document_id, current_user["id"]),
        ).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Medical document not found")

        rows = conn.execute(
            "SELECT * FROM qa_messages WHERE document_id = ? AND user_id = ? ORDER BY created_at ASC",
            (document_id, current_user["id"]),
        ).fetchall()

    from app.config import MEDICAL_DISCLAIMER

    return [
        QAResponseOut(
            id=r["id"],
            question=r["question"],
            answer=r["answer"],
            citations=parse_json_field(r["citations_json"], []),
            information_unavailable=bool(r["information_unavailable"]),
            language=r["language"],
            ai_provider="history",
            safety_disclaimer=MEDICAL_DISCLAIMER,
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/{document_id}/doctor-summary", response_model=DoctorSummaryOut)
def get_doctor_summary(
    document_id: str,
    language: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    lang = language if language in SUPPORTED_LANGUAGES else current_user["preferred_language"]
    detail = fetch_document_detail(current_user["id"], document_id, lang)
    return build_doctor_summary_payload(
        user=current_user,
        doc=detail,
        classification=detail["classification"],
        entities=detail["entities"],
        lab_findings=detail["lab_findings"],
        analysis=detail["analysis"] or {},
        language=lang,
    )


@router.get("/{document_id}/doctor-summary/pdf")
def export_doctor_summary_pdf(
    document_id: str,
    language: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    lang = language if language in SUPPORTED_LANGUAGES else current_user["preferred_language"]
    detail = fetch_document_detail(current_user["id"], document_id, lang)
    summary = build_doctor_summary_payload(
        user=current_user,
        doc=detail,
        classification=detail["classification"],
        entities=detail["entities"],
        lab_findings=detail["lab_findings"],
        analysis=detail["analysis"] or {},
        language=lang,
    )
    pdf_bytes = render_doctor_summary_pdf(summary)
    safe_stem = Path(detail["original_filename"]).stem.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="MediScan_Doctor_Summary_{safe_stem}.pdf"'
        },
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    with db_session() as conn:
        row = conn.execute(
            "SELECT stored_path FROM medical_documents WHERE id = ? AND user_id = ?",
            (document_id, current_user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Medical document not found")

        p = Path(row["stored_path"])
        if p.exists():
            p.unlink(missing_ok=True)
        conn.execute("DELETE FROM medical_documents WHERE id = ? AND user_id = ?", (document_id, current_user["id"]))

    return {"deleted": True, "document_id": document_id}


@router.post("/cleanup-expired")
def trigger_cleanup(current_user: dict = Depends(get_current_user)):
    removed = cleanup_expired_documents()
    return {"cleaned_up_documents": removed}
