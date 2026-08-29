from app.domain.schemas import AnalyzeApplicationRequest, CVRecommendation
from app.services.agent import JobApplicationAgent
from app.services.recommendations import CVRecommendationEngine


class FakeLLMProvider:
    @property
    def is_configured(self) -> bool:
        return True

    def generate_cv_recommendations(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        cv_text: str,
        job_description: str,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> list[CVRecommendation]:
        return [
            CVRecommendation(
                category="project_evidence",
                priority="high",
                title="Add stronger AI backend project evidence",
                explanation="The target role needs clearer proof of backend and AI work.",
                suggested_change="Add one bullet about FastAPI, RAG, tests, and deployment.",
                example_bullet=(
                    "Built a FastAPI-based AI backend with RAG-style retrieval and "
                    "automated tests."
                ),
            )
        ]


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
    assert response.cv_recommendations
    assert response.ai_recommendation_status == "not_requested"
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


def test_agent_caps_perfect_score_when_job_skill_evidence_is_limited() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="Backend Developer",
        company_name="Example GmbH",
        cv_text=(
            "I built Python REST API projects with FastAPI, Docker, Git, testing, "
            "React, TypeScript, and SQLite."
        ),
        job_description="We need Python and REST API experience.",
    )

    response = JobApplicationAgent().analyze(payload)

    assert response.match_score == 75
    assert response.matched_skills == ["python", "rest api"]
    assert "capped instead of treated as a perfect fit" in response.explanation


def test_agent_uses_job_title_for_seniority_signal() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="Junior AI Backend Developer",
        company_name="Example GmbH",
        cv_text="I built Python APIs with FastAPI, Git, and testing.",
        job_description="We need Python, FastAPI, REST APIs, and tests.",
    )

    response = JobApplicationAgent().analyze(payload)

    assert response.seniority_signal == "junior"


def test_agent_drafts_more_specific_cover_letter() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="AI Backend Developer",
        company_name="Example GmbH",
        cv_text="I built Python APIs with FastAPI, Git, and testing.",
        job_description="We need Python, FastAPI, Docker, REST APIs, and tests.",
    )

    response = JobApplicationAgent().analyze(payload)

    assert "Dear Example GmbH team," in response.cover_letter_draft
    assert "AI Backend Developer" in response.cover_letter_draft
    assert "FastAPI" in response.cover_letter_draft
    assert "Where the role asks for Docker" in response.cover_letter_draft
    assert response.cover_letter_draft.count("\n\n") >= 4


def test_agent_returns_structured_cv_recommendations() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="AI Backend Developer",
        company_name="Example GmbH",
        cv_text="I built Python APIs with Git and backend projects.",
        job_description="We need Python, FastAPI, Docker, RAG, LLM, testing, and CI/CD.",
    )

    response = JobApplicationAgent().analyze(payload)

    keyword_recommendation = next(
        item for item in response.cv_recommendations if item.category == "keyword_optimization"
    )

    assert keyword_recommendation.priority == "high"
    assert "fastapi" in keyword_recommendation.suggested_change.lower()
    assert any(item.category == "impact_framing" for item in response.cv_recommendations)


def test_agent_can_use_ai_recommendation_provider() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="AI Backend Developer",
        company_name="Example GmbH",
        cv_text="I built Python APIs with Git and backend projects.",
        job_description="We need Python, FastAPI, Docker, RAG, LLM, testing, and CI/CD.",
        use_ai_recommendations=True,
    )
    agent = JobApplicationAgent(
        recommendation_engine=CVRecommendationEngine(llm_provider=FakeLLMProvider())
    )

    response = agent.analyze(payload)

    assert response.ai_recommendation_status == "generated"
    assert response.cv_recommendations[0].title == "Add stronger AI backend project evidence"
