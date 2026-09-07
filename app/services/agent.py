import re

from app.domain.schemas import (
    AnalyzeApplicationRequest,
    AnalyzeApplicationResponse,
    JobRequirementAnalysis,
    ScoreBreakdown,
)
from app.services.cover_letter import CoverLetterEngine
from app.services.recommendations import CVRecommendationEngine
from app.services.requirements import analyze_job_requirements
from app.services.skills import extract_skills
from app.services.workflow import WorkflowPlanner


class JobApplicationAgent:
    def __init__(
        self,
        workflow_planner: WorkflowPlanner | None = None,
        recommendation_engine: CVRecommendationEngine | None = None,
        cover_letter_engine: CoverLetterEngine | None = None,
    ) -> None:
        self.workflow_planner = workflow_planner or WorkflowPlanner()
        self.recommendation_engine = recommendation_engine or CVRecommendationEngine()
        self.cover_letter_engine = cover_letter_engine or CoverLetterEngine()

    def analyze(self, payload: AnalyzeApplicationRequest) -> AnalyzeApplicationResponse:
        cv_skills = extract_skills(payload.cv_text)
        job_text = f"{payload.job_title}\n{payload.job_description}"
        job_skills = extract_skills(job_text)
        requirement_analysis = analyze_job_requirements(
            job_title=payload.job_title,
            job_description=payload.job_description,
            cv_skills=cv_skills,
        )

        matched_skills = sorted(cv_skills & job_skills)
        missing_skills = sorted(job_skills - cv_skills)
        extra_candidate_skills = sorted(cv_skills - job_skills)

        match_score, score_breakdown = self._calculate_match_score(
            requirement_analysis=requirement_analysis,
            matched_skills=set(matched_skills),
            extra_candidate_skills=set(extra_candidate_skills),
            cv_text=payload.cv_text,
        )
        seniority_signal = requirement_analysis.seniority
        recommendations = self._build_recommendations(
            match_score=match_score,
            missing_skills=missing_skills,
            extra_candidate_skills=extra_candidate_skills,
            requirement_analysis=requirement_analysis,
            score_breakdown=score_breakdown,
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
        cover_letter_result = self.cover_letter_engine.build(
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            company_name=payload.company_name,
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            extra_candidate_skills=extra_candidate_skills,
            requirement_analysis=requirement_analysis,
            cv_text=payload.cv_text,
            job_description=payload.job_description,
            use_ai=payload.use_ai_recommendations,
        )

        workflow_actions = self.workflow_planner.plan(
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            company_name=payload.company_name,
            match_score=match_score,
            missing_skills=missing_skills,
            cover_letter_draft=cover_letter_result.draft,
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
            requirement_analysis=requirement_analysis,
            score_breakdown=score_breakdown,
            recommendations=recommendations,
            cv_recommendations=cv_recommendation_result.recommendations,
            ai_recommendation_status=cv_recommendation_result.ai_status,
            cover_letter_draft=cover_letter_result.draft,
            cover_letter_status=cover_letter_result.status,
            workflow_actions=workflow_actions,
            explanation=self._explain(
                match_score,
                requirement_analysis=requirement_analysis,
                score_breakdown=score_breakdown,
            ),
        )

    @staticmethod
    def _calculate_match_score(
        *,
        requirement_analysis: JobRequirementAnalysis,
        matched_skills: set[str],
        extra_candidate_skills: set[str],
        cv_text: str,
    ) -> tuple[int, ScoreBreakdown]:
        must_have_count = len(requirement_analysis.must_have_skills)
        nice_to_have_count = len(requirement_analysis.nice_to_have_skills)
        detected_skill_count = must_have_count + nice_to_have_count
        confidence = _score_confidence(
            detected_skill_count=detected_skill_count,
            hard_requirement_count=_hard_requirement_count(requirement_analysis),
        )

        if not detected_skill_count:
            hard_requirement_score = _hard_requirement_score(
                requirement_analysis=requirement_analysis,
                cv_text=cv_text,
            )
            evidence_score = _evidence_score(cv_text, matched_skills)
            score_breakdown = ScoreBreakdown(
                hard_requirement_score=hard_requirement_score,
                technical_score=0,
                preferred_score=0,
                evidence_score=evidence_score,
                adjacent_skill_score=0,
                score_cap=_score_cap_for_requirement_analysis(
                    requirement_analysis=requirement_analysis,
                    hard_requirement_score=hard_requirement_score,
                    confidence=confidence,
                ),
                confidence=confidence,
            )
            return (
                min(
                    score_breakdown.score_cap,
                    score_breakdown.hard_requirement_score
                    + score_breakdown.evidence_score,
                ),
                score_breakdown,
            )

        hard_requirement_score = _hard_requirement_score(
            requirement_analysis=requirement_analysis,
            cv_text=cv_text,
        )
        technical_score = _technical_score(requirement_analysis)
        preferred_score = _preferred_score(requirement_analysis)
        evidence_score = _evidence_score(cv_text, matched_skills)
        adjacent_skill_score = _adjacent_skill_score(
            requirement_analysis=requirement_analysis,
            extra_candidate_skills=extra_candidate_skills,
        )
        score_cap = _score_cap_for_requirement_analysis(
            requirement_analysis=requirement_analysis,
            hard_requirement_score=hard_requirement_score,
            confidence=confidence,
        )
        raw_score = (
            hard_requirement_score
            + technical_score
            + preferred_score
            + evidence_score
            + adjacent_skill_score
        )
        final_score = min(score_cap, raw_score)

        return final_score, ScoreBreakdown(
            hard_requirement_score=hard_requirement_score,
            technical_score=technical_score,
            preferred_score=preferred_score,
            evidence_score=evidence_score,
            adjacent_skill_score=adjacent_skill_score,
            score_cap=score_cap,
            confidence=confidence,
        )

    @staticmethod
    def _build_recommendations(
        *,
        match_score: int,
        missing_skills: list[str],
        extra_candidate_skills: list[str],
        requirement_analysis: JobRequirementAnalysis,
        score_breakdown: ScoreBreakdown,
    ) -> list[str]:
        recommendations: list[str] = []

        if match_score >= 80:
            recommendations.append("Apply after tailoring the CV summary to this role.")
        elif match_score >= 65:
            recommendations.append("Apply, but improve the CV bullets around the missing skills.")
        else:
            recommendations.append("Consider learning the top missing skills before applying.")

        if score_breakdown.hard_requirement_score < 20:
            recommendations.append(
                "Verify hard requirements such as language, degree, location, or seniority "
                "before applying."
            )

        if missing_skills:
            recommendations.append(
                "Add project evidence for: " + ", ".join(missing_skills[:3]) + "."
            )

        if score_breakdown.confidence == "low":
            recommendations.append(
                "Treat this score as directional because the job description exposed only a "
                "small number of measurable requirements."
            )

        if requirement_analysis.missing_must_have_skills:
            recommendations.append(
                "Prioritize must-have gaps first: "
                + ", ".join(requirement_analysis.missing_must_have_skills[:3])
                + "."
            )

        if extra_candidate_skills:
            recommendations.append(
                "Mention related strengths if relevant: "
                + ", ".join(extra_candidate_skills[:3])
                + "."
            )

        return recommendations

    @staticmethod
    def _explain(
        match_score: int,
        *,
        requirement_analysis: JobRequirementAnalysis,
        score_breakdown: ScoreBreakdown,
    ) -> str:
        explanation = (
            f"The ATS compatibility score is {match_score}/100 using recruiter-weighted "
            "signals: hard requirements, required technical skills, preferred skills, "
            "CV evidence, and adjacent strengths. Required technical coverage is "
            f"{len(requirement_analysis.matched_must_have_skills)}/"
            f"{len(requirement_analysis.must_have_skills)} and preferred coverage is "
            f"{len(requirement_analysis.matched_nice_to_have_skills)}/"
            f"{len(requirement_analysis.nice_to_have_skills)}."
        )

        if score_breakdown.score_cap < 100:
            explanation += (
                f" Confidence is {score_breakdown.confidence}, so the score is capped at "
                f"{score_breakdown.score_cap} instead of treated as a perfect fit."
            )

        return explanation


def _mentions_experience(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ("experience", "project", "built", "developed"))


def _mentions_impact(text: str) -> bool:
    lowered = text.lower()
    return any(
        term in lowered
        for term in (
            "improved",
            "reduced",
            "increased",
            "automated",
            "optimized",
            "measured",
            "deployed",
            "%",
        )
    )


def _coverage_score(*, matched_count: int, total_count: int, max_score: int) -> int:
    if total_count == 0:
        return 0
    return round(matched_count / total_count * max_score)


def _hard_requirement_score(
    *,
    requirement_analysis: JobRequirementAnalysis,
    cv_text: str,
) -> int:
    checks = _hard_requirement_checks(requirement_analysis, cv_text)
    if not checks:
        return 20

    return _coverage_score(
        matched_count=sum(checks),
        total_count=len(checks),
        max_score=20,
    )


def _hard_requirement_checks(
    requirement_analysis: JobRequirementAnalysis,
    cv_text: str,
) -> list[bool]:
    checks: list[bool] = []

    checks.extend(
        _matches_language_requirement(requirement, cv_text)
        for requirement in requirement_analysis.language_requirements
    )
    checks.extend(
        _matches_location_requirement(requirement, cv_text)
        for requirement in requirement_analysis.location_requirements
    )
    checks.extend(
        _matches_degree_requirement(requirement, cv_text)
        for requirement in requirement_analysis.degree_requirements
    )

    return checks


def _hard_requirement_count(requirement_analysis: JobRequirementAnalysis) -> int:
    return (
        len(requirement_analysis.language_requirements)
        + len(requirement_analysis.location_requirements)
        + len(requirement_analysis.degree_requirements)
    )


def _matches_language_requirement(requirement: str, cv_text: str) -> bool:
    requirement_parts = requirement.lower().split()
    if not requirement_parts:
        return False

    language = requirement_parts[0]
    if not _contains_term(cv_text, language):
        return False

    required_level = next(
        (part for part in requirement_parts[1:] if part in LANGUAGE_LEVEL_ORDER),
        "",
    )
    if not required_level:
        return True

    cv_level = _find_language_level(cv_text, language)
    return bool(cv_level) and LANGUAGE_LEVEL_ORDER[cv_level] >= LANGUAGE_LEVEL_ORDER[required_level]


def _find_language_level(text: str, language: str) -> str:
    language_match = re.search(
        rf"(?<![a-z0-9]){re.escape(language)}(?![a-z0-9]).{{0,32}}",
        text,
        flags=re.IGNORECASE,
    )
    if not language_match:
        return ""

    level_match = re.search(
        r"\b(a1|a2|b1|b2|c1|c2|native|fluent|professional)\b",
        language_match.group(0),
        flags=re.IGNORECASE,
    )
    if not level_match:
        return ""

    return _normalize_language_level(level_match.group(1))


def _normalize_language_level(level: str) -> str:
    normalized = level.lower()
    if normalized == "native":
        return "c2"
    if normalized in {"fluent", "professional"}:
        return "c1"
    return normalized


def _matches_location_requirement(requirement: str, cv_text: str) -> bool:
    lowered_requirement = requirement.lower()
    lowered_cv = cv_text.lower()

    if lowered_requirement in {"remote", "hybrid", "on-site"}:
        return True

    return _contains_term(lowered_cv, lowered_requirement)


def _matches_degree_requirement(requirement: str, cv_text: str) -> bool:
    lowered_requirement = requirement.lower()
    lowered_cv = cv_text.lower()

    if "bachelor" in lowered_requirement:
        return any(term in lowered_cv for term in ("bachelor", "master", "degree"))
    if "master" in lowered_requirement:
        return "master" in lowered_cv
    if "computer science" in lowered_requirement:
        return any(
            term in lowered_cv
            for term in (
                "computer science",
                "informatics",
                "software engineering",
                "data science",
                "artificial intelligence",
            )
        )
    if "degree" in lowered_requirement:
        return any(term in lowered_cv for term in ("bachelor", "master", "degree", "university"))

    return _contains_term(lowered_cv, lowered_requirement)


def _technical_score(requirement_analysis: JobRequirementAnalysis) -> int:
    must_have_count = len(requirement_analysis.must_have_skills)
    if not must_have_count:
        return _coverage_score(
            matched_count=len(requirement_analysis.matched_nice_to_have_skills),
            total_count=len(requirement_analysis.nice_to_have_skills),
            max_score=28,
        )

    return _coverage_score(
        matched_count=len(requirement_analysis.matched_must_have_skills),
        total_count=must_have_count,
        max_score=_technical_score_ceiling(must_have_count),
    )


def _technical_score_ceiling(must_have_count: int) -> int:
    if must_have_count <= 2:
        return 28
    if must_have_count == 3:
        return 36
    return 45


def _preferred_score(requirement_analysis: JobRequirementAnalysis) -> int:
    nice_to_have_count = len(requirement_analysis.nice_to_have_skills)
    if not nice_to_have_count:
        return 15

    return _coverage_score(
        matched_count=len(requirement_analysis.matched_nice_to_have_skills),
        total_count=nice_to_have_count,
        max_score=15,
    )


def _adjacent_skill_score(
    *,
    requirement_analysis: JobRequirementAnalysis,
    extra_candidate_skills: set[str],
) -> int:
    if not requirement_analysis.matched_must_have_skills:
        return 0

    max_adjacent_score = 5
    if len(requirement_analysis.must_have_skills) <= 2:
        max_adjacent_score = 3
    if requirement_analysis.missing_must_have_skills:
        max_adjacent_score = 2

    return min(len(extra_candidate_skills), max_adjacent_score)


def _evidence_score(cv_text: str, matched_skills: set[str]) -> int:
    if not matched_skills:
        return 0

    score = 0
    if _mentions_experience(cv_text):
        score += 5
    if _mentions_impact(cv_text):
        score += 5
    if len(matched_skills) >= 3:
        score += 5
    elif matched_skills:
        score += 2
    return score


def _score_cap_for_requirement_analysis(
    *,
    requirement_analysis: JobRequirementAnalysis,
    hard_requirement_score: int,
    confidence: str,
) -> int:
    skill_count = (
        len(requirement_analysis.must_have_skills)
        + len(requirement_analysis.nice_to_have_skills)
    )
    caps = [100]

    if skill_count == 0:
        caps.append(50)
    elif _has_only_generic_role_signals(requirement_analysis):
        caps.append(55)
    elif confidence == "low":
        caps.append(72)
    elif confidence == "medium":
        caps.append(92 if skill_count <= 4 else 95)

    if hard_requirement_score < 20:
        caps.append(78)

    if requirement_analysis.missing_must_have_skills:
        caps.append(82)

    return min(caps)


def _has_only_generic_role_signals(requirement_analysis: JobRequirementAnalysis) -> bool:
    role_signals = set(requirement_analysis.must_have_skills) | set(
        requirement_analysis.nice_to_have_skills
    )
    generic_signals = {"ai", "automation"}
    return bool(role_signals) and role_signals <= generic_signals


LANGUAGE_LEVEL_ORDER = {
    "a1": 1,
    "a2": 2,
    "b1": 3,
    "b2": 4,
    "c1": 5,
    "c2": 6,
    "professional": 5,
    "fluent": 5,
    "native": 6,
}


def _score_confidence(
    *,
    detected_skill_count: int,
    hard_requirement_count: int,
) -> str:
    measurable_signal_count = detected_skill_count + hard_requirement_count
    if measurable_signal_count <= 2:
        return "low"
    if measurable_signal_count <= 5:
        return "medium"
    return "high"


def _contains_term(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()) is not None
