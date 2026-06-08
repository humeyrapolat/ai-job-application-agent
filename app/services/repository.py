import json
from typing import Any

from app.core.database import get_connection
from app.domain.schemas import AnalyzeApplicationResponse


class ApplicationRepository:
    def save_analysis(self, analysis: AnalyzeApplicationResponse) -> int:
        response_json = analysis.json()

        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO application_analyses (
                    candidate_name,
                    job_title,
                    company_name,
                    match_score,
                    seniority_signal,
                    response_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.candidate_name,
                    analysis.job_title,
                    analysis.company_name,
                    analysis.match_score,
                    analysis.seniority_signal,
                    response_json,
                ),
            )

        return int(cursor.lastrowid)

    def list_analyses(self) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    candidate_name,
                    job_title,
                    company_name,
                    match_score,
                    seniority_signal,
                    created_at
                FROM application_analyses
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def get_analysis(self, application_id: int) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    response_json,
                    created_at
                FROM application_analyses
                WHERE id = ?
                """,
                (application_id,),
            ).fetchone()

        if row is None:
            return None

        response = json.loads(row["response_json"])
        response["id"] = row["id"]
        response["created_at"] = row["created_at"]
        return response