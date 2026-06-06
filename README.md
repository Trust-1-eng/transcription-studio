# Transcription Studio

Local FastAPI web service for high-quality speech-to-text on top of AssemblyAI Universal-2 (99 languages, including Ukrainian and Russian) with optional Gemini-powered analysis and a one-page Vanilla JS UI.

Drag-and-drop video or audio, paste a YouTube / Vimeo / SoundCloud URL — the service extracts audio, sends it to AssemblyAI, streams status back to the browser, and renders the transcript with speaker labels, timestamps, summaries, and 25+ export formats.

## Features

- **AssemblyAI Universal-2** — 99 languages, automatic language detection, speaker diarization, speech understanding (summaries, chapters, sentiment, key phrases).
- **Source flexibility** — local files (video, audio) or URL (1000+ sites via `yt-dlp`).
- **Audio pipeline** — `FFmpeg` extracts the best audio track from any container (`.mp4`, `.mkv`, `.mov`, `.avi`, …) before upload.
- **Streaming status** — Server-Sent Events keep the UI in sync with the AssemblyAI job (queued → processing → completed).
- **Exports** — plain TXT, formatted Word (`python-docx`), PDF with full Cyrillic support (`fpdf2` + DejaVuSans), bilingual columns, interview script, verbatim with pause/interruption markers, SRT/VTT subtitles, ZIP bundle.
- **Gemini integration (optional)** — post-transcription analysis: summarization, structured notes, Q&A material.
- **No build step on the frontend** — `static/index.html` + `static/app.js` opens directly in the browser.

## Stack

| Layer | Tech |
| --- | --- |
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| Speech-to-text | AssemblyAI REST (Universal-2) |
| AI analysis | Google Gemini (optional) |
| Audio extraction | FFmpeg (system) |
| URL download | yt-dlp |
| Word export | python-docx |
| PDF export | fpdf2 + DejaVuSans |
| Frontend | Vanilla HTML / CSS / JS |

## Quick start

```bash
# Prerequisites: Python 3.11+, FFmpeg, an AssemblyAI API key.
brew install ffmpeg              # macOS — or use your package manager

git clone https://github.com/Trust-1-eng/transcription-studio.git
cd transcription-studio

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: paste your ASSEMBLYAI_API_KEY (and optionally GEMINI_API_KEY)

uvicorn main:app --reload
# Open http://localhost:8000
```

## Architecture

```
Browser (static/index.html, app.js)
        │
        ▼
FastAPI (main.py)
  ├─ app/routes/core.py     ─ upload, transcribe, status (SSE)
  ├─ app/routes/export.py   ─ format conversion, ZIP bundles
  ├─ app/assemblyai_client.py
  ├─ app/gemini_service.py
  └─ app/exporters/         ─ pdf.py · document.py · subtitles.py · table.py · text.py
        │
        ▼
External: AssemblyAI REST · Gemini API · FFmpeg · yt-dlp
```

## Project layout

```
.
├── main.py                  FastAPI app entry point
├── app/                     Backend modules
│   ├── routes/              HTTP routes (core, export)
│   ├── exporters/           Format converters (PDF, DOCX, SRT, …)
│   ├── assemblyai_client.py REST wrapper around AssemblyAI
│   ├── gemini_service.py    Optional Gemini analysis
│   ├── config.py            Settings from .env
│   └── utils.py             FFmpeg helpers, font management
├── static/                  Frontend (no build step)
├── docs/                    Function references for languages
├── tests/                   API + UI tests
├── MANIFEST.md              Full feature roadmap and design notes
└── requirements.txt
```

See [`MANIFEST.md`](MANIFEST.md) for the full feature roadmap and design discussion.

## License

MIT. See `LICENSE` once added.
