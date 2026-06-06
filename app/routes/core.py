import uuid
import subprocess
from pathlib import Path
from datetime import datetime

import requests
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse

from app.config import (
    API_KEY, BASE_URL, JSON_HEADERS, GEMINI_API_KEY,
    STATIC_DIR, TEMP_DIR, MAX_UPLOAD_SIZE,
)
from app.dependencies import temp_files, temp_lock
from app.utils import is_video, extract_audio
from app.assemblyai_client import upload, assemblyai_get, build_request, get_transcript_cached
from app.gemini_service import get_gemini_cached

router = APIRouter()


@router.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@router.get("/api/health")
async def health():
    if not API_KEY:
        return JSONResponse({"ok": False, "error": "API key not set"}, status_code=200)
    r = requests.get(f"{BASE_URL}/v2/transcript", headers={"Authorization": API_KEY},
                     params={"limit": 1})
    if r.status_code == 401:
        return JSONResponse({"ok": False, "error": "Invalid API key"})
    return JSONResponse({"ok": True, "gemini": bool(GEMINI_API_KEY)})


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    fid = str(uuid.uuid4())
    suffix = Path(file.filename).suffix.lower() or ".bin"
    save_path = TEMP_DIR / f"{fid}{suffix}"

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(413, f"File too large (max {MAX_UPLOAD_SIZE // 1024 // 1024} MB)")

    with open(save_path, "wb") as f:
        f.write(content)

    final_path = str(save_path)

    if is_video(file.filename):
        final_path = extract_audio(str(save_path))
        save_path.unlink(missing_ok=True)

    with temp_lock:
        temp_files[fid] = {
            "path": final_path,
            "created": datetime.now(),
            "name": file.filename,
        }

    return {"file_id": fid, "name": file.filename, "ready": True}


@router.post("/api/download-url")
async def download_url(request: Request):
    body = await request.json()
    url = (body.get("url") or "").strip()
    if not url:
        raise HTTPException(400, "URL required")

    fid = str(uuid.uuid4())
    out_tmpl = str(TEMP_DIR / f"{fid}.%(ext)s")

    title = url
    try:
        title_result = subprocess.run(
            ["yt-dlp", "--no-download", "--print", "title",
             "--no-playlist", url],
            capture_output=True, text=True, timeout=30
        )
        if title_result.returncode == 0 and title_result.stdout.strip():
            title = title_result.stdout.strip()
    except Exception:
        pass

    result = subprocess.run(
        ["yt-dlp", "--extract-audio", "--audio-format", "mp3",
         "--audio-quality", "0", "--output", out_tmpl,
         "--no-playlist", url],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        raise HTTPException(500, f"Download failed: {result.stderr[-400:]}")

    files = list(TEMP_DIR.glob(f"{fid}.*"))
    if not files:
        raise HTTPException(500, "Downloaded file not found")

    with temp_lock:
        temp_files[fid] = {
            "path": str(files[0]),
            "created": datetime.now(),
            "name": title,
        }

    return {"file_id": fid, "name": title, "ready": True}


@router.post("/api/transcribe")
async def transcribe(request: Request):
    body = await request.json()
    fid = body.get("file_id")
    cfg = body.get("config", {})

    if not API_KEY:
        raise HTTPException(500, "AssemblyAI API key not configured. Add ASSEMBLYAI_API_KEY to .env")

    with temp_lock:
        file_info = temp_files.get(fid)
    if not file_info:
        raise HTTPException(400, "File not found. Upload again.")

    upload_url = upload(file_info["path"])
    payload = build_request(upload_url, cfg)

    r = requests.post(f"{BASE_URL}/v2/transcript", headers=JSON_HEADERS, json=payload)
    if r.status_code != 200:
        raise HTTPException(500, f"Transcription submit failed: {r.text[:400]}")

    data = r.json()
    file_name = body.get("file_name")
    if file_name:
        from app.dependencies import filename_cache
        filename_cache[data["id"]] = file_name
    return {"transcript_id": data["id"], "status": data["status"]}


@router.get("/api/transcript/{tid}")
async def get_transcript(tid: str):
    return assemblyai_get(f"/v2/transcript/{tid}")


@router.patch("/api/transcript/{tid}/edit")
async def edit_transcript(tid: str, request: Request):
    """Save user edits to transcript text. Edits override original data in all exports."""
    from app.dependencies import edit_cache
    body = await request.json()
    edits = {}
    if body.get("utterances") is not None:
        edits["utterances"] = body["utterances"]
    if body.get("text") is not None:
        edits["text"] = body["text"]
    if not edits:
        raise HTTPException(400, "No edits provided")
    edit_cache[tid] = edits
    return {"ok": True}


@router.get("/api/resume/{tid}")
async def resume_transcript(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}")
    if data.get("status") != "completed":
        raise HTTPException(400, f"Transcript status: {data.get('status')}")
    return data


@router.post("/api/gemini/{tid}")
async def gemini_analysis(tid: str, request: Request):
    if not GEMINI_API_KEY:
        return JSONResponse({"error": "Gemini not configured"})

    data = get_transcript_cached(tid)
    if data.get("status") != "completed":
        return JSONResponse({"error": "Transcript not ready"})

    text = data.get("text", "")
    if len(text) < 20:
        return JSONResponse({"error": "Transcript too short"})

    body = await request.json()
    language = data.get("language_code", "en")
    has_speakers = bool(data.get("utterances"))

    spk_labels = list({u.get("speaker") for u in (data.get("utterances") or []) if u.get("speaker")})

    opts = {
        "summary": body.get("summary", True),
        "notes": body.get("notes", False),
        "speakers": body.get("speakers", True),
    }

    result = get_gemini_cached(tid, text, language, has_speakers, spk_labels if spk_labels else None, opts=opts)
    return JSONResponse(result)
