# AI Job Application Agent

An AI-assisted ATS compatibility demo that compares a CV with a job description, highlights matched and missing role signals, and produces CV improvement recommendations plus a cover letter draft.

Live demo: https://humeyrapolat.github.io/ai-job-application-agent/

The project is built as a portfolio-ready product demo:

- GitHub Pages hosts a static recruiter-facing frontend.
- The frontend can run a browser-based demo analysis without a deployed backend.
- A FastAPI backend is included for local API usage, PDF text extraction, persistence, and optional LLM calls.
- Groq/OpenAI integration is backend-only so API keys are never exposed in the browser.

## What It Does

- Upload a CV PDF.
- Paste a job description.
- Extract ATS-style skills and role signals.
- Calculate a recruiter-weighted compatibility score.
- Show matched skills, missing skills, extra candidate strengths, and score confidence.
- Separate hard requirements from technical and preferred skills.
- Generate CV recommendations.
- Draft a cover letter.
- Provide workflow actions for an application tracker or automation tool.

## Demo Mode

The GitHub Pages version is designed to work even when the backend is not deployed.

When the API is unavailable, the frontend switches to demo mode:

- PDF text is extracted in the browser using PDF.js.
- CV and job text are analyzed locally in JavaScript.
- No API key is required.
- No CV data is sent to a server in demo mode.
- The result is clearly marked as a demo result.

This keeps the public portfolio link usable for recruiters without asking them to run terminal commands.

## Scoring Model

The score is not a generic keyword percentage. It is a weighted compatibility score:

| Signal | Weight | Purpose |
| ------ | ------ | ------- |
| Hard requirements | 20 | Language, degree, location, or similar gatekeeping requirements |
| Required skills | 45 | Core technical requirements from the role |
| Preferred skills | 15 | Nice-to-have skills |
| Evidence | 15 | Project, implementation, automation, or impact evidence in the CV |
| Adjacent strengths | 5 | Relevant extra skills that support the role |

The model also applies a confidence cap. If the job description exposes only a small number of measurable signals, the score is capped so a thin match is not presented as a perfect fit.

## Current Limitations

- This is a compatibility assistant, not a validated hiring model.
- The public demo uses deterministic browser logic when no backend is available.
- Live LLM-generated recommendations require running the backend with a Groq or OpenAI API key.
- Accuracy, precision, recall, and F1 should only be claimed after building a labeled evaluation set of job descriptions and expected extracted requirements.

## Tech Stack

- Frontend: HTML, CSS, vanilla JavaScript, PDF.js
- Backend: Python 3.11, FastAPI, Pydantic
- Storage: SQLite
- AI provider layer: Groq-compatible Chat Completions and OpenAI Responses support
- Quality: Pytest, Ruff, GitHub Actions, Docker
- Hosting: GitHub Pages for the frontend

## Architecture

```text
GitHub Pages Frontend
  - CV PDF upload
  - Browser demo analysis
  - ATS results UI
  - Optional connection to FastAPI backend

FastAPI Backend
  - /documents/extract-text
  - /applications/analyze
  - /applications
  - /applications/{application_id}
  - SQLite repository
  - Optional Groq/OpenAI provider
```

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

## Optional LLM Setup

Create a local `.env` file from `.env.example` and add one provider key:

```bash
LLM_PROVIDER="groq"
GROQ_API_KEY="your_groq_api_key_here"
GROQ_MODEL="openai/gpt-oss-20b"
```

or:

```bash
LLM_PROVIDER="openai"
OPENAI_API_KEY="your_openai_api_key_here"
OPENAI_MODEL="gpt-5.6-luna"
```

Never commit real API keys. `.env` is ignored by git.

## API Endpoints

| Method | Path                             | Description                         |
| ------ | -------------------------------- | ----------------------------------- |
| GET    | `/health`                        | Health check                        |
| GET    | `/skills`                        | List known skills                   |
| POST   | `/documents/extract-text`        | Extract readable text from a CV     |
| POST   | `/applications/analyze`          | Analyze and store a job application |
| GET    | `/applications`                  | List stored application analyses    |
| GET    | `/applications/{application_id}` | Retrieve one stored analysis        |

## Test And Lint

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest
RUFF_CACHE_DIR=/tmp/ai-job-application-agent-ruff-cache .venv/bin/ruff check .
node --check frontend/app.js
```

## Deployment

The frontend is deployed to GitHub Pages from the `frontend/` directory.

The backend does not need to be deployed for the public demo to work. A Render blueprint is included in `render.yaml` for a future production backend deployment.

## Project Status

Finished portfolio demo version:

- Static GitHub Pages demo works without backend deployment.
- Local FastAPI backend remains available for real API usage.
- Optional Groq/OpenAI calls are supported through the backend.
- Recruiter-facing flow avoids technical API setup.
