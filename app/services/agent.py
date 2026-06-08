from app.domain.schemas import AnalyzeApplicationRequest, AnalyzeApplicationResponse
from app.services.skills import extract_skills
from app.services.workflow import WorkflowPlanner


class JobApplicationAgent:
    def __init__(self, workflow_planner: WorkflowPlanner | None = None) -> None:
        self.workflow_planner = workflow_planner or WorkflowPlanner()

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
        seniority_signal = self._infer_seniority(payload.job_description)
        recommendations = self._build_recommendations(
            match_score=match_score,
            missing_skills=missing_skills,
            extra_candidate_skills=extra_candidate_skills,
        )
        cover_letter_draft = self._draft_cover_letter(
            candidate_name=payload.candidate_name,
            job_title=payload.job_title,
            company_name=payload.company_name,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
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
            cover_letter_draft=cover_letter_draft,
            workflow_actions=workflow_actions,
            explanation=self._explain(match_score, matched_skills, missing_skills),
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

        required_skill_score = len(matched_skills) / len(job_skills) * 80
        extra_skill_bonus = min(len(extra_candidate_skills), 4) * 3
        experience_bonus = 8 if _mentions_experience(cv_text) else 0

        return min(100, round(required_skill_score + extra_skill_bonus + experience_bonus))

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
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> str:
        strengths = ", ".join(matched_skills[:5]) if matched_skills else "backend development"
        growth_area = (
            f"I am also actively improving my knowledge of {', '.join(missing_skills[:3])}."
            if missing_skills
            else "My current skills align well with the role requirements."
        )

        return (
            f"Dear {company_name} team,\n\n"
            f"My name is {candidate_name}, and I am excited to apply for the {job_title} role. "
            f"I can contribute with hands-on experience in {strengths}. "
            f"{growth_area}\n\n"
            "I would welcome the opportunity to discuss how my backend and AI automation "
            "experience can support your team.\n\n"
            f"Best regards,\n{candidate_name}"
        )

    @staticmethod
    def _explain(match_score: int, matched_skills: list[str], missing_skills: list[str]) -> str:
        return (
            f"The score is {match_score}/100 because the CV matched "
            f"{len(matched_skills)} required skill(s) and missed {len(missing_skills)}."
        )


def _mentions_experience(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ("experience", "project", "built", "developed"))

