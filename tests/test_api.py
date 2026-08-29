import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.database import initialize_database


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    test_database_path = tmp_path / "test_applications.db"
    monkeypatch.setenv("DATABASE_PATH", str(test_database_path))
    initialize_database()

    from app.main import app

    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_accepts_frontend_cors_preflight(client: TestClient) -> None:
    response = client.options(
        "/applications/analyze",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_extract_document_text_endpoint(client: TestClient) -> None:
    response = client.post(
        "/documents/extract-text",
        json={
            "filename": "cv.txt",
            "content_base64": base64.b64encode(
                b"Python FastAPI backend project with Docker, tests, and REST APIs."
            ).decode("ascii"),
            "content_type": "text/plain",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "cv.txt"
    assert "Python FastAPI backend project" in body["text"]
    assert body["character_count"] == len(body["text"])


def test_analyze_application_endpoint(client: TestClient) -> None:
    response = client.post(
        "/applications/analyze",
        json={
            "candidate_name": "Ada Lovelace",
            "job_title": "Junior AI Backend Developer",
            "company_name": "Example GmbH",
            "cv_text": (
                "Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, OpenAI API, "
                "AI, and LLM projects."
            ),
            "job_description": "Looking for Python, FastAPI, PostgreSQL, Docker, Git, and LLM.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["application_id"] >= 1
    assert body["candidate_name"] == "Ada Lovelace"
    assert body["match_score"] >= 70
    assert "python" in body["matched_skills"]
    assert body["requirement_analysis"]["must_have_skills"]
    assert body["score_breakdown"]["confidence"] in {"medium", "high"}
    assert body["cv_recommendations"]
    assert body["ai_recommendation_status"] == "not_requested"
    assert body["cover_letter_status"] == "deterministic"
    assert {"category", "priority", "title", "explanation", "suggested_change"}.issubset(
        body["cv_recommendations"][0]
    )


def test_list_applications_endpoint(client: TestClient) -> None:
    create_response = client.post(
        "/applications/analyze",
        json={
            "candidate_name": "Grace Hopper",
            "job_title": "Backend Automation Developer",
            "company_name": "Example GmbH",
            "cv_text": "I built Python and FastAPI projects with Git.",
            "job_description": "Looking for Python, FastAPI, Docker, PostgreSQL, and Git.",
        },
    )
    assert create_response.status_code == 200

    response = client.get("/applications")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert any(item["candidate_name"] == "Grace Hopper" for item in body)


def test_get_application_endpoint(client: TestClient) -> None:
    create_response = client.post(
        "/applications/analyze",
        json={
            "candidate_name": "Alan Turing",
            "job_title": "AI Backend Developer",
            "company_name": "Example GmbH",
            "cv_text": "I developed Python, FastAPI, Docker and Git projects.",
            "job_description": "Looking for Python, FastAPI, Docker, Git and LLM.",
        },
    )
    application_id = create_response.json()["application_id"]

    response = client.get(f"/applications/{application_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == application_id
    assert body["candidate_name"] == "Alan Turing"


def test_get_application_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/applications/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Application analysis not found"
