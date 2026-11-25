from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.config import MEDICAL_DISCLAIMER
from app.database import db_session, parse_json_field
from app.schemas import CompareRequest, ComparisonResultOut
from app.security import get_current_user
from app.services.comparator import build_medical_timeline, compare_reports

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.post("/compare", response_model=ComparisonResultOut)
def compare_two_reports(
    req: CompareRequest,
    current_user: dict = Depends(get_current_user),
):
    if req.doc_a_id == req.doc_b_id:
        raise HTTPException(status_code=400, detail="Please select two different documents to compare.")

    with db_session() as conn:
        doc_a = conn.execute(
            "SELECT * FROM medical_documents WHERE id = ? AND user_id = ?",
            (req.doc_a_id, current_user["id"]),
        ).fetchone()
        doc_b = conn.execute(
            "SELECT * FROM medical_documents WHERE id = ? AND user_id = ?",
            (req.doc_b_id, current_user["id"]),
        ).fetchone()
        if not doc_a or not doc_b:
            raise HTTPException(status_code=404, detail="One or both selected documents were not found.")

        labs_a = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM laboratory_findings WHERE document_id = ? AND user_id = ?",
                (req.doc_a_id, current_user["id"]),
            ).fetchall()
        ]
        labs_b = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM laboratory_findings WHERE document_id = ? AND user_id = ?",
                (req.doc_b_id, current_user["id"]),
            ).fetchall()
        ]

        result = compare_reports(dict(doc_a), labs_a, dict(doc_b), labs_b)
        conn.execute(
            """
            INSERT INTO report_comparisons (
                id, user_id, doc_a_id, doc_b_id, matched_count, incompatible_count, result_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["id"],
                current_user["id"],
                req.doc_a_id,
                req.doc_b_id,
                len(result["matched_tests"]),
                len(result["incompatible_tests"]),
                json.dumps(result),
                result["created_at"],
            ),
        )
    return ComparisonResultOut(**result)


@router.get("/comparisons")
def list_comparisons(current_user: dict = Depends(get_current_user)):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM report_comparisons WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (current_user["id"],),
        ).fetchall()
    return [parse_json_field(r["result_json"], {}) for r in rows]


@router.get("/timeline")
def get_timeline(current_user: dict = Depends(get_current_user)):
    with db_session() as conn:
        docs = [
            dict(r)
            for r in conn.execute(
                """
                SELECT d.id, d.original_filename, d.report_date, d.created_at,
                       d.ocr_quality_status, c.final_type AS document_type
                FROM medical_documents d
                LEFT JOIN document_classifications c ON c.document_id = d.id AND c.user_id = d.user_id
                WHERE d.user_id = ?
                """,
                (current_user["id"],),
            ).fetchall()
        ]
        labs_rows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM laboratory_findings WHERE user_id = ?",
                (current_user["id"],),
            ).fetchall()
        ]

    labs_by_doc: Dict[str, List[dict]] = defaultdict(list)
    for lab in labs_rows:
        labs_by_doc[lab["document_id"]].append(lab)

    return build_medical_timeline(docs, labs_by_doc)


@router.get("/prescriptions")
def list_prescriptions(current_user: dict = Depends(get_current_user)):
    with db_session() as conn:
        med_rows = conn.execute(
            """
            SELECT e.*, d.original_filename, d.report_date, d.created_at AS doc_created_at,
                   c.final_type AS document_type
            FROM extracted_entities e
            JOIN medical_documents d ON d.id = e.document_id AND d.user_id = e.user_id
            LEFT JOIN document_classifications c ON c.document_id = d.id AND c.user_id = d.user_id
            WHERE e.user_id = ? AND e.entity_type = 'medication'
            ORDER BY COALESCE(d.report_date, substr(d.created_at, 1, 10)) DESC, e.created_at DESC
            """,
            (current_user["id"],),
        ).fetchall()

    items = []
    for r in med_rows:
        items.append(
            {
                "id": r["id"],
                "document_id": r["document_id"],
                "filename": r["original_filename"],
                "document_type": r["document_type"] or "prescription",
                "report_date": r["report_date"] or r["doc_created_at"][:10],
                "medicine_name": r["name"],
                "dosage": r["dosage"],
                "frequency": r["frequency"],
                "duration": r["duration"],
                "instructions": r["observation"],
                "source_page": r["source_page"],
                "source_snippet": r["source_snippet"],
                "confidence": r["confidence"],
                "needs_verification": bool(r["needs_verification"]),
                "verification_reason": r["verification_reason"],
                "verified_by_user": bool(r["verified_by_user"]),
            }
        )

    return {
        "medications": items,
        "safety_notice": (
            "MediScan AI displays medications and dosages exactly as printed on your uploaded documents. "
            "It never generates new prescriptions or recommends changing your dosage. "
            + MEDICAL_DISCLAIMER
        ),
    }
