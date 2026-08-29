import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

from app.domain.schemas import CVRecommendation

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com"
DEFAULT_OPENAI_MODEL = "gpt-5.6"
DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_HTTP_USER_AGENT = "ai-job-application-agent/1.0"


class LLMProviderError(Exception):
    """Raised when an LLM request cannot be completed."""


class LLMRecommendationProvider(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def generate_cv_recommendations(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        cv_text: str,
        job_description: str,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> list[CVRecommendation]: ...


class DisabledLLMProvider:
    @property
    def is_configured(self) -> bool:
        return False

    def generate_cv_recommendations(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        cv_text: str,
        job_description: str,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> list[CVRecommendation]:
        raise LLMProviderError("LLM provider is not configured")


class OpenAIResponsesProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = (
            model
            or os.getenv("OPENAI_MODEL")
            or os.getenv("LLM_MODEL", DEFAULT_OPENAI_MODEL)
        )
        self.base_url = (
            base_url or os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_cv_recommendations(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        cv_text: str,
        job_description: str,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> list[CVRecommendation]:
        if not self.api_key:
            raise LLMProviderError("OPENAI_API_KEY is not configured")

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You are a precise AI career assistant. Return concise, practical CV "
                        "recommendations that match the provided JSON schema."
                    ),
                },
                {
                    "role": "user",
                    "content": _build_cv_recommendation_prompt(
                        candidate_name=candidate_name,
                        job_title=job_title,
                        company_name=company_name,
                        cv_text=cv_text,
                        job_description=job_description,
                        matched_skills=matched_skills,
                        missing_skills=missing_skills,
                    ),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "cv_recommendation_result",
                    "strict": True,
                    "schema": _cv_recommendation_schema(),
                }
            },
        }

        request = urllib.request.Request(
            f"{self.base_url}/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": DEFAULT_HTTP_USER_AGENT,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise LLMProviderError("LLM request failed") from exc

        return _parse_recommendations_json(_extract_output_text(response_payload))


class GroqChatCompletionsProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        self.base_url = (
            base_url or os.getenv("GROQ_BASE_URL", DEFAULT_GROQ_BASE_URL)
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_cv_recommendations(
        self,
        *,
        candidate_name: str,
        job_title: str,
        company_name: str,
        cv_text: str,
        job_description: str,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> list[CVRecommendation]:
        if not self.api_key:
            raise LLMProviderError("GROQ_API_KEY is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a precise AI career assistant. Return concise, practical CV "
                        "recommendations that match the provided JSON schema."
                    ),
                },
                {
                    "role": "user",
                    "content": _build_cv_recommendation_prompt(
                        candidate_name=candidate_name,
                        job_title=job_title,
                        company_name=company_name,
                        cv_text=cv_text,
                        job_description=job_description,
                        matched_skills=matched_skills,
                        missing_skills=missing_skills,
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "cv_recommendation_result",
                    "strict": True,
                    "schema": _cv_recommendation_schema(),
                },
            },
        }

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": DEFAULT_HTTP_USER_AGENT,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise LLMProviderError("Groq request failed") from exc

        return _parse_recommendations_json(_extract_chat_message_content(response_payload))


def create_llm_provider() -> LLMRecommendationProvider:
    provider_name = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider_name == "openai":
        return OpenAIResponsesProvider()
    if provider_name == "groq":
        return GroqChatCompletionsProvider()

    return DisabledLLMProvider()


def _build_cv_recommendation_prompt(
    *,
    candidate_name: str,
    job_title: str,
    company_name: str,
    cv_text: str,
    job_description: str,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    return (
        f"Candidate: {candidate_name}\n"
        f"Target role: {job_title} at {company_name}\n"
        f"Matched skills: {', '.join(matched_skills) or 'none'}\n"
        f"Missing skills: {', '.join(missing_skills) or 'none'}\n\n"
        "CV text:\n"
        f"{cv_text}\n\n"
        "Job description:\n"
        f"{job_description}\n\n"
        "Create 1 to 3 CV recommendations. Focus on concrete CV edits, stronger project "
        "evidence, missing keywords, and impact-oriented bullet points."
    )


def _parse_recommendations_json(output_text: str) -> list[CVRecommendation]:
    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise LLMProviderError("LLM response was not valid JSON") from exc

    try:
        return [
            CVRecommendation(
                category=item["category"],
                priority=item["priority"],
                title=item["title"],
                explanation=item["explanation"],
                suggested_change=item["suggested_change"],
                example_bullet=item["example_bullet"] or None,
            )
            for item in parsed.get("recommendations", [])
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise LLMProviderError("LLM response did not match the recommendation schema") from exc


def _cv_recommendation_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "recommendations": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "keyword_optimization",
                                "project_evidence",
                                "impact_framing",
                                "application_decision",
                            ],
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "title": {"type": "string"},
                        "explanation": {"type": "string"},
                        "suggested_change": {"type": "string"},
                        "example_bullet": {"type": "string"},
                    },
                    "required": [
                        "category",
                        "priority",
                        "title",
                        "explanation",
                        "suggested_change",
                        "example_bullet",
                    ],
                },
            }
        },
        "required": ["recommendations"],
    }


def _extract_output_text(response_payload: dict[str, Any]) -> str:
    direct_output = response_payload.get("output_text")
    if isinstance(direct_output, str) and direct_output:
        return direct_output

    for output_item in response_payload.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")
            if isinstance(text, str) and text:
                return text

    raise LLMProviderError("LLM response did not contain output text")


def _extract_chat_message_content(response_payload: dict[str, Any]) -> str:
    try:
        content = response_payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("LLM chat response did not contain message content") from exc

    if isinstance(content, str) and content:
        return content

    raise LLMProviderError("LLM chat response content was empty")
