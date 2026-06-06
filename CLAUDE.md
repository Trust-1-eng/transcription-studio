# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

AssemblyAI Transcription Studio — local web app for audio/video transcription via AssemblyAI API (Universal-2, 99 languages). Supports file upload, YouTube/URL download via yt-dlp, and exports to 36+ formats. Includes Gemini API integration for post-transcription analysis.

## Commands

```bash
# Run the app (http://localhost:8000)
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Install dependencies
pip install -r requirements.txt

# System dependencies (macOS)
brew install ffmpeg
pip install yt-dlp

# Run API tests (requires running server + a transcript ID)
bash tests/test_api.sh <transcript_id>

# Run UI tests
python tests/test_ui.py
```

## Architecture

**Backend** (Python/FastAPI) — modular `app/` package:
- `main.py` → app creation, lifespan, router mounting
- `app/config.py` → API keys, paths, constants
- `app/dependencies.py` → shared mutable state: in-memory caches (5-min transcript, 10-min Gemini), locks
- `app/assemblyai_client.py` → direct HTTP calls to AssemblyAI REST API (no SDK), request builder, caching
- `app/gemini_service.py` → Gemini API integration with caching
- `app/utils.py` → font auto-download, audio helpers (ffmpeg/yt-dlp), time formatting
- `app/routes/core.py` → main routes: index, health, upload, transcribe, poll, gemini
- `app/routes/export.py` → ~30 export endpoints + ZIP bundle
- `app/exporters/` → format generators: text (standard/verbatim/bilingual/literary), document (DOCX: standard/verbatim/bilingual/literary/interview), table (DOCX+PDF), pdf (fpdf2 + DejaVuSans for Cyrillic), subtitles (SRT/VTT)

**Frontend** (vanilla HTML/CSS/JS, no build step):
- `static/index.html` → full UI (steps: Source → Options → Results)
- `static/app.js` → all client logic: upload, polling, export, history
- `static/data.js` → language lists, PII policy arrays
- `static/style.css` → dark theme, toggle sliders

## Key Design Decisions

- **No AssemblyAI SDK** — uses `requests` directly to `api.assemblyai.com` for full parameter control. Auth header is `Authorization: KEY` (no Bearer prefix).
- **No frontend build tools** — vanilla JS served by FastAPI's StaticFiles.
- **PDF Cyrillic support** — requires `DejaVuSans.ttf` in `fonts/`, auto-downloaded on first run via `app/utils.py:ensure_font()`.
- **Temp file lifecycle** — uploaded/converted files go to `temp/`, background thread cleans files older than 2 hours.
- **UI controls** — all settings use toggle sliders (not checkboxes), numeric values use range sliders.

## Environment Variables

- `ASSEMBLYAI_API_KEY` (required)
- `GEMINI_API_KEY` (optional, for AI analysis features)

## Reference Docs

- `MANIFEST.md` — full roadmap, API parameter mapping, feature matrix, export format specs
- `SKILL.md` — AssemblyAI API reference (auth, models, gotchas, common mistakes)
- `docs/` — language function libraries and implementation notes
