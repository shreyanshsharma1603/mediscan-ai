from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any, Dict, List

from app.config import MEDICAL_DISCLAIMER
from app.database import utc_now_iso
from app.services.lab_analyzer import units_are_compatible


def compare_reports(
    doc_a: dict,
    labs_a: List[dict],
    doc_b: dict,
    labs_b: List[dict],
) -> dict:
    """Compare two reports by matching canonical tests AND enforcing unit compatibility."""
    map_a: Dict[str, dict] = {}
    for item in labs_a:
        key = item["canonical_test_key"]
        if key not in map_a:
            map_a[key] = item

    map_b: Dict[str, dict] = {}
    for item in labs_b:
        key = item["canonical_test_key"]
        if key not in map_b:
            map_b[key] = item

    matched_tests: List[dict] = []
    incompatible_tests: List[dict] = []
    only_in_a: List[str] = []
    only_in_b: List[str] = []

    all_keys = sorted(set(map_a.keys()) | set(map_b.keys()))
    for key in all_keys:
        in_a = map_a.get(key)
        in_b = map_b.get(key)
        if in_a and not in_b:
            only_in_a.append(in_a["test_name"])
            continue
        if in_b and not in_a:
            only_in_b.append(in_b["test_name"])
            continue
        assert in_a and in_b

        compatible, reason = units_are_compatible(in_a.get("unit"), in_b.get("unit"))
        if not compatible or in_a.get("value_numeric") is None or in_b.get("value_numeric") is None:
            if not compatible:
                incompatible_tests.append(
                    {
                        "test_name_a": in_a["test_name"],
                        "unit_a": in_a.get("unit"),
                        "test_name_b": in_b["test_name"],
                        "unit_b": in_b.get("unit"),
                        "reason": reason,
                    }
                )
            else:
                incompatible_tests.append(
                    {
                        "test_name_a": in_a["test_name"],
                        "unit_a": in_a.get("unit"),
                        "test_name_b": in_b["test_name"],
                        "unit_b": in_b.get("unit"),
                        "reason": "One or both values are non-numeric and cannot be compared quantitatively.",
                    }
                )
            continue

        val_a = float(in_a["value_numeric"])
        val_b = float(in_b["value_numeric"])
        abs_change = round(val_b - val_a, 3)
        pct_change = round(((val_b - val_a) / abs(val_a)) * 100.0, 2) if val_a != 0 else None
        if abs_change > 0:
            direction = "increased"
        elif abs_change < 0:
            direction = "decreased"
        else:
            direction = "unchanged"

        matched_tests.append(
            {
                "canonical_test_key": key,
                "display_name": in_b["test_name"] or in_a["test_name"],
                "unit": in_a.get("canonical_unit") or in_a.get("unit"),
                "value_a": val_a,
                "value_a_raw": in_a["value_raw"],
                "status_a": in_a["status"],
                "date_a": doc_a.get("report_date") or doc_a.get("created_at", "")[:10],
                "value_b": val_b,
                "value_b_raw": in_b["value_raw"],
                "status_b": in_b["status"],
                "date_b": doc_b.get("report_date") or doc_b.get("created_at", "")[:10],
                "absolute_change": abs_change,
                "percent_change": pct_change,
                "direction": direction,
            }
        )

    summary_lines = [
        f"Compared '{doc_a['original_filename']}' with '{doc_b['original_filename']}'.",
        f"Matched {len(matched_tests)} comparable test(s) with identical units.",
    ]
    if incompatible_tests:
        summary_lines.append(
            f"Excluded {len(incompatible_tests)} test(s) from numerical comparison due to incompatible or missing units."
        )

    return {
        "id": str(uuid.uuid4()),
        "doc_a": {
            "id": doc_a["id"],
            "filename": doc_a["original_filename"],
            "report_date": doc_a.get("report_date") or doc_a.get("created_at", "")[:10],
        },
        "doc_b": {
            "id": doc_b["id"],
            "filename": doc_b["original_filename"],
            "report_date": doc_b.get("report_date") or doc_b.get("created_at", "")[:10],
        },
        "matched_tests": matched_tests,
        "incompatible_tests": incompatible_tests,
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "narrative_summary": " ".join(summary_lines),
        "safety_disclaimer": MEDICAL_DISCLAIMER,
        "created_at": utc_now_iso(),
    }


def build_medical_timeline(documents: List[dict], labs_by_doc: Dict[str, List[dict]]) -> dict:
    """Chronological documents + trend series ONLY where test key & canonical unit match."""
    def sort_key(d: dict) -> str:
        return d.get("report_date") or d.get("created_at", "")[:10]

    ordered_docs = sorted(documents, key=sort_key)

    series_buckets: Dict[tuple[str, str], List[dict]] = defaultdict(list)
    for doc in ordered_docs:
        date_label = sort_key(doc)
        for lab in labs_by_doc.get(doc["id"], []):
            if lab.get("value_numeric") is None or not lab.get("canonical_unit"):
                continue
            bucket_key = (lab["canonical_test_key"], lab["canonical_unit"])
            series_buckets[bucket_key].append(
                {
                    "date": date_label,
                    "document_id": doc["id"],
                    "filename": doc["original_filename"],
                    "test_name": lab["test_name"],
                    "value": lab["value_numeric"],
                    "unit": lab["canonical_unit"],
                    "ref_low": lab.get("ref_low"),
                    "ref_high": lab.get("ref_high"),
                    "status": lab["status"],
                }
            )

    comparable_trends = []
    for (test_key, unit), points in sorted(series_buckets.items()):
        if len(points) >= 2:
            comparable_trends.append(
                {
                    "canonical_test_key": test_key,
                    "display_name": points[-1]["test_name"],
                    "unit": unit,
                    "points": points,
                }
            )

    return {
        "timeline_documents": ordered_docs,
        "comparable_trends": comparable_trends,
        "safety_disclaimer": MEDICAL_DISCLAIMER,
    }
