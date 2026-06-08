import re

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "python": ("python", "py"),
    "fastapi": ("fastapi", "fast api"),
    "django": ("django",),
    "flask": ("flask",),
    "postgresql": ("postgresql", "postgres", "psql"),
    "mysql": ("mysql",),
    "sqlite": ("sqlite",),
    "mongodb": ("mongodb", "mongo"),
    "redis": ("redis",),
    "docker": ("docker", "container", "containers"),
    "kubernetes": ("kubernetes", "k8s"),
    "rest api": ("rest api", "restful", "api development"),
    "graphql": ("graphql",),
    "git": ("git", "github", "gitlab"),
    "ci/cd": ("ci/cd", "github actions", "gitlab ci", "continuous integration"),
    "testing": ("pytest", "unit test", "unit tests", "integration test", "testing"),
    "openai api": ("openai", "openai api", "gpt", "chatgpt"),
    "llm": ("llm", "large language model", "language model"),
    "rag": ("rag", "retrieval augmented generation", "vector search"),
    "langchain": ("langchain",),
    "langgraph": ("langgraph",),
    "n8n": ("n8n",),
    "power automate": ("power automate",),
    "azure": ("azure", "microsoft azure"),
    "aws": ("aws", "amazon web services"),
    "linux": ("linux",),
    "javascript": ("javascript", "js"),
    "typescript": ("typescript", "ts"),
    "react": ("react", "reactjs"),
}

KNOWN_SKILLS = tuple(SKILL_ALIASES.keys())


def extract_skills(text: str) -> set[str]:
    normalized = _normalize(text)
    found: set[str] = set()

    for skill, aliases in SKILL_ALIASES.items():
        if any(_contains_alias(normalized, alias) for alias in aliases):
            found.add(skill)

    return found


def _normalize(text: str) -> str:
    lowered = text.lower()
    return re.sub(r"[^a-z0-9+#./ -]+", " ", lowered)


def _contains_alias(text: str, alias: str) -> bool:
    escaped = re.escape(alias.lower())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None

