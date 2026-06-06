# AssemblyAI Transcription Studio

Full-featured web application for audio/video transcription powered by AssemblyAI Universal-2 model. Supports 99 languages, speaker diarization, PII redaction, AI analysis via Google Gemini, and exports to 36+ formats.

## Features

**Transcription**
- AssemblyAI Universal-2 model — 99 languages with automatic detection
- Speaker diarization (up to 10 speakers, multichannel support)
- PII redaction (50+ entity types) with audio and text methods
- Code-switching for multilingual audio
- Custom vocabulary and formatting options

**Input Sources**
- File upload (drag-and-drop) — MP3, WAV, MP4, MKV, AVI, MOV, and more
- YouTube and 1000+ sites via yt-dlp
- Direct audio URL
- Automatic video-to-audio conversion via FFmpeg

**AI Analysis (Google Gemini)**
- Auto-generated titles and summaries
- Topic extraction and sentiment analysis
- Key moments and speaker identification
- Language-aware responses

**Export Formats (36+)**
- **Text**: Standard, verbatim, bilingual, literary, paragraphs
- **Documents**: DOCX (standard, verbatim, bilingual, literary, interview)
- **Tables**: DOCX and PDF with timestamps and speaker labels
- **PDF**: Full Unicode/Cyrillic support via DejaVu Sans
- **Subtitles**: SRT and VTT with translation support
- **Data**: CSV (sentence-level and word-level with confidence scores)
- **ZIP**: Bundle all formats in a single download

**Translation**
- 80+ target languages
- Formal and informal styles
- Bilingual export (original + translation side by side)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| APIs | AssemblyAI REST API (direct HTTP), Google Gemini, yt-dlp |
| Documents | python-docx, fpdf2 (PDF with Unicode) |
| Media | FFmpeg, yt-dlp |
| Frontend | Vanilla JavaScript, HTML5, CSS3 (no build tools) |
| Deployment | Docker, docker-compose |

## Quick Start

### With Docker (recommended)
```bash
# Clone the repo
git clone https://github.com/Trust-1-eng/transcription-studio.git
cd transcription-studio

# Set API keys
echo "ASSEMBLYAI_API_KEY=your_key_here" > .env
echo "GEMINI_API_KEY=your_key_here" >> .env

# Run
docker compose up --build
```
Open http://localhost:8000

### Manual Setup
```bash
# Install system dependencies (macOS)
brew install ffmpeg
pip install yt-dlp

# Install Python packages
pip install -r requirements.txt

# Set environment variables
export ASSEMBLYAI_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here  # optional

# Run
python main.py
```

## Architecture

```
app/
├── config.py              # API keys, paths, constants
├── dependencies.py        # Shared state: caches, locks
├── assemblyai_client.py   # AssemblyAI REST API client (no SDK)
├── gemini_service.py      # Gemini API with caching and retries
├── utils.py               # Font download, audio helpers, formatting
├── routes/
│   ├── core.py            # Upload, transcribe, poll, gemini endpoints
│   ├── export.py          # 40+ export endpoints + ZIP bundle
│   └── alignment.py       # Subtitle alignment for edited transcripts
└── exporters/
    ├── text.py            # Plain text format generators
    ├── document.py        # DOCX generators (6 styles)
    ├── table.py           # Table exports (DOCX + PDF)
    ├── pdf.py             # PDF with Unicode font support
    └── subtitles.py       # SRT/VTT generators
```

**Design decisions:**
- Direct HTTP to AssemblyAI API (no SDK) for full parameter control
- In-memory caching with TTL (5 min transcripts, 10 min Gemini)
- Thread-safe state management with locks
- Automatic temp file cleanup (2-hour retention)
- Font auto-download on first run

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ASSEMBLYAI_API_KEY` | Yes | AssemblyAI API key |
| `GEMINI_API_KEY` | No | Google Gemini API key (for AI analysis) |

## License

MIT
