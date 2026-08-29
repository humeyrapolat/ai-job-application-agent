from app.domain.schemas import AnalyzeApplicationRequest, CVRecommendation, JobRequirementAnalysis
from app.services.agent import JobApplicationAgent
from app.services.cover_letter import CoverLetterEngine
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
                suggested_change=(
                    "Use the first project section to show clearer backend delivery evidence."
                ),
                example_bullet="Documented backend project scope and implementation decisions.",
            )
        ]

    def generate_cover_letter(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        cv_text: str,
        job_description: str,
        matched_skills: list[str],
        missing_skills: list[str],
        extra_candidate_skills: list[str],
        requirement_analysis: JobRequirementAnalysis,
    ) -> str:
        return (
            f"Dear {company_name} team,\n\n"
            f"I am excited to apply for the {job_title} role with hands-on FastAPI and "
            "LLM project experience.\n\n"
            "Best regards,\n"
            f"{candidate_name}"
        )


class OverclaimingLLMProvider(FakeLLMProvider):
    def generate_cover_letter(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        cv_text: str,
        job_description: str,
        matched_skills: list[str],
        missing_skills: list[str],
        extra_candidate_skills: list[str],
        requirement_analysis: JobRequirementAnalysis,
    ) -> str:
        return (
            f"Dear {company_name} team,\n\n"
            "I hold a Bachelor's degree in Computer Science and speak German B2.\n\n"
            "I improved backend accuracy by 95%.\n\n"
            "Best regards,\n"
            f"{candidate_name}"
        )


class UnsupportedRecommendationLLMProvider(FakeLLMProvider):
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
                title="Claim unsupported RAG impact",
                explanation="This recommendation invents unsupported delivery metrics.",
                suggested_change="Add a RAG success metric.",
                example_bullet="Built a RAG system that improved answer accuracy by 95%.",
            )
        ]


def test_agent_returns_high_score_for_matching_profile() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="Junior AI Backend Developer",
        company_name="Example GmbH",
        cv_text=(
            "I built AI backend projects with Python, FastAPI, PostgreSQL, Docker, REST "
            "APIs, Git, OpenAI API, LLM integrations, and testing."
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
    assert "capped at 75" in response.explanation


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
    assert "Docker" in response.cover_letter_draft
    assert "actively strengthening" in response.cover_letter_draft
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
    assert any(
        skill in keyword_recommendation.suggested_change.lower()
        for skill in ("ci/cd", "docker", "fastapi")
    )
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
        recommendation_engine=CVRecommendationEngine(llm_provider=FakeLLMProvider()),
        cover_letter_engine=CoverLetterEngine(llm_provider=FakeLLMProvider()),
    )

    response = agent.analyze(payload)

    assert response.ai_recommendation_status == "generated"
    assert response.cv_recommendations[0].title == "Add stronger AI backend project evidence"
    assert response.cover_letter_status == "generated"
    assert "hands-on FastAPI and LLM project experience" in response.cover_letter_draft


def test_agent_falls_back_when_ai_recommendations_claim_unsupported_facts() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="AI Backend Developer",
        company_name="Example GmbH",
        cv_text="I built Python APIs with FastAPI, Git, and testing.",
        job_description="We need Python, FastAPI, RAG, LLM, Docker, and testing.",
        use_ai_recommendations=True,
    )
    agent = JobApplicationAgent(
        recommendation_engine=CVRecommendationEngine(
            llm_provider=UnsupportedRecommendationLLMProvider()
        ),
        cover_letter_engine=CoverLetterEngine(llm_provider=FakeLLMProvider()),
    )

    response = agent.analyze(payload)

    assert response.ai_recommendation_status == "fallback"
    assert all("95%" not in item.suggested_change for item in response.cv_recommendations)
    assert all(
        item.example_bullet is None or "95%" not in item.example_bullet
        for item in response.cv_recommendations
    )


def test_agent_falls_back_when_ai_cover_letter_claims_unsupported_facts() -> None:
    payload = AnalyzeApplicationRequest(
        candidate_name="Ada Lovelace",
        job_title="AI Backend Developer",
        company_name="Example GmbH",
        cv_text="I built Python APIs with FastAPI, Git, OpenAI API, and testing.",
        job_description=(
            "Requirements: Python, FastAPI, LLM, and testing. German B2 is required. "
            "Bachelor degree in computer science or related field."
        ),
        use_ai_recommendations=True,
    )
    agent = JobApplicationAgent(
        recommendation_engine=CVRecommendationEngine(llm_provider=FakeLLMProvider()),
        cover_letter_engine=CoverLetterEngine(llm_provider=OverclaimingLLMProvider()),
    )

    response = agent.analyze(payload)

    assert response.cover_letter_status == "fallback"
    assert "Bachelor's degree" not in response.cover_letter_draft
    assert "German B2" not in response.cover_letter_draft
    assert "95%" not in response.cover_letter_draft
