# AssemblyAI Transcription Studio

## Project Overview

**AssemblyAI Transcription Studio** is a local, lightweight web application that provides a comprehensive interface for transcribing audio and video files using the AssemblyAI API (Universal-2 model). It supports 99 languages, including Ukrainian and Russian, and is designed to give the user fine-grained control over transcription settings.

The tool supports local file uploads as well as direct URL downloads (e.g., from YouTube) via `yt-dlp`. It provides advanced export capabilities (TXT, DOCX, PDF, MD, SRT, VTT, CSV, JSON, and ZIP bundles) and integrates with the Google Gemini API to offer AI-powered summaries, topic extraction, and transcript analysis.

### Architecture and Tech Stack

*   **Backend:** Python 3.11+ using **FastAPI**. Modular structure under `app/` package with separate modules for config, routes, exporters, and services.
*   **Frontend:** Vanilla HTML, CSS, and JavaScript. Served directly by FastAPI from the `static/` directory with no build step required.
*   **External Utilities:** 
    *   `ffmpeg` for extracting audio from video files.
    *   `yt-dlp` for downloading audio from various web URLs.
*   **APIs:** AssemblyAI REST API (direct HTTP calls without the SDK for maximum parameter control) and Google Gemini API (for post-transcription analysis).

## Directory Structure

*   `main.py`: Entry point — FastAPI app creation, lifespan, router mounting (~55 lines).
*   `app/`: Backend Python package:
    *   `config.py`: All configuration, API keys, paths, constants.
    *   `dependencies.py`: Shared mutable state (caches, locks).
    *   `utils.py`: Font setup, audio helpers, time formatting.
    *   `assemblyai_client.py`: AssemblyAI API client, request builder, transcript caching.
    *   `gemini_service.py`: Gemini API integration and caching.
    *   `routes/core.py`: Main routes (index, health, upload, transcribe, poll, gemini).
    *   `routes/export.py`: All export endpoints (~25 routes).
    *   `exporters/helpers.py`: Document header, speaker resolution, download helpers.
    *   `exporters/text.py`: TXT, CSV exporters.
    *   `exporters/document.py`: DOCX exporter.
    *   `exporters/pdf.py`: PDF exporter with Cyrillic support.
    *   `exporters/subtitles.py`: SRT, VTT, translation exporters.
*   `static/`: Frontend assets (`index.html`, `style.css`, `data.js`, `app.js`).
*   `fonts/`: `DejaVuSans.ttf` font for PDF Cyrillic support.
*   `temp/`: Temporary storage, auto-cleaned by background process.
*   `tests/`: API and UI tests.
*   `docs/`: Reference documentation and language function libraries.
*   `MANIFEST.md`: Extensive project roadmap, architecture design, API mapping documentation, and feature planning.

## Building and Running

### Prerequisites
1.  Python 3.11 or higher.
2.  System utilities: `ffmpeg` and `yt-dlp`.
    ```bash
    # On macOS
    brew install ffmpeg
    pip install yt-dlp
    ```

### Setup Instructions

1.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables:**
    Copy `.env.example` to `.env` and add your API keys:
    ```env
    ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
    GEMINI_API_KEY=your_gemini_api_key_here  # Optional: For AI Analysis features
    ```

3.  **Run the Application:**
    ```bash
    python main.py
    # OR
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

4.  **Access the UI:**
    Open your browser and navigate to `http://localhost:8000`.

## Development Conventions

*   **Frontend:** Vanilla JavaScript and CSS with no build tools. Data arrays (languages, PII policies) are in `static/data.js`, logic in `static/app.js`.
*   **Backend:** Modular structure under `app/` package. Routes use FastAPI `APIRouter`.
*   **AssemblyAI Integration:** Direct `requests` calls for full parameter control (no SDK).
*   **Caching:** In-memory caches in `app/dependencies.py` (5-min transcript, 10-min Gemini).
*   **Temporary File Management:** Background thread cleans files older than 2 hours.
