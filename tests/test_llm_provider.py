import json
import urllib.request
from typing import Any

import pytest

from app.domain.schemas import JobRequirementAnalysis
from app.services.llm_provider import (
    DEFAULT_GROQ_COVER_LETTER_TOKENS,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GROQ_RECOMMENDATION_TOKENS,
    DEFAULT_HTTP_USER_AGENT,
    DisabledLLMProvider,
    GroqChatCompletionsProvider,
    LLMProviderError,
    OpenAIResponsesProvider,
    create_llm_provider,
)


def test_create_llm_provider_uses_openai_by_default(monkeypatch: Any) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    provider = create_llm_provider()

    assert isinstance(provider, OpenAIResponsesProvider)


def test_create_llm_provider_uses_groq_when_selected(monkeypatch: Any) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    provider = create_llm_provider()

    assert isinstance(provider, GroqChatCompletionsProvider)
    assert not provider.is_configured


def test_create_llm_provider_disables_unknown_provider(monkeypatch: Any) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "none")

    provider = create_llm_provider()

    assert isinstance(provider, DisabledLLMProvider)
    assert not provider.is_configured


def test_groq_provider_parses_chat_completion_response(monkeypatch: Any) -> None:
    captured_payload: dict[str, Any] = {}
    captured_url = ""

    class FakeHTTPResponse:
        def __enter__(self) -> "FakeHTTPResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            recommendation_json = {
                "recommendations": [
                    {
                        "category": "project_evidence",
                        "priority": "high",
                        "title": "Add stronger backend evidence",
                        "explanation": "The role needs concrete backend project proof.",
                        "suggested_change": "Add one bullet about APIs, tests, and deployment.",
                        "example_bullet": (
                            "Built a FastAPI service with tests and deployment automation."
                        ),
                    }
                ]
            }
            response_payload = {
                "choices": [
                    {"message": {"content": json.dumps(recommendation_json)}}
                ]
            }
            return json.dumps(response_payload).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        timeout: int,
    ) -> FakeHTTPResponse:
        nonlocal captured_url
        captured_url = request.full_url
        assert request.get_header("User-agent") == DEFAULT_HTTP_USER_AGENT
        captured_payload.update(json.loads(request.data.decode("utf-8")))
        assert timeout == 30
        return FakeHTTPResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    provider = GroqChatCompletionsProvider(api_key="test-groq-key")

    recommendations = provider.generate_cv_recommendations(
        candidate_name="Ada Lovelace",
        job_title="AI Backend Developer",
        company_name="Example GmbH",
        cv_text="Python, FastAPI, Git",
        job_description="We need Python, FastAPI, Docker, tests, and LLM work.",
        matched_skills=["python", "fastapi"],
        missing_skills=["docker", "testing", "llm"],
    )

    assert captured_url == "https://api.groq.com/openai/v1/chat/completions"
    assert captured_payload["model"] == DEFAULT_GROQ_MODEL
    assert captured_payload["response_format"]["type"] == "json_schema"
    assert captured_payload["max_completion_tokens"] == DEFAULT_GROQ_RECOMMENDATION_TOKENS
    assert recommendations[0].title == "Add stronger backend evidence"


def test_groq_provider_generates_cover_letter(monkeypatch: Any) -> None:
    captured_payload: dict[str, Any] = {}

    class FakeHTTPResponse:
        def __enter__(self) -> "FakeHTTPResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            response_payload = {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Dear Example GmbH team,\n\n"
                                "I am excited to apply for the AI Backend Developer role.\n\n"
                                "Best regards,\nAda Lovelace"
                            )
                        }
                    }
                ]
            }
            return json.dumps(response_payload).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        timeout: int,
    ) -> FakeHTTPResponse:
        captured_payload.update(json.loads(request.data.decode("utf-8")))
        assert timeout == 30
        return FakeHTTPResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    provider = GroqChatCompletionsProvider(api_key="test-groq-key")

    cover_letter = provider.generate_cover_letter(
        candidate_name="Ada Lovelace",
        job_title="AI Backend Developer",
        company_name="Example GmbH",
        cv_text="Python, FastAPI, OpenAI API, and testing.",
        job_description="We need Python, FastAPI, LLM, Docker, and English.",
        matched_skills=["ai", "python", "fastapi", "llm"],
        missing_skills=["docker"],
        extra_candidate_skills=["testing"],
        requirement_analysis=JobRequirementAnalysis(
            must_have_skills=["ai", "python", "fastapi", "llm", "docker"],
            nice_to_have_skills=[],
            matched_must_have_skills=["ai", "python", "fastapi", "llm"],
            missing_must_have_skills=["docker"],
            matched_nice_to_have_skills=[],
            missing_nice_to_have_skills=[],
            language_requirements=["English"],
            location_requirements=[],
            degree_requirements=[],
            seniority="unknown",
        ),
    )

    assert "response_format" not in captured_payload
    assert captured_payload["max_completion_tokens"] == DEFAULT_GROQ_COVER_LETTER_TOKENS
    assert captured_payload["reasoning_effort"] == "low"
    assert "4-paragraph cover letter" in captured_payload["messages"][1]["content"]
    assert "Only claim a degree" in captured_payload["messages"][1]["content"]
    assert cover_letter.startswith("Dear Example GmbH team")


def test_groq_provider_rejects_truncated_cover_letter(monkeypatch: Any) -> None:
    class FakeHTTPResponse:
        def __enter__(self) -> "FakeHTTPResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            response_payload = {
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": "Dear Example GmbH team,\n\nI am"},
                    }
                ]
            }
            return json.dumps(response_payload).encode("utf-8")

    def fake_urlopen(
        request: urllib.request.Request,
        timeout: int,
    ) -> FakeHTTPResponse:
        return FakeHTTPResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    provider = GroqChatCompletionsProvider(api_key="test-groq-key")

    with pytest.raises(LLMProviderError):
        provider.generate_cover_letter(
            candidate_name="Ada Lovelace",
            job_title="AI Backend Developer",
            company_name="Example GmbH",
            cv_text="Python and FastAPI.",
            job_description="We need Python and FastAPI.",
            matched_skills=["python", "fastapi"],
            missing_skills=[],
            extra_candidate_skills=[],
            requirement_analysis=JobRequirementAnalysis(
                must_have_skills=["python", "fastapi"],
                nice_to_have_skills=[],
                matched_must_have_skills=["python", "fastapi"],
                missing_must_have_skills=[],
                matched_nice_to_have_skills=[],
                missing_nice_to_have_skills=[],
                language_requirements=[],
                location_requirements=[],
                degree_requirements=[],
                seniority="unknown",
            ),
        )
