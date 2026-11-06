# How to run Testownik AI locally

The app has two parts that run side by side during development:

| Part     | Folder      | Stack                                   | URL                          |
| -------- | ----------- | --------------------------------------- | ---------------------------- |
| Frontend | `frontend/` | React 19 + TypeScript + Vite            | http://localhost:5173        |
| Backend  | `backend/`  | Django + Django REST Framework (Python) | http://127.0.0.1:8000/api/v1 |

The Vite dev server forwards every `/api/...` request to Django, so you only open
http://localhost:5173 in the browser.

Out of the box the backend uses a **mock AI generator** and **SQLite**, so you do **not**
need an API key, Ollama, a GPU, PostgreSQL or Docker to start working. To generate real
questions, add a Gemini API key (section 7).

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
| `AI_PROVIDER`             | `mock`                  | `mock`, `gemini` or `ollama`                    |
| `GEMINI_API_KEY`          | empty                   | Your Gemini API key (see section 7)             |
| `GEMINI_MODEL`            | `gemini-3.5-flash-lite` | Gemini model ID (`python manage.py gemini_models` lists yours) |
| `OLLAMA_BASE_URL`         | `http://localhost:11434`| Ollama server                                   |
| `OLLAMA_MODEL`            | `llama3.1:8b`           | Model to use                                    |
| `MAX_UPLOAD_SIZE_MB`      | `100`                   | Per-file upload limit                           |
| `MOCK_GENERATION_SECONDS` | `4`                     | Fake job duration for the mock generator        |
| `AI_LOG_LEVEL`            | `INFO`                  | `DEBUG` logs the material sent to the model and its raw reply |

Frontend (optional, `frontend/.env.local`): `VITE_API_BASE_URL` (default `/api/v1`) and
`VITE_API_PROXY_TARGET` (default `http://127.0.0.1:8000`).

## 7. Real questions with Gemini

The provider is chosen by `AI_PROVIDER` in `backend/.env`: `mock` (default), `gemini` or
`ollama` (not implemented yet). Everything else in `.env` stays as it is.

1. Create a free API key in Google AI Studio: https://aistudio.google.com/apikey
2. Edit `backend/.env` (gitignored – **never commit the key** or put it in frontend code).
   Keep all existing lines and change/add only these three:

   ```
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your-key-here
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```

   - `AI_PROVIDER` already exists – change `mock` to `gemini`.
   - `GEMINI_API_KEY` and `GEMINI_MODEL` are new if your `.env` was copied from an older
     `.env.example`; add them anywhere in the file. `GEMINI_MODEL` is optional
     (`gemini-3.5-flash-lite` is the default).
   - No quotes or spaces around `=`. Each variable may appear only once.
3. Install the Gemini SDK (`google-genai`) into the backend virtualenv (once, and again
   whenever `requirements.txt` changes):

   ```bash
   cd backend
   pip install -r requirements-dev.txt
   ```

4. Restart the backend (`Ctrl+C`, then `python manage.py runserver`). Django reads `.env` only
   at startup.
5. Start the frontend as usual (`npm run dev`) and open http://localhost:5173. Paste some real
   study material or upload files, click **Generuj pytania** and wait – a real model takes
   several seconds to tens of seconds.

**Files with Gemini.** `.txt` and `.md` are read locally. PDF, DOCX, PPTX and images
(`.png`, `.jpg`, `.jpeg`, `.webp`) are sent to Gemini, which extracts their text – including
OCR of scans, photos and handwriting, and short descriptions of diagrams. The progress bar shows
**Odczytywanie plików…** during this step and **Generowanie pytań…** after it.

- Each such file costs **one extra request** to your Gemini quota (the questions are then
  generated in one more request).
- Gemini's limit is 50 MB / 1000 pages per file. Files over 15 MB are sent through Gemini's
  Files API and deleted from Google's servers right after reading.
- With `AI_PROVIDER=mock`, these files are not read – the material contains only a placeholder
  line. With `ollama`, they are rejected (no reader yet).

**Seeing what Gemini returned.** Add `AI_LOG_LEVEL=DEBUG` to `backend/.env` and restart the
backend. Each request then prints to the backend terminal:

- `Gemini read ...` – for each uploaded PDF/DOCX/PPTX/image: its size, `finish_reason` and the
  first 1000 characters of the text Gemini extracted,
- `Gemini request: ...` – model, question count, language, material length and the first
  1000 characters of the material that was actually sent,
- `Gemini response: ...` – `finish_reason`, `block_reason`, token counts and the raw JSON reply.

Set it back to `INFO` afterwards – `DEBUG` prints your study material into the terminal.

To go back to fake questions, set `AI_PROVIDER=mock` and restart the backend. The Gemini lines can
stay in the file; they are ignored while the provider is `mock`.

Each teammate uses their own key. The free tier has per-minute and per-day request limits
(see your project's limits at https://aistudio.google.com/rate-limit). One quiz is one request
plus one per uploaded PDF/DOCX/PPTX/image, and each "Wygeneruj ponownie" is one more. When you hit the limit, the UI shows a message and
you can try again a bit later. On the free tier Google may use the submitted material to improve
its products, so don't upload anything confidential.

Switch back to `AI_PROVIDER=mock` when working on the UI to save your quota.

## 8. Optional: PostgreSQL and Ollama via Docker

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
- **"Brak klucza GEMINI_API_KEY"** → `AI_PROVIDER=gemini` is set but the key is missing from
  `backend/.env`, or the server was not restarted after editing it.
- **"Model Gemini „…” nie jest dostępny"** (backend log: `404 ... is not found for API version`)
  → your key can't use that model ID. List the models it can use and copy one into
  `GEMINI_MODEL`, then restart the backend:

  ```bash
  cd backend
  python manage.py gemini_models
  ```

  Use a specific model ID (e.g. `gemini-3.5-flash-lite`); aliases like `gemini-flash-latest`
  don't work for this API.
- **"Model nie zwrócił żadnych pytań"** (log: `Gemini returned no usable questions ... '[]'`)
  → the model found nothing to ask about: the material is too short, or the file had no
  readable content. Use `AI_LOG_LEVEL=DEBUG` (section 7) to see what was extracted and sent.
- **"Odczyt plików .pdf wymaga AI_PROVIDER=gemini"** → you uploaded a PDF/DOCX/PPTX/image while
  `AI_PROVIDER=ollama`. Switch to `gemini`, or paste the text.
- **Text of a long PDF is cut off** (log: `was cut off at the model's output limit`) → Gemini
  can only return a limited amount of text per request. Split the document into smaller files.
- **Generated jobs disappear** → expected: Stage 1 keeps jobs in memory only; restarting Django clears them.
