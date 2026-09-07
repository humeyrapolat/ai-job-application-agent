from app.services.requirements import analyze_job_requirements


def test_analyze_job_requirements_splits_must_have_and_nice_to_have_skills() -> None:
    requirements = analyze_job_requirements(
        job_title="Junior AI Backend Developer",
        job_description=(
            "Requirements: Python, FastAPI, REST APIs, Docker, and testing. "
            "Nice to have: Neo4j, NLP, and RAG. "
            "German B2 and English fluent are required. Hybrid role in Berlin. "
            "Bachelor's degree in computer science or related field."
        ),
        cv_skills={"python", "fastapi", "rest api", "testing", "rag"},
    )

    assert requirements.seniority == "junior"
    assert requirements.must_have_skills == [
        "ai",
        "docker",
        "fastapi",
        "python",
        "rest api",
        "testing",
    ]
    assert requirements.nice_to_have_skills == ["neo4j", "nlp", "rag"]
    assert requirements.matched_must_have_skills == ["fastapi", "python", "rest api", "testing"]
    assert requirements.missing_must_have_skills == ["ai", "docker"]
    assert requirements.matched_nice_to_have_skills == ["rag"]
    assert requirements.missing_nice_to_have_skills == ["neo4j", "nlp"]
    assert "German B2" in requirements.language_requirements
    assert "English fluent" in requirements.language_requirements
    assert requirements.location_requirements == ["Berlin", "Hybrid"]
    assert "Bachelor's degree" in requirements.degree_requirements
    assert "Computer science or related field" in requirements.degree_requirements


def test_working_student_title_overrides_senior_terms_in_description() -> None:
    requirements = analyze_job_requirements(
        job_title="Working Student AI & Automation (m/f/d)",
        job_description=(
            "The role includes Python, automation, and LLM prototype work. "
            "You will present findings to senior stakeholders and support internal teams."
        ),
        cv_skills={"python", "automation", "llm"},
    )

    assert requirements.seniority == "student"


def test_analyze_job_requirements_keeps_nice_to_have_section_separate() -> None:
    requirements = analyze_job_requirements(
        job_title="Student Assistant AI Agent for Software Development",
        job_description=(
            "Must-have:\n"
            "Experience with AI tools like OpenCode, Copilot, or Claude Code.\n"
            "Good knowledge of software development with Java.\n"
            "Basic knowledge of frameworks like Spring or Jakarta.\n"
            "Basic knowledge of JUnit and Mockito.\n"
            "Basic knowledge of Git, IntelliJ, VS Code, and Gradle.\n"
            "German A2 and English B2.\n"
            "Nice-to-have:\n"
            "Knowledge of JavaScript and Python.\n"
            "Knowledge of web frameworks such as Vue.js.\n"
            "Database knowledge, for example MongoDB.\n"
            "Initial experience with AWS Cloud.\n"
            "Experience with Docker, GitHub Actions, WireMock, AssertJ, Bash, Jira, "
            "and Confluence."
        ),
        cv_skills={"ai", "git", "python", "docker", "ci/cd"},
    )

    assert requirements.seniority == "student"
    assert {
        "ai coding tools",
        "java",
        "spring",
        "junit",
        "mockito",
        "git",
        "intellij",
        "vscode",
        "gradle",
    } <= set(requirements.must_have_skills)
    assert {
        "assertj",
        "aws",
        "bash",
        "ci/cd",
        "confluence",
        "docker",
        "javascript",
        "jira",
        "mongodb",
        "python",
        "vue",
        "wiremock",
    } <= set(requirements.nice_to_have_skills)
    assert "java" not in requirements.nice_to_have_skills
    assert "aws" not in requirements.must_have_skills
