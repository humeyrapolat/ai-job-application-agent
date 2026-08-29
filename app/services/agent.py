from app.domain.schemas import AnalyzeApplicationRequest, AnalyzeApplicationResponse
from app.services.recommendations import CVRecommendationEngine
from app.services.skills import extract_skills
from app.services.workflow import WorkflowPlanner


class JobApplicationAgent:
    def __init__(
        self,
        workflow_planner: WorkflowPlanner | None = None,
        recommendation_engine: CVRecommendationEngine | None = None,
    ) -> None:
        self.workflow_planner = workflow_planner or WorkflowPlanner()
        self.recommendation_engine = recommendation_engine or CVRecommendationEngine()

    def analyze(self, payload: AnalyzeApplicationRequest) -> AnalyzeApplicationResponse:
        cv_skills = extract_skills(payload.cv_text)
        job_skills = extract_skills(payload.job_description)

        matched_skills = sorted(cv_skills & job_skills)
        missing_skills = sorted(job_skills - cv_skills)
        extra_candidate_skills = sorted(cv_skills - job_skills)

        match_score = self._calculate_match_score(
            job_skills=job_skills,
            matched_skills=set(matched_skills),
            extra_candidate_skills=set(extra_candidate_skills),
            cv_text=payload.cv_text,
        )
        seniority_signal = self._infer_seniority(
            f"{payload.job_title}\n{payload.job_description}"
        )
        recommendations = self._build_recommendations(
            match_score=match_score,
            missing_skills=missing_skills,
            extra_candidate_skills=extra_candidate_skills,
        )
        cv_recommendation_result = self.recommendation_engine.build(
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            company_name=payload.company_name,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            cv_text=payload.cv_text,
            job_description=payload.job_description,
            use_ai=payload.use_ai_recommendations,
        )
        cover_letter_draft = self._draft_cover_letter(
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            company_name=payload.company_name,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            extra_candidate_skills=extra_candidate_skills,
        )

        workflow_actions = self.workflow_planner.plan(
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            company_name=payload.company_name,
            match_score=match_score,
            missing_skills=missing_skills,
            cover_letter_draft=cover_letter_draft,
        )

        return AnalyzeApplicationResponse(
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            company_name=payload.company_name,
            match_score=match_score,
            seniority_signal=seniority_signal,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            extra_candidate_skills=extra_candidate_skills,
            recommendations=recommendations,
            cv_recommendations=cv_recommendation_result.recommendations,
            ai_recommendation_status=cv_recommendation_result.ai_status,
            cover_letter_draft=cover_letter_draft,
            workflow_actions=workflow_actions,
            explanation=self._explain(
                match_score,
                matched_skills,
                missing_skills,
                detected_job_skill_count=len(job_skills),
            ),
        )

    @staticmethod
    def _calculate_match_score(
        *,
        job_skills: set[str],
        matched_skills: set[str],
        extra_candidate_skills: set[str],
        cv_text: str,
    ) -> int:
        if not job_skills:
            return 50

        required_skill_score = len(matched_skills) / len(job_skills) * 85
        extra_skill_bonus = min(len(extra_candidate_skills), 3) * 2
        experience_bonus = 5 if _mentions_experience(cv_text) else 0
        evidence_cap = _score_cap_for_detected_skills(job_skills)

        return min(
            evidence_cap,
            round(required_skill_score + extra_skill_bonus + experience_bonus),
        )

    @staticmethod
    def _infer_seniority(job_description: str) -> str:
        lowered = job_description.lower()
        if any(term in lowered for term in ("senior", "lead", "principal", "staff")):
            return "senior"
        if any(term in lowered for term in ("junior", "entry level", "graduate", "intern")):
            return "junior"
        if any(term in lowered for term in ("mid", "professional", "2+ years", "3+ years")):
            return "mid"
        return "unknown"

    @staticmethod
    def _build_recommendations(
        *,
        match_score: int,
        missing_skills: list[str],
        extra_candidate_skills: list[str],
    ) -> list[str]:
        recommendations: list[str] = []

        if match_score >= 80:
            recommendations.append("Apply after tailoring the CV summary to this role.")
        elif match_score >= 65:
            recommendations.append("Apply, but improve the CV bullets around the missing skills.")
        else:
            recommendations.append("Consider learning the top missing skills before applying.")

        if missing_skills:
            recommendations.append(
                "Add project evidence for: " + ", ".join(missing_skills[:3]) + "."
            )

        if extra_candidate_skills:
            recommendations.append(
                "Mention related strengths if relevant: "
                + ", ".join(extra_candidate_skills[:3])
                + "."
            )

        return recommendations

    @staticmethod
    def _draft_cover_letter(
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        match_score: int,
        matched_skills: list[str],
        missing_skills: list[str],
        extra_candidate_skills: list[str],
    ) -> str:
        strengths = _format_human_skill_list(matched_skills[:5]) or "backend development"
        role_focus = _build_role_focus(job_title, matched_skills, missing_skills)
        adjacent_strengths = _format_human_skill_list(extra_candidate_skills[:4])
        readiness_sentence = _build_readiness_sentence(
            match_score=match_score,
            missing_skills=missing_skills,
        )
        adjacent_sentence = (
            f" I can also bring adjacent experience in {adjacent_strengths}, where relevant."
            if adjacent_strengths
            else ""
        )

        return (
            f"Dear {company_name} team,\n\n"
            f"I am applying for the {job_title} role because it aligns with my interest in "
            f"{role_focus}.\n\n"
            f"My recent work includes hands-on project experience with {strengths}. This "
            "background would help me contribute to practical implementation, clear API "
            f"workflows, and reliable delivery for {company_name}.{adjacent_sentence}\n\n"
            f"{readiness_sentence}\n\n"
            f"Thank you for considering my application. I would be glad to discuss how my "
            f"backend and AI automation experience can support the {company_name} team.\n\n"
            f"Best regards,\n{candidate_name}"
        )

    @staticmethod
    def _explain(
        match_score: int,
        matched_skills: list[str],
        missing_skills: list[str],
        *,
        detected_job_skill_count: int,
    ) -> str:
        explanation = (
            f"The score is {match_score}/100 because the CV matched "
            f"{len(matched_skills)} required skill(s) and missed {len(missing_skills)}."
        )

        if detected_job_skill_count <= 2:
            explanation += (
                f" Only {detected_job_skill_count} role skill(s) were detected, so the score "
                "is capped instead of treated as a perfect fit."
            )

        return explanation


def _mentions_experience(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ("experience", "project", "built", "developed"))


def _build_role_focus(
    job_title: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    role_terms = matched_skills[:3] + missing_skills[:2]
    if role_terms:
        return _format_human_skill_list(role_terms)

    return job_title.lower()


def _build_readiness_sentence(*, match_score: int, missing_skills: list[str]) -> str:
    if missing_skills:
        missing_skill_list = _format_human_skill_list(missing_skills[:3])
        return (
            f"Where the role asks for {missing_skill_list}, I am actively strengthening those "
            "areas through focused project work and would connect that learning to the role's "
            "delivery needs."
        )

    if match_score >= 80:
        return (
            "Because the core requirements are well aligned with my current profile, I would "
            "focus on tailoring the first project bullets to the role's priorities."
        )

    return (
        "Although the match is not perfect, the overlap gives me a clear starting point to "
        "contribute while continuing to deepen the role-specific skills."
    )


def _format_human_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _format_human_skill_list(skills: list[str]) -> str:
    return _format_human_list([_format_skill_label(skill) for skill in skills])


def _format_skill_label(skill: str) -> str:
    display_names = {
        "aws": "AWS",
        "azure": "Azure",
        "ci/cd": "CI/CD",
        "docker": "Docker",
        "fastapi": "FastAPI",
        "git": "Git",
        "graphql": "GraphQL",
        "javascript": "JavaScript",
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "llm": "LLM",
        "mongodb": "MongoDB",
        "mysql": "MySQL",
        "neo4j": "Neo4j",
        "nlp": "NLP",
        "openai api": "OpenAI API",
        "postgresql": "PostgreSQL",
        "python": "Python",
        "rag": "RAG",
        "react": "React",
        "redis": "Redis",
        "rest api": "REST APIs",
        "sqlite": "SQLite",
        "typescript": "TypeScript",
    }
    return display_names.get(skill, skill)


def _score_cap_for_detected_skills(job_skills: set[str]) -> int:
    skill_count = len(job_skills)
    if skill_count <= 2:
        return 75
    if skill_count == 3:
        return 85
    if skill_count == 4:
        return 92
    return 100
