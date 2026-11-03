# AGENTS.md

Guidance for AI coding agents (and humans) working in this repository.
The product vision and requirements (in Polish) are in `README.md`; run instructions are in
`HOWTORUN.md`.

## Project in one paragraph

Testownik AI turns study materials (PDF, DOCX, PPTX, TXT, MD, pasted text) into a quiz
database in the **Testownik format** (ZIP of `001.txt`, `002.txt`, …). A React frontend talks
to a Django REST API only through HTTP; the AI module generates single- and multiple-choice
questions with an LLM (Ollama by default). Stage 1 has **no user accounts** and keeps uploaded
documents only for the duration of a job.

## Layout

```
frontend/                React 19 + TypeScript + Vite
  src/api/client.ts      All HTTP calls – the only place that knows URLs
  src/api/types.ts       TS mirror of the backend serializers
  src/components/        UI components
backend/                 Django + DRF
  config/                settings (env-driven), root urls
  apps/generation/       REST API: serializers, views, urls, in-memory job store
  ai_engine/             AI module, framework-independent
    extraction.py        document → text (TODO: PDF/DOCX/PPTX/OCR)
    generator.py         QuestionGenerator protocol, Mock + Ollama (TODO) providers
    testownik.py         Testownik ZIP export (implemented)
  tests/                 pytest tests
docker-compose.yml       optional PostgreSQL + Ollama
```

## API (v1, base `/api/v1`)

| Method | Path                                           | Purpose                              |
| ------ | ---------------------------------------------- | ------------------------------------ |
| GET    | `/health/`                                     | Liveness                             |
| GET    | `/config/`                                     | Limits, formats, languages           |
| POST   | `/jobs/` (multipart: `files[]`, `text`, `language`, `question_count`) | Start generation |
| GET    | `/jobs/{id}/`                                  | Status, progress, questions          |
| DELETE | `/jobs/{id}/`                                  | End session, discard documents       |
| DELETE | `/jobs/{id}/questions/{qid}/`                  | Remove a question                    |
| POST   | `/jobs/{id}/questions/{qid}/regenerate/`       | Regenerate one question              |
| GET    | `/jobs/{id}/export/`                           | Download Testownik ZIP (409 if not done) |

Live docs: `/api/docs/` (Swagger), schema: `/api/schema/`.

**What is mocked:** the job store is in memory (`apps/generation/store.py`), progress is
simulated from elapsed time, the generator returns fake questions, and binary document
extraction returns a placeholder. Request validation and the Testownik export are real.

## Commands

Backend (in `backend/`, virtualenv active):

- `pytest` – tests
- `ruff check .` and `ruff format .` – lint / format
- `python manage.py runserver` – dev server on :8000

Frontend (in `frontend/`):

- `npm test` – Vitest
- `npm run lint` – oxlint; `npm run format` – Prettier
- `npm run build` – type-check + build
- `npm run dev` – dev server on :5173 (proxies `/api` to :8000)

Run the relevant lint + tests before finishing a change; CI runs all of them.

## Conventions

- **API contract changes** go in three places together: the DRF serializer, the view's
  `@extend_schema`, and `frontend/src/api/types.ts`. Add/adjust a test in `backend/tests/`.
- Keep `ai_engine/` free of DRF/HTTP code. New AI providers implement `QuestionGenerator` and
  are selected in `get_generator()` via the `AI_PROVIDER` setting.
- Settings come from environment variables (`django-environ`); never hard-code secrets, never
  commit `.env`. Add new variables to `backend/.env.example` and `HOWTORUN.md`.
- User-facing UI text is **Polish**. Code, identifiers, comments and commit messages are English.
- Python: ruff (line length 100), type hints on public functions. TypeScript: strict, no `any`;
  Prettier (no semicolons, single quotes, width 100).
- Versioned API under `/api/v1/`; breaking changes need a new version or team agreement.
- Pin backend dependencies with `==` in `requirements*.txt`; frontend uses `package-lock.json`.

## Git workflow

- `main` is protected; work on feature branches (`feature/…`, `fix/…`) and open a pull request.
- At least one teammate reviews each PR (README §5). Keep PRs small and reference the
  requirement ID (e.g. `WF-07`, `PU-02`).
- Commit messages: imperative mood, short subject (e.g. `Add Testownik ZIP export`).

## Ownership (README §10)

| Area                                   | Owner             |
| -------------------------------------- | ----------------- |
| Backend (`backend/config`, `backend/apps`) | Piotr Staworko    |
| Frontend (`frontend/`)                 | Radosław Przybyło |
| AI & formats (`backend/ai_engine`)     | Szymon Pestrowicz |
