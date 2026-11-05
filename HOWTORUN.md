# How to run Testownik AI locally

The app has two parts that run side by side during development:

| Part     | Folder      | Stack                                   | URL                          |
| -------- | ----------- | --------------------------------------- | ---------------------------- |
| Frontend | `frontend/` | React 19 + TypeScript + Vite            | http://localhost:5173        |
| Backend  | `backend/`  | Django + Django REST Framework (Python) | http://127.0.0.1:8000/api/v1 |

The Vite dev server forwards every `/api/...` request to Django, so you only open
http://localhost:5173 in the browser.

Out of the box the backend uses a **mock AI generator** and **SQLite**, so you do **not**
need Ollama, a GPU, PostgreSQL or Docker to start working.

## 1. Prerequisites

| Tool    | Version                         | Check              |
| ------- | ------------------------------- | ------------------ |
| Git     | any recent                      | `git --version`    |
| Python  | 3.12+ (3.13 recommended)        | `python --version` |
| Node.js | 22.12+ (24 LTS recommended)     | `node --version`   |
| Docker  | optional (PostgreSQL / Ollama)  | `docker --version` |


## 2. Backend (first time)

PowerShell (Windows):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python manage.py migrate
```

bash / macOS / Linux:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Git Bash on Windows: source .venv/Scripts/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
```

> If PowerShell blocks `Activate.ps1`, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## 3. Frontend (first time)

```bash
cd frontend
npm install
```

## 4. Run the app

Use two terminals.

**Terminal 1 – backend** (with the virtualenv activated):

```bash
cd backend
python manage.py runserver
```

**Terminal 2 – frontend:**

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. Paste some text, click **Generuj pytania**, wait for the progress
bar (the mock pretends to work for ~4 s), review the questions and download the ZIP.

Useful backend URLs:

- Swagger UI (API docs): http://127.0.0.1:8000/api/docs/
- OpenAPI schema: http://127.0.0.1:8000/api/schema/
- Health check: http://127.0.0.1:8000/api/v1/health/

## 5. Tests, linting, formatting

Backend (inside `backend/`, virtualenv active):

```bash
pytest                 # tests
ruff check .           # lint
ruff format .          # format
python manage.py spectacular --validate --fail-on-warn --file schema.yml   # export + validate OpenAPI
```

Frontend (inside `frontend/`):

```bash
npm test               # Vitest + Testing Library
npm run lint           # oxlint
npm run format         # Prettier (format:check in CI)
npm run build          # type-check + production build
```

GitHub Actions (`.github/workflows/ci.yml`) runs all of these on every pull request.

## 6. Configuration

Backend settings come from environment variables / `backend/.env` (see `backend/.env.example`):

| Variable                  | Default                 | Meaning                                         |
| ------------------------- | ----------------------- | ----------------------------------------------- |
| `DJANGO_DEBUG`            | `False`                 | Debug mode (`True` in `.env.example`)           |
| `DJANGO_SECRET_KEY`       | dev-only key            | Must be set to a real secret outside dev        |
| `DATABASE_URL`            | SQLite `db.sqlite3`     | e.g. `postgres://testownik:testownik@localhost:5432/testownik` |
| `AI_PROVIDER`             | `mock`                  | `mock` or `ollama`                              |
| `OLLAMA_BASE_URL`         | `http://localhost:11434`| Ollama server                                   |
| `OLLAMA_MODEL`            | `llama3.1:8b`           | Model to use                                    |
| `MAX_UPLOAD_SIZE_MB`      | `100`                   | Per-file upload limit                           |
| `MOCK_GENERATION_SECONDS` | `4`                     | Fake job duration for the mock generator        |

Frontend (optional, `frontend/.env.local`): `VITE_API_BASE_URL` (default `/api/v1`) and
`VITE_API_PROXY_TARGET` (default `http://127.0.0.1:8000`).

## 7. Optional: PostgreSQL and Ollama via Docker

Not needed for Stage 1. When you want them:

```bash
docker compose up -d postgres ollama
docker compose exec ollama ollama pull llama3.1:8b
```

Then set in `backend/.env`:

```
DATABASE_URL=postgres://testownik:testownik@localhost:5432/testownik
AI_PROVIDER=ollama
```

PostgreSQL also needs a driver: `pip install "psycopg[binary]"` (add it to
`requirements.txt` when the team switches to Postgres). You can also install
[Ollama](https://ollama.com/download) natively instead of using Docker; it uses the GPU directly.

> `AI_PROVIDER=ollama` currently raises "not implemented" – the integration lives in
> `backend/ai_engine/generator.py` (`OllamaQuestionGenerator`) and is the AI module's next task.

## Troubleshooting

- **"Nie można połączyć się z serwerem"** in the UI → the Django server is not running on port 8000.
- **`npm run dev` fails with an engine / syntax error** → Node is older than 22.12; switch to Node 24.
- **Port already in use** → `python manage.py runserver 8001` and start Vite with
  `VITE_API_PROXY_TARGET=http://127.0.0.1:8001 npm run dev`.
- **Generated jobs disappear** → expected: Stage 1 keeps jobs in memory only; restarting Django clears them.
