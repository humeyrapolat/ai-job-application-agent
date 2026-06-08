from app.domain.schemas import WorkflowAction


class WorkflowPlanner:
    def plan(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        match_score: int,
        missing_skills: list[str],
        cover_letter_draft: str,
    ) -> list[WorkflowAction]:
        actions = [
            WorkflowAction(
                kind="status_update",
                title="Create application tracker entry",
                description="Store this analysis result in the application tracking board.",
                payload={
                    "candidate_name": candidate_name,
                    "job_title": job_title,
                    "company_name": company_name,
                    "status": self._suggest_status(match_score),
                },
            ),
            WorkflowAction(
                kind="email_draft",
                title="Prepare cover letter email",
                description="Create a draft email that the candidate can review before sending.",
                payload={
                    "subject": f"Application for {job_title}",
                    "body": cover_letter_draft,
                },
            ),
        ]

        if missing_skills:
            actions.append(
                WorkflowAction(
                    kind="learning_plan",
                    title="Create learning plan",
                    description="Turn missing skills into a focused study checklist.",
                    payload={"skills": ", ".join(missing_skills[:5])},
                )
            )

        if match_score < 65:
            actions.append(
                WorkflowAction(
                    kind="manual_review",
                    title="Review before applying",
                    description="The match score is low, so a human review is recommended.",
                    payload={"reason": "match_score_below_threshold"},
                )
            )

        return actions

    @staticmethod
    def _suggest_status(match_score: int) -> str:
        if match_score >= 80:
            return "ready_to_apply"
        if match_score >= 65:
            return "needs_small_edits"
        return "needs_review"

