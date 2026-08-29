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
