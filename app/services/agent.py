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

        if not detected_skill_count:
            score_breakdown = ScoreBreakdown(
                must_have_score=35,
                nice_to_have_score=0,
                evidence_score=5 if _mentions_experience(cv_text) else 0,
                adjacent_skill_score=0,
                score_cap=55,
                confidence="low",
            )
            return (
                score_breakdown.must_have_score + score_breakdown.evidence_score,
                score_breakdown,
            )

        must_have_score = _coverage_score(
            matched_count=len(requirement_analysis.matched_must_have_skills),
            total_count=must_have_count,
            max_score=70,
        )
        if not must_have_count and nice_to_have_count:
            must_have_score = _coverage_score(
                matched_count=len(requirement_analysis.matched_nice_to_have_skills),
                total_count=nice_to_have_count,
                max_score=55,
            )

        nice_to_have_score = (
            _coverage_score(
                matched_count=len(requirement_analysis.matched_nice_to_have_skills),
                total_count=nice_to_have_count,
                max_score=15,
            )
            if must_have_count
            else 0
        )
        evidence_score = _evidence_score(cv_text, matched_skills)
        adjacent_skill_score = min(len(extra_candidate_skills), 5) if matched_skills else 0
        score_cap = _score_cap_for_requirement_analysis(requirement_analysis)
        raw_score = (
            must_have_score
            + nice_to_have_score
            + evidence_score
            + adjacent_skill_score
        )
        final_score = min(score_cap, raw_score)

        return final_score, ScoreBreakdown(
            must_have_score=must_have_score,
            nice_to_have_score=nice_to_have_score,
            evidence_score=evidence_score,
            adjacent_skill_score=adjacent_skill_score,
            score_cap=score_cap,
            confidence=_score_confidence(detected_skill_count),
        )

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
    def _explain(
        match_score: int,
        *,
        requirement_analysis: JobRequirementAnalysis,
        score_breakdown: ScoreBreakdown,
    ) -> str:
        explanation = (
            f"The ATS compatibility score is {match_score}/100 using weighted "
            "requirement coverage: "
            f"{len(requirement_analysis.matched_must_have_skills)}/"
            f"{len(requirement_analysis.must_have_skills)} must-have skill(s) and "
            f"{len(requirement_analysis.matched_nice_to_have_skills)}/"
            f"{len(requirement_analysis.nice_to_have_skills)} nice-to-have skill(s) matched."
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


def _evidence_score(cv_text: str, matched_skills: set[str]) -> int:
    if not matched_skills:
        return 0

    score = 0
    if _mentions_experience(cv_text):
        score += 5
    if _mentions_impact(cv_text):
        score += 5
    return score


def _score_cap_for_requirement_analysis(requirement_analysis: JobRequirementAnalysis) -> int:
    skill_count = (
        len(requirement_analysis.must_have_skills)
        + len(requirement_analysis.nice_to_have_skills)
    )
    if skill_count <= 2:
        return 75
    if skill_count == 3:
        return 85
    if skill_count == 4:
        return 92
    if requirement_analysis.missing_must_have_skills:
        return 88
    return 100


def _score_confidence(detected_skill_count: int) -> str:
    if detected_skill_count <= 2:
        return "low"
    if detected_skill_count <= 4:
        return "medium"
    return "high"
