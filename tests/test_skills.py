from app.services.skills import extract_skills


def test_extract_skills_detects_graph_database_and_nlp_terms() -> None:
    skills = extract_skills(
        "Experience with Neo4j graph databases, NLP, and natural language processing."
    )

    assert "neo4j" in skills
    assert "nlp" in skills


def test_extract_skills_detects_plural_rest_apis_and_ai_related_terms() -> None:
    skills = extract_skills(
        "Built REST APIs with OpenAI API, GPT workflows, and vector databases."
    )

    assert {"ai", "llm", "openai api", "rest api", "vector database"} <= skills
