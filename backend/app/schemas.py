from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


DocumentType = Literal[
    "blood_test",
    "urine_test",
    "prescription",
    "radiology",
    "discharge_summary",
    "clinical_notes",
    "other",
]

LabStatus = Literal[
    "below_range",
    "within_range",
    "above_range",
    "reference_unavailable",
    "manual_verification_needed",
]


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=120)
    preferred_language: str = Field(default="en")
    consent_accepted: bool = Field(...)


class LoginRequest(BaseModel):
    email: str
    password: str


class PreferencesUpdateRequest(BaseModel):
    preferred_language: Optional[str] = None
    retention_days: Optional[int] = Field(default=None, ge=1, le=365)


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    preferred_language: str
    consent_accepted: bool
    consent_accepted_at: Optional[str] = None
    retention_days: int
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class OCRPageOut(BaseModel):
    page_number: int
    method: str
    text: str
    avg_confidence: float


class ClassificationOut(BaseModel):
    predicted_type: DocumentType
    final_type: DocumentType
    confidence: float
    is_manual_override: bool
    signals: List[str]
    candidate_scores: Dict[str, float]


class ClassificationOverrideRequest(BaseModel):
    document_type: DocumentType


class ExtractedEntityOut(BaseModel):
    id: str
    entity_type: str
    name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    date_value: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    observation: Optional[str] = None
    source_page: int = 1
    source_snippet: str = ""
    confidence: float = 0.8
    needs_verification: bool = False
    verification_reason: Optional[str] = None
    verified_by_user: bool = False


class EntityVerifyRequest(BaseModel):
    verified: bool = True


class LabFindingOut(BaseModel):
    id: str
    test_name: str
    canonical_test_key: str
    value_numeric: Optional[float] = None
    value_raw: str
    unit: Optional[str] = None
    canonical_unit: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    ref_text: Optional[str] = None
    status: LabStatus
    deviation_pct: Optional[float] = None
    source_page: int = 1
    source_snippet: str = ""
    confidence: float = 0.8
    needs_verification: bool = False
    verification_reason: Optional[str] = None


class TerminologyItem(BaseModel):
    term: str
    plain_definition: str


class FindingExplanation(BaseModel):
    item_name: str
    explanation: str
    uncertainty_note: Optional[str] = None


class AIAnalysisOut(BaseModel):
    language: str
    ai_provider: str
    plain_summary: str
    key_takeaways: List[str]
    finding_explanations: List[FindingExplanation]
    terminology_glossary: List[TerminologyItem]
    questions_for_doctor: List[str]
    uncertainty_notes: List[str]
    safety_disclaimer: str


class DocumentSummaryOut(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    report_date: Optional[str] = None
    ocr_engine: str
    ocr_quality_score: float
    ocr_quality_status: str
    ocr_warnings: List[str]
    classification: ClassificationOut
    lab_count: int = 0
    abnormal_count: int = 0
    verification_needed_count: int = 0
    medication_count: int = 0
    expires_at: Optional[str] = None
    created_at: str


class DocumentDetailOut(DocumentSummaryOut):
    raw_ocr_text: str
    pages: List[OCRPageOut]
    entities: List[ExtractedEntityOut]
    lab_findings: List[LabFindingOut]
    analysis: Optional[AIAnalysisOut] = None


class CompareRequest(BaseModel):
    doc_a_id: str
    doc_b_id: str
    language: str = "en"


class MatchedTestComparison(BaseModel):
    canonical_test_key: str
    display_name: str
    unit: Optional[str] = None
    value_a: Optional[float] = None
    value_a_raw: str
    status_a: str
    date_a: Optional[str] = None
    value_b: Optional[float] = None
    value_b_raw: str
    status_b: str
    date_b: Optional[str] = None
    absolute_change: Optional[float] = None
    percent_change: Optional[float] = None
    direction: str


class IncompatibleComparison(BaseModel):
    test_name_a: str
    unit_a: Optional[str] = None
    test_name_b: str
    unit_b: Optional[str] = None
    reason: str


class ComparisonResultOut(BaseModel):
    id: str
    doc_a: Dict[str, Any]
    doc_b: Dict[str, Any]
    matched_tests: List[MatchedTestComparison]
    incompatible_tests: List[IncompatibleComparison]
    only_in_a: List[str]
    only_in_b: List[str]
    narrative_summary: str
    safety_disclaimer: str
    created_at: str


class QARequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    language: str = "en"


class QACitation(BaseModel):
    page: int
    snippet: str


class QAResponseOut(BaseModel):
    id: str
    question: str
    answer: str
    citations: List[QACitation]
    information_unavailable: bool
    language: str
    ai_provider: str
    safety_disclaimer: str
    created_at: str


class DoctorSummaryOut(BaseModel):
    document_id: str
    patient_name: str
    document_type: str
    report_date: Optional[str] = None
    language: str
    concise_clinical_summary: str
    extracted_values: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    radiology_sections: List[Dict[str, Any]]
    uncertainties_for_verification: List[str]
    questions_for_clinician: List[str]
    safety_disclaimer: str
