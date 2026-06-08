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

## Tech stack

- Python
- FastAPI
- Pydantic
- Pytest
- Uvicorn

## Run locally

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open:

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Run tests

```bash
uv run pytest
```

## First API example

```bash
curl -X POST http://127.0.0.1:8000/applications/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "Ada Lovelace",
    "job_title": "Junior AI Backend Developer",
    "company_name": "Example GmbH",
    "cv_text": "Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, OpenAI API",
    "job_description": "We need a junior developer with Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, and LLM experience."
  }'
```

## Learning roadmap

### Sprint 1

Build the deterministic backend agent and understand every step.

### Sprint 2

Persist analyses in PostgreSQL and add job application tracking.

### Sprint 3

Add a workflow adapter with webhooks for n8n first.

### Sprint 4

Add an LLM provider interface and use it for better cover letters and reasoning.

### Sprint 5

Add RAG over CV/project documents and prepare the portfolio README.

