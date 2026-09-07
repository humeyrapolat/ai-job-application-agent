import re

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "ai": ("ai", "ai/ml", "artificial intelligence", "machine learning", "ml", "openai"),
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
    "rest api": (
        "rest api",
        "rest apis",
        "rest endpoint",
        "rest endpoints",
        "restful",
        "api development",
    ),
    "graphql": ("graphql",),
    "neo4j": ("neo4j", "graph database", "graph databases"),
    "git": ("git", "github", "gitlab"),
    "ci/cd": ("ci/cd", "github actions", "gitlab ci", "continuous integration"),
    "testing": ("pytest", "unit test", "unit tests", "integration test", "testing"),
    "nlp": ("nlp", "natural language processing"),
    "openai api": ("openai", "openai api", "gpt", "chatgpt"),
    "llm": (
        "llm",
        "large language model",
        "large language models",
        "language model",
        "language models",
        "openai api",
        "gpt",
        "chatgpt",
    ),
    "ai agents": (
        "agentic ai",
        "ai agent",
        "ai agents",
        "agent system",
        "agent systems",
        "agent framework",
        "agent frameworks",
    ),
    "automation": (
        "automation",
        "automating",
        "automated workflow",
        "automated workflows",
        "workflow automation",
    ),
    "ai coding tools": (
        "ai coding tool",
        "ai coding tools",
        "claude code",
        "copilot",
        "github copilot",
        "opencode",
        "open code",
    ),
    "autogen": ("autogen", "auto gen"),
    "assertj": ("assertj", "assert j"),
    "bash": ("bash", "shell script", "shell scripting"),
    "confluence": ("confluence",),
    "crewai": ("crewai", "crew ai"),
    "gradle": ("gradle",),
    "guardrails": ("guardrails", "nemo guardrails", "nemoguardrails"),
    "intellij": ("intellij", "intellij idea"),
    "java": ("java",),
    "jira": ("jira",),
    "junit": ("junit", "j unit"),
    "openclaw": ("openclaw", "open claw"),
    "mockito": ("mockito",),
    "rag": ("rag", "retrieval augmented generation", "vector search"),
    "spring": ("spring", "spring boot", "jakarta", "jakarta ee"),
    "vector database": ("vector database", "vector databases", "vector db", "embeddings"),
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
    "vscode": ("vs code", "vscode", "visual studio code"),
    "vue": ("vue", "vue.js", "vuejs"),
    "wiremock": ("wiremock", "wire mock"),
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
