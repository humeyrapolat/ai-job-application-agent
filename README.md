# AI Job Application Agent

A backend project for learning AI agents and workflow automation without depending on Microsoft Power Automate access.

The first version is a deterministic agent:

1. It reads a CV and a job description.
2. It extracts skills using small explainable tools.
3. It calculates a match score.
4. It identifies missing skills.
5. It drafts a cover letter.
6. It returns workflow actions that can later be sent to n8n, Power Automate, Make, Zapier, or a custom worker.

## Why this project matters

Power Automate and Copilot Studio are enterprise products. If you cannot access them through school or work, you can still learn the same engineering ideas:

- triggers
- actions
- conditions
- webhooks
- approval steps
- status updates
- audit-friendly backend APIs
- agent tools

This backend is designed so the workflow layer can later be connected to Power Automate through HTTP webhooks.

## Features

- Analyze a CV against a job description.
- Extract matched, missing, and extra candidate skills.
- Calculate a deterministic match score.
- Infer job seniority signals such as junior, mid, or senior.
- Generate practical recommendations.
- Draft a cover letter template.
- Plan workflow automation actions such as status updates, email drafts, learning plans, and manual review.
- Persist analysis results in SQLite.
- List previous application analyses.
- Retrieve a stored analysis by id.

## Tech stack

- Python 3.11
- FastAPI
- Pydantic
- SQLite
- Pytest
- Uvicorn
- Ruff

## Run locally

```bash
uv sync
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Open:

- API: http://127.0.0.1:8001
- Docs: http://127.0.0.1:8001/docs

## Run tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/pytest
.venv/bin/ruff check .
```

## Configuration

By default, the app stores SQLite data at:

```text
data/applications.db
```

You can override the database path with:

```bash
DATABASE_PATH=/tmp/test_applications.db .venv/bin/pytest
```

Tests use a temporary database path so local development data is not polluted by test runs.

## API endpoints

| Method | Path                             | Description                         |
| ------ | -------------------------------- | ----------------------------------- |
| GET    | `/health`                        | Health check                        |
| GET    | `/skills`                        | List known skills                   |
| POST   | `/applications/analyze`          | Analyze and store a job application |
| GET    | `/applications`                  | List stored application analyses    |
| GET    | `/applications/{application_id}` | Retrieve one stored analysis        |

## First API example

```bash
curl -X POST http://127.0.0.1:8001/applications/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "Ada Lovelace",
    "job_title": "Junior AI Backend Developer",
    "company_name": "Example GmbH",
    "cv_text": "Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, OpenAI API",
    "job_description": "We need a junior developer with Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, and LLM experience."
  }'
```

## Roadmap

### V1 - Deterministic Agent

- CV and job description analysis
- Skill extraction
- Match scoring
- Recommendations
- Cover letter drafting
- Workflow action planning

### V2 - Persistence and Tracking

- SQLite database support
- Repository layer
- Stored application analyses
- Application list endpoint
- Application detail endpoint
- Test database isolation

### Future Improvements

- PostgreSQL and Docker Compose
- n8n webhook integration
- OpenAI or local LLM provider
- RAG over CV and portfolio documents
- GitHub Actions CI
- Authentication
