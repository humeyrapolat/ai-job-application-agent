import json
import urllib.request
from typing import Any

from app.services.llm_provider import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_HTTP_USER_AGENT,
    DisabledLLMProvider,
    GroqChatCompletionsProvider,
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
    assert recommendations[0].title == "Add stronger backend evidence"
