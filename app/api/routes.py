from fastapi import APIRouter

from app.domain.schemas import AnalyzeApplicationRequest, AnalyzeApplicationResponse
from app.services.agent import JobApplicationAgent
from app.services.skills import KNOWN_SKILLS

router = APIRouter()
agent = JobApplicationAgent()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/skills")
def list_known_skills() -> dict[str, list[str]]:
    return {"skills": sorted(KNOWN_SKILLS)}


@router.post("/applications/analyze", response_model=AnalyzeApplicationResponse)
def analyze_application(payload: AnalyzeApplicationRequest) -> AnalyzeApplicationResponse:
    return agent.analyze(payload)

