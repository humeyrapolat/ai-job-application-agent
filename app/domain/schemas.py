from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeApplicationRequest(BaseModel):
    candidate_name: str = Field(..., min_length=2, examples=["Ada Lovelace"])
    job_title: str = Field(..., min_length=2, examples=["Junior AI Backend Developer"])
    company_name: str = Field(..., min_length=2, examples=["Example GmbH"])
    cv_text: str = Field(..., min_length=20)
    job_description: str = Field(..., min_length=20)


class WorkflowAction(BaseModel):
    kind: Literal["email_draft", "status_update", "learning_plan", "manual_review"]
    title: str
    description: str
    payload: dict[str, str] = Field(default_factory=dict)


class AnalyzeApplicationResponse(BaseModel):
    candidate_name: str
    job_title: str
    company_name: str
    match_score: int = Field(..., ge=0, le=100)
    seniority_signal: str
    matched_skills: list[str]
    missing_skills: list[str]
    extra_candidate_skills: list[str]
    recommendations: list[str]
    cover_letter_draft: str
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
