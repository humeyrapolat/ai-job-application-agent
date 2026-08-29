from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.database import initialize_database
from app.domain.schemas import (
    AnalyzeApplicationRequest,
    ApplicationSummary,
    ExtractDocumentTextRequest,
    ExtractDocumentTextResponse,
    StoredAnalyzeApplicationResponse,
)
from app.services.agent import JobApplicationAgent
from app.services.document_text import DocumentTextExtractionError, extract_document_text
from app.services.repository import ApplicationRepository
from app.services.skills import KNOWN_SKILLS

router = APIRouter()
agent = JobApplicationAgent()
repository = ApplicationRepository()
initialize_database()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/skills")
def list_known_skills() -> dict[str, list[str]]:
    return {"skills": sorted(KNOWN_SKILLS)}


@router.post("/documents/extract-text", response_model=ExtractDocumentTextResponse)
def extract_text_from_document(
    payload: ExtractDocumentTextRequest,
) -> ExtractDocumentTextResponse:
    try:
        text = extract_document_text(
            filename=payload.filename,
            content_base64=payload.content_base64,
        )
    except DocumentTextExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ExtractDocumentTextResponse(
        filename=payload.filename,
        text=text,
        character_count=len(text),
    )


@router.post("/applications/analyze", response_model=StoredAnalyzeApplicationResponse)
def analyze_application(payload: AnalyzeApplicationRequest) -> StoredAnalyzeApplicationResponse:
    analysis = agent.analyze(payload)
    application_id = repository.save_analysis(analysis)

    return StoredAnalyzeApplicationResponse(
        application_id=application_id,
        **analysis.dict(),
    )


@router.get("/applications", response_model=list[ApplicationSummary])
def list_applications() -> list[ApplicationSummary]:
    return [ApplicationSummary(**item) for item in repository.list_analyses()]


@router.get("/applications/{application_id}")
def get_application(application_id: int) -> dict[str, Any]:
    application = repository.get_analysis(application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application analysis not found")

    return application
