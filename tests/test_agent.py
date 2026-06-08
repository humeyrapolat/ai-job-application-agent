from app.domain.schemas import AnalyzeApplicationRequest
from app.services.agent import JobApplicationAgent


def test_agent_returns_high_score_for_matching_profile() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="Junior AI Backend Developer",
        company_name="Example GmbH",
        cv_text=(
            "I built projects with Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, "
            "OpenAI API, and testing."
        ),
        job_description=(
            "We need a junior developer with Python, FastAPI, PostgreSQL, Docker, REST APIs, "
            "Git, LLM experience, and unit tests."
        ),
    )

    response = JobApplicationAgent().analyze(payload)

    assert response.match_score >= 75
    assert "python" in response.matched_skills
    assert "fastapi" in response.matched_skills
    assert response.seniority_signal == "junior"
    assert response.workflow_actions


def test_agent_recommends_learning_plan_when_skills_are_missing() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="Backend Automation Developer",
        company_name="Example GmbH",
        cv_text="I built Python APIs with Flask and Git.",
        job_description="We need Python, FastAPI, PostgreSQL, Docker, n8n, and RAG.",
    )

    response = JobApplicationAgent().analyze(payload)

    assert response.match_score < 80
    assert "fastapi" in response.missing_skills
    assert any(action.kind == "learning_plan" for action in response.workflow_actions)

