import re
from dataclasses import dataclass
from typing import Literal

from app.domain.schemas import JobRequirementAnalysis
from app.services.llm_provider import (
    LLMProviderError,
    LLMRecommendationProvider,
    create_llm_provider,
)

CoverLetterStatus = Literal["deterministic", "generated", "fallback"]


@dataclass(frozen=True)
class CoverLetterDraftResult:
    draft: str
    status: CoverLetterStatus


class CoverLetterEngine:
    def __init__(self, llm_provider: LLMRecommendationProvider | None = None) -> None:
        self.llm_provider = llm_provider or create_llm_provider()

    def build(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        match_score: int,
        matched_skills: list[str],
        missing_skills: list[str],
        extra_candidate_skills: list[str],
        requirement_analysis: JobRequirementAnalysis,
        cv_text: str,
        job_description: str,
        use_ai: bool,
    ) -> CoverLetterDraftResult:
        deterministic_draft = build_deterministic_cover_letter(
            candidate_name=candidate_name,
            job_title=job_title,
            company_name=company_name,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            extra_candidate_skills=extra_candidate_skills,
        )

        if not use_ai:
            return CoverLetterDraftResult(
                draft=deterministic_draft,
                status="deterministic",
            )

        if not self.llm_provider.is_configured:
            return CoverLetterDraftResult(
                draft=deterministic_draft,
                status="fallback",
            )

        try:
            ai_draft = self.llm_provider.generate_cover_letter(
                candidate_name=candidate_name,
                job_title=job_title,
                company_name=company_name,
                cv_text=cv_text,
                job_description=job_description,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                extra_candidate_skills=extra_candidate_skills,
                requirement_analysis=requirement_analysis,
            )
        except LLMProviderError:
            return CoverLetterDraftResult(
                draft=deterministic_draft,
                status="fallback",
            )

        if _has_unsupported_requirement_claims(
            draft=ai_draft,
            cv_text=cv_text,
            requirement_analysis=requirement_analysis,
        ):
            return CoverLetterDraftResult(
                draft=deterministic_draft,
                status="fallback",
            )

        return CoverLetterDraftResult(
            draft=ai_draft or deterministic_draft,
            status="generated" if ai_draft else "fallback",
        )


def build_deterministic_cover_letter(
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
        "ai": "AI",
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
        "vector database": "vector databases",
    }
    return display_names.get(skill, skill)


def _has_unsupported_requirement_claims(
    *,
    draft: str,
    cv_text: str,
    requirement_analysis: JobRequirementAnalysis,
) -> bool:
    return any(
        (
            _has_unsupported_degree_claim(draft=draft, cv_text=cv_text),
            _has_unsupported_language_claim(
                draft=draft,
                cv_text=cv_text,
                language_requirements=requirement_analysis.language_requirements,
            ),
            _has_unsupported_location_claim(
                draft=draft,
                cv_text=cv_text,
                location_requirements=requirement_analysis.location_requirements,
            ),
            _has_unsupported_metric_claim(draft=draft, cv_text=cv_text),
        )
    )


def _has_unsupported_degree_claim(*, draft: str, cv_text: str) -> bool:
    degree_terms = (
        "bachelor",
        "master",
        "degree",
        "university",
        "computer science",
        "informatics",
        "software engineering",
    )
    return any(
        _contains_term(draft, term) and not _contains_term(cv_text, term)
        for term in degree_terms
    )


def _has_unsupported_language_claim(
    *,
    draft: str,
    cv_text: str,
    language_requirements: list[str],
) -> bool:
    for requirement in language_requirements:
        for token in requirement.lower().split():
            if token in {"and", "or"}:
                continue
            if _contains_term(draft, token) and not _contains_term(cv_text, token):
                return True
    return False


def _has_unsupported_location_claim(
    *,
    draft: str,
    cv_text: str,
    location_requirements: list[str],
) -> bool:
    return any(
        _contains_term(draft, requirement) and not _contains_term(cv_text, requirement)
        for requirement in location_requirements
    )


def _has_unsupported_metric_claim(*, draft: str, cv_text: str) -> bool:
    metric_pattern = re.compile(
        r"\b\d+(?:\.\d+)?\s?(?:%|ms|s|sec|seconds|minutes|hours|rps|requests|k)\b",
        re.IGNORECASE,
    )
    return any(
        match.group(0).lower() not in cv_text.lower()
        for match in metric_pattern.finditer(draft)
    )


def _contains_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()) is not None
