# AI Job Application Agent

A CV-to-job matching tool that scans a resume against a job description and returns an ATS-style compatibility report.

Live demo: https://humeyrapolat.github.io/ai-job-application-agent/

## Overview

The application helps candidates review how well a CV fits a target role before applying. It extracts text from a PDF resume, reads the job description, identifies relevant requirements, and returns a structured report with a compatibility score, matched keywords, missing keywords, CV improvement suggestions, and a cover letter draft.

The public demo runs on GitHub Pages and works without a deployed backend. PDF text extraction and the demo analysis run directly in the browser, so recruiters can try the project from the live link without any setup.

## Features

- Upload a CV as a PDF
- Paste a job description
- Extract ATS-style keywords from both documents
- Separate required skills, preferred skills, hard requirements, languages, location, and degree signals
- Calculate a weighted compatibility score
- Show matched, missing, and extra candidate skills
- Generate CV improvement recommendations
- Draft a role-specific cover letter
- Use a local FastAPI backend for API workflows and optional provider-based recommendations

## Scoring

The score is a weighted compatibility score, not a simple keyword percentage.

| Signal | Weight |
| ------ | ------ |
| Hard requirements | 20 |
| Required skills | 45 |
| Preferred skills | 15 |
| Evidence in the CV | 15 |
| Adjacent relevant skills | 5 |

The scoring model also applies confidence caps. If a job description contains only a few measurable signals, the result is capped so the application does not report a perfect match from limited evidence.

## Tech Stack

- Frontend: HTML, CSS, JavaScript, PDF.js
- Backend: Python, FastAPI, Pydantic
- Storage: SQLite
- Testing: Pytest, Ruff
- CI: GitHub Actions
- Deployment: GitHub Pages

## Architecture

```text
frontend/
  index.html
  styles.css
  app.js

app/
  api/
  core/
  domain/
  services/

tests/
  API, scoring, requirement parsing, document extraction, and provider tests
```

The frontend contains the public demo flow. The backend contains the API, document extraction endpoint, scoring service, repository layer, and optional recommendation provider integration.

## Run Locally

Install dependencies:

```bash
uv sync
```

Start the backend:

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Start the frontend:

```bash
npx vite frontend --host 127.0.0.1 --port 5173
```

Open:

- Frontend: http://127.0.0.1:5173/
- API docs: http://127.0.0.1:8001/docs

## Environment Variables

Create a local `.env` file if you want to use provider-backed recommendations through the backend.

```bash
APP_NAME="AI Job Application Agent"
APP_ENV="local"
LOG_LEVEL="INFO"
CORS_ALLOW_ORIGINS="http://127.0.0.1:5173,http://localhost:5173,https://humeyrapolat.github.io"

LLM_PROVIDER="groq"
GROQ_API_KEY="your_groq_api_key_here"
GROQ_MODEL="openai/gpt-oss-20b"
```

`.env` is ignored by git and should not be committed.

## API Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Health check |
| GET | `/skills` | List known skills |
| POST | `/documents/extract-text` | Extract text from a CV PDF |
| POST | `/applications/analyze` | Analyze a CV against a job description |
| GET | `/applications` | List saved analyses |
| GET | `/applications/{application_id}` | Retrieve one saved analysis |

## Quality Checks

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest
RUFF_CACHE_DIR=/tmp/ai-job-application-agent-ruff-cache .venv/bin/ruff check .
node --check frontend/app.js
```

## Notes

- The GitHub Pages version is designed as a public project demo.
- The local backend is available for API testing and future deployment.
- The score should be described as an ATS-style compatibility score, not as a validated hiring accuracy metric.
- Precision, recall, or F1 would require a labeled evaluation dataset.
