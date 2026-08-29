from dataclasses import dataclass
from typing import Literal

from app.domain.schemas import CVRecommendation
from app.services.llm_provider import (
    LLMProviderError,
    LLMRecommendationProvider,
    create_llm_provider,
)

AIRecommendationStatus = Literal["not_requested", "generated", "unavailable"]


@dataclass(frozen=True)
class CVRecommendationResult:
    recommendations: list[CVRecommendation]
    ai_status: AIRecommendationStatus


class CVRecommendationEngine:
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
        cv_text: str,
        job_description: str,
        use_ai: bool,
    ) -> CVRecommendationResult:
        recommendations: list[CVRecommendation] = []

        if missing_skills:
            recommendations.append(
                CVRecommendation(
                    category="keyword_optimization",
                    priority="high" if match_score < 65 else "medium",
                    title="Add evidence for missing role keywords",
                    explanation=(
                        "The job description mentions skills that are not clearly supported "
                        "by the CV text."
                    ),
                    suggested_change=(
                        "Add a project or experience bullet that demonstrates: "
                        + ", ".join(missing_skills[:3])
                        + "."
                    ),
                    example_bullet=(
                        "Built a backend feature using "
                        + ", ".join(missing_skills[:3])
                        + " and documented the implementation with tests."
                    ),
                )
            )

        if matched_skills:
            recommendations.append(
                CVRecommendation(
                    category="project_evidence",
                    priority="medium",
                    title="Move the strongest matching skills closer to the top",
                    explanation=(
                        "Recruiters often scan the profile summary and first project bullets "
                        "before reading the full CV."
                    ),
                    suggested_change=(
                        "Mention the most relevant matched skills near the profile summary "
                        f"or first project for the {job_title} role."
                    ),
                    example_bullet=(
                        "Developed a backend project with "
                        + ", ".join(matched_skills[:4])
                        + ", focusing on reliable API workflows."
                    ),
                )
            )

        if not _mentions_impact(cv_text):
            recommendations.append(
                CVRecommendation(
                    category="impact_framing",
                    priority="medium",
                    title="Rewrite technical bullets with clearer impact",
                    explanation=(
                        "The CV lists technical skills, but stronger bullets should show what "
                        "was built, improved, automated, or measured."
                    ),
                    suggested_change=(
                        "Use action-and-result bullets instead of only listing technologies."
                    ),
                    example_bullet=(
                        "Implemented FastAPI endpoints with SQLite persistence and Pytest "
                        "coverage to automate job application analysis workflows."
                    ),
                )
            )

        if match_score < 65:
            recommendations.append(
                CVRecommendation(
                    category="application_decision",
                    priority="high",
                    title="Strengthen the CV before applying",
                    explanation=(
                        "The match score is below the recommended threshold for a strong "
                        "application."
                    ),
                    suggested_change=(
                        "Improve the CV around the top missing skills before sending the "
                        "application."
                    ),
                )
            )
        elif match_score >= 80:
            recommendations.append(
                CVRecommendation(
                    category="application_decision",
                    priority="low",
                    title="Tailor the summary before applying",
                    explanation=(
                        "The CV already matches many role requirements, so small wording "
                        "changes may be enough."
                    ),
                    suggested_change=(
                        "Adjust the profile summary and first project bullet to mirror the "
                        "job title and most important role keywords."
                    ),
                )
            )

        if not use_ai:
            return CVRecommendationResult(
                recommendations=recommendations,
                ai_status="not_requested",
            )

        if not self.llm_provider.is_configured:
            return CVRecommendationResult(
                recommendations=recommendations,
                ai_status="unavailable",
            )

        try:
            ai_recommendations = self.llm_provider.generate_cv_recommendations(
                candidate_name=candidate_name,
                job_title=job_title,
                company_name=company_name,
                cv_text=cv_text,
                job_description=job_description,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
            )
        except LLMProviderError:
            return CVRecommendationResult(
                recommendations=recommendations,
                ai_status="unavailable",
            )

        return CVRecommendationResult(
            recommendations=ai_recommendations or recommendations,
            ai_status="generated" if ai_recommendations else "unavailable",
        )


def _mentions_impact(text: str) -> bool:
    lowered = text.lower()
    impact_terms = (
        "improved",
        "reduced",
        "increased",
        "automated",
        "optimized",
        "measured",
        "deployed",
        "%",
    )
    return any(term in lowered for term in impact_terms)
