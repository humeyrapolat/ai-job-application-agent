from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeApplicationRequest(BaseModel):
    candidate_name: str = Field(..., min_length=2, examples=["Ada Lovelace"])
    job_title: str = Field(..., min_length=2, examples=["Junior AI Backend Developer"])
    company_name: str = Field(..., min_length=2, examples=["Example GmbH"])
    cv_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)
    use_ai_recommendations: bool = Field(default=False)


class ExtractDocumentTextRequest(BaseModel):
    filename: str = Field(..., min_length=1, examples=["cv.pdf"])
    content_base64: str = Field(..., min_length=1)
    content_type: str = Field(default="")


class ExtractDocumentTextResponse(BaseModel):
    filename: str
    text: str
    character_count: int


class WorkflowAction(BaseModel):
    kind: Literal["email_draft", "status_update", "learning_plan", "manual_review"]
    title: str
    description: str
    payload: dict[str, str] = Field(default_factory=dict)


class CVRecommendation(BaseModel):
    category: Literal[
        "keyword_optimization",
        "project_evidence",
        "impact_framing",
        "application_decision",
    ]
    priority: Literal["low", "medium", "high"]
    title: str
    explanation: str
    suggested_change: str
    example_bullet: str | None = None


class JobRequirementAnalysis(BaseModel):
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    matched_must_have_skills: list[str]
    missing_must_have_skills: list[str]
    matched_nice_to_have_skills: list[str]
    missing_nice_to_have_skills: list[str]
    language_requirements: list[str]
    location_requirements: list[str]
    degree_requirements: list[str]
    seniority: str


class ScoreBreakdown(BaseModel):
    must_have_score: int = Field(..., ge=0, le=70)
    nice_to_have_score: int = Field(..., ge=0, le=15)
    evidence_score: int = Field(..., ge=0, le=10)
    adjacent_skill_score: int = Field(..., ge=0, le=5)
    score_cap: int = Field(..., ge=0, le=100)
    confidence: Literal["low", "medium", "high"]


class AnalyzeApplicationResponse(BaseModel):
    candidate_name: str
    job_title: str
    company_name: str
    match_score: int = Field(..., ge=0, le=100)
    seniority_signal: str
    matched_skills: list[str]
    missing_skills: list[str]
    extra_candidate_skills: list[str]
    requirement_analysis: JobRequirementAnalysis
    score_breakdown: ScoreBreakdown
    recommendations: list[str]
    cv_recommendations: list[CVRecommendation]
    ai_recommendation_status: Literal["not_requested", "generated", "unavailable", "fallback"]
    cover_letter_draft: str
    cover_letter_status: Literal["deterministic", "generated", "fallback"]
    workflow_actions: list[WorkflowAction]
    explanation: str


class StoredAnalyzeApplicationResponse(AnalyzeApplicationResponse):
    application_id: int


class ApplicationSummary(BaseModel):
    id: int
    candidate_name: str
    job_title: str
    company_name: str
    match_score: int
    seniority_signal: str
    created_at: str
