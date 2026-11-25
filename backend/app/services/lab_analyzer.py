from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

# Canonical test aliasing for accurate cross-report matching (never compares different tests)
CANONICAL_TEST_ALIASES: Dict[str, Tuple[str, str]] = {
    "hemoglobin": ("hemoglobin", "Hemoglobin"),
    "hb": ("hemoglobin", "Hemoglobin"),
    "hgb": ("hemoglobin", "Hemoglobin"),
    "haemoglobin": ("hemoglobin", "Hemoglobin"),
    "wbc": ("wbc_count", "White Blood Cell Count (WBC)"),
    "white blood cell": ("wbc_count", "White Blood Cell Count (WBC)"),
    "white blood cells": ("wbc_count", "White Blood Cell Count (WBC)"),
    "total leukocyte count": ("wbc_count", "White Blood Cell Count (WBC)"),
    "tlc": ("wbc_count", "White Blood Cell Count (WBC)"),
    "rbc": ("rbc_count", "Red Blood Cell Count (RBC)"),
    "red blood cell": ("rbc_count", "Red Blood Cell Count (RBC)"),
    "platelet": ("platelet_count", "Platelet Count"),
    "platelets": ("platelet_count", "Platelet Count"),
    "platelet count": ("platelet_count", "Platelet Count"),
    "hematocrit": ("hematocrit", "Hematocrit (HCT)"),
    "hct": ("hematocrit", "Hematocrit (HCT)"),
    "pcv": ("hematocrit", "Hematocrit (HCT)"),
    "mcv": ("mcv", "Mean Corpuscular Volume (MCV)"),
    "mch": ("mch", "Mean Corpuscular Hemoglobin (MCH)"),
    "mchc": ("mchc", "Mean Corpuscular Hemoglobin Concentration (MCHC)"),
    "fasting glucose": ("fasting_glucose", "Fasting Blood Glucose"),
    "fasting blood sugar": ("fasting_glucose", "Fasting Blood Glucose"),
    "fbs": ("fasting_glucose", "Fasting Blood Glucose"),
    "glucose fasting": ("fasting_glucose", "Fasting Blood Glucose"),
    "random blood sugar": ("random_glucose", "Random Blood Glucose"),
    "rbs": ("random_glucose", "Random Blood Glucose"),
    "hba1c": ("hba1c", "Glycated Hemoglobin (HbA1c)"),
    "glycated hemoglobin": ("hba1c", "Glycated Hemoglobin (HbA1c)"),
    "a1c": ("hba1c", "Glycated Hemoglobin (HbA1c)"),
    "total cholesterol": ("total_cholesterol", "Total Cholesterol"),
    "cholesterol total": ("total_cholesterol", "Total Cholesterol"),
    "ldl": ("ldl_cholesterol", "LDL Cholesterol"),
    "ldl cholesterol": ("ldl_cholesterol", "LDL Cholesterol"),
    "hdl": ("hdl_cholesterol", "HDL Cholesterol"),
    "hdl cholesterol": ("hdl_cholesterol", "HDL Cholesterol"),
    "triglycerides": ("triglycerides", "Triglycerides"),
    "creatinine": ("creatinine", "Serum Creatinine"),
    "serum creatinine": ("creatinine", "Serum Creatinine"),
    "egfr": ("egfr", "Estimated GFR (eGFR)"),
    "bun": ("bun", "Blood Urea Nitrogen (BUN)"),
    "blood urea nitrogen": ("bun", "Blood Urea Nitrogen (BUN)"),
    "urea": ("urea", "Blood Urea"),
    "alt": ("alt_sgpt", "ALT (SGPT)"),
    "sgpt": ("alt_sgpt", "ALT (SGPT)"),
    "ast": ("ast_sgot", "AST (SGOT)"),
    "sgot": ("ast_sgot", "AST (SGOT)"),
    "total bilirubin": ("total_bilirubin", "Total Bilirubin"),
    "bilirubin total": ("total_bilirubin", "Total Bilirubin"),
    "tsh": ("tsh", "Thyroid Stimulating Hormone (TSH)"),
    "sodium": ("sodium", "Serum Sodium"),
    "potassium": ("potassium", "Serum Potassium"),
    "vitamin d": ("vitamin_d", "Vitamin D (25-OH)"),
    "25-oh vitamin d": ("vitamin_d", "Vitamin D (25-OH)"),
    "vitamin b12": ("vitamin_b12", "Vitamin B12"),
    "ferritin": ("ferritin", "Serum Ferritin"),
    "urine ph": ("urine_ph", "Urine pH"),
    "specific gravity": ("urine_specific_gravity", "Urine Specific Gravity"),
    "urine albumin": ("urine_albumin", "Urine Albumin"),
    "microalbumin": ("urine_microalbumin", "Urine Microalbumin"),
    "urine protein": ("urine_protein", "Urine Protein"),
}


UNIT_CANONICAL_MAP: Dict[str, str] = {
    "g/dl": "g/dL",
    "gm/dl": "g/dL",
    "g/l": "g/L",
    "mg/dl": "mg/dL",
    "mmol/l": "mmol/L",
    "umol/l": "umol/L",
    "µmol/l": "umol/L",
    "u/l": "U/L",
    "iu/l": "U/L",
    "miu/l": "mIU/L",
    "uiu/ml": "mIU/L",
    "µiu/ml": "mIU/L",
    "meq/l": "mEq/L",
    "%": "%",
    "fl": "fL",
    "pg": "pg",
    "ng/ml": "ng/mL",
    "pg/ml": "pg/mL",
    "cells/ul": "cells/uL",
    "cells/µl": "cells/uL",
    "/ul": "cells/uL",
    "k/ul": "10^3/uL",
    "10^3/ul": "10^3/uL",
    "x10^3/ul": "10^3/uL",
    "10^3/µl": "10^3/uL",
    "x10^9/l": "10^3/uL",
    "10^9/l": "10^3/uL",
    "lakhs/cumm": "lakhs/cumm",
    "10^6/ul": "10^6/uL",
    "million/ul": "10^6/uL",
    "10^12/l": "10^6/uL",
    "ml/min/1.73m2": "mL/min/1.73m2",
    "hpf": "/HPF",
    "/hpf": "/HPF",
}


def canonicalize_test_name(raw_name: str) -> Tuple[str, str]:
    cleaned = re.sub(r"[^a-z0-9\s/-]", " ", raw_name.lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned in CANONICAL_TEST_ALIASES:
        return CANONICAL_TEST_ALIASES[cleaned]
    for alias, pair in CANONICAL_TEST_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", cleaned):
            return pair
    key = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_") or "unknown_test"
    return key, raw_name.strip()


def canonicalize_unit(raw_unit: Optional[str]) -> Optional[str]:
    if not raw_unit:
        return None
    u = raw_unit.strip().replace(" ", "").lower()
    u = u.replace("μ", "u").replace("µ", "u")
    return UNIT_CANONICAL_MAP.get(u, raw_unit.strip())


def parse_reference_interval(ref_text: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """Parse printed reference range without ever inventing missing limits."""
    if not ref_text:
        return None, None
    s = ref_text.strip()
    if not s:
        return None, None

    # Range: e.g. "13.5 - 17.5", "4.5–11.0", "70 to 99"
    range_match = re.search(
        r"(-?\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(-?\d+(?:\.\d+)?)",
        s,
        flags=re.IGNORECASE,
    )
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        if low <= high:
            return low, high
        return high, low

    # Upper bound only: "< 200", "<= 150", "up to 40"
    upper_match = re.search(
        r"(?:<=|<|less than|up to|below)\s*(-?\d+(?:\.\d+)?)",
        s,
        flags=re.IGNORECASE,
    )
    if upper_match:
        return None, float(upper_match.group(1))

    # Lower bound only: "> 40", ">= 60"
    lower_match = re.search(
        r"(?:>=|>|greater than|above)\s*(-?\d+(?:\.\d+)?)",
        s,
        flags=re.IGNORECASE,
    )
    if lower_match:
        return float(lower_match.group(1)), None

    return None, None


def parse_numeric_value(value_raw: str) -> Tuple[Optional[float], bool, Optional[str]]:
    """Extract float from raw value string and note ambiguity if present."""
    if not value_raw:
        return None, True, "Empty measurement value."
    s = value_raw.strip()
    # Clean commas in numbers like 150,000
    s_clean = s.replace(",", "")
    if re.fullmatch(r"[<>]=?\s*-?\d+(?:\.\d+)?", s_clean):
        num = float(re.sub(r"[<>=\s]", "", s_clean))
        return num, True, f"Qualifier prefix present in '{value_raw}'; verify exact bound."
    m = re.search(r"-?\d+(?:\.\d+)?", s_clean)
    if not m:
        return None, False, None
    return float(m.group(0)), False, None


def evaluate_lab_finding(
    value_raw: str,
    unit: Optional[str],
    ref_text: Optional[str],
    confidence: float = 0.85,
) -> dict:
    """Compare result ONLY against printed reference interval; never invent missing ranges."""
    value_num, val_uncertain, val_reason = parse_numeric_value(value_raw)
    ref_low, ref_high = parse_reference_interval(ref_text)
    needs_verification = val_uncertain or confidence < 0.72
    reasons = [r for r in [val_reason] if r]

    if confidence < 0.72:
        reasons.append("Low OCR confidence on this line; please verify against the original report.")

    if value_num is None:
        return {
            "value_numeric": None,
            "ref_low": ref_low,
            "ref_high": ref_high,
            "status": "manual_verification_needed" if needs_verification else "reference_unavailable",
            "deviation_pct": None,
            "needs_verification": True if not ref_text else needs_verification,
            "verification_reason": "; ".join(reasons) if reasons else "Non-numeric or qualitative lab result.",
        }

    if ref_low is None and ref_high is None:
        return {
            "value_numeric": value_num,
            "ref_low": None,
            "ref_high": None,
            "status": "reference_unavailable",
            "deviation_pct": None,
            "needs_verification": needs_verification,
            "verification_reason": "; ".join(reasons)
            if reasons
            else "No printed reference range detected on the source report.",
        }

    if not unit:
        needs_verification = True
        reasons.append("Measurement unit missing on extracted line; confirm unit on source document.")

    status = "within_range"
    deviation_pct: Optional[float] = None

    if ref_low is not None and value_num < ref_low:
        status = "below_range"
        if ref_low != 0:
            deviation_pct = round(((value_num - ref_low) / abs(ref_low)) * 100.0, 1)
    elif ref_high is not None and value_num > ref_high:
        status = "above_range"
        if ref_high != 0:
            deviation_pct = round(((value_num - ref_high) / abs(ref_high)) * 100.0, 1)

    if needs_verification and status == "within_range":
        status = "manual_verification_needed"

    return {
        "value_numeric": value_num,
        "ref_low": ref_low,
        "ref_high": ref_high,
        "status": status,
        "deviation_pct": deviation_pct,
        "needs_verification": needs_verification,
        "verification_reason": "; ".join(reasons) if reasons else None,
    }


def units_are_compatible(unit_a: Optional[str], unit_b: Optional[str]) -> Tuple[bool, str]:
    """Never compare incompatible units or missing-unit vs unitful measurements."""
    ca = canonicalize_unit(unit_a)
    cb = canonicalize_unit(unit_b)
    if ca and cb:
        if ca == cb:
            return True, f"Matching unit ({ca})"
        return False, f"Incompatible measurement units: '{unit_a}' vs '{unit_b}'. Conversion not assumed."
    if not ca and not cb:
        return False, "Units missing in both reports; cannot safely verify comparability."
    return False, f"Unit present in only one report ('{unit_a or 'missing'}' vs '{unit_b or 'missing'}')."
