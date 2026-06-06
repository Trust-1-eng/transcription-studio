import shutil
import subprocess
from pathlib import Path

import requests
from fastapi import HTTPException

from app.config import (
    DEJAVU_PATH, DEJAVU_URLS, SYSTEM_FONT_CANDIDATES, VIDEO_EXTS,
)


# ─────────────────────────────────────────────
# Font setup
# ─────────────────────────────────────────────
def ensure_font() -> bool:
    """Return True if a usable Unicode font is available at DEJAVU_PATH."""
    if DEJAVU_PATH.exists():
        return True

    for candidate in SYSTEM_FONT_CANDIDATES:
        if candidate.exists():
            shutil.copy(str(candidate), str(DEJAVU_PATH))
            print(f"Font: using system font {candidate}")
            return True

    for url in DEJAVU_URLS:
        try:
            print(f"Downloading font from {url} …")
            r = requests.get(url, timeout=20, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 50_000:
                DEJAVU_PATH.write_bytes(r.content)
                print("Font downloaded successfully.")
                return True
            print(f"  → {r.status_code}, skipping")
        except Exception as e:
            print(f"  → failed: {e}")

    print("WARNING: Could not obtain Unicode font. PDF export will use ASCII fallback.")
    return False


# ─────────────────────────────────────────────
# Audio helpers
# ─────────────────────────────────────────────
def is_video(filename: str) -> bool:
    return Path(filename).suffix.lower() in VIDEO_EXTS


def extract_audio(input_path: str) -> str:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", input_path],
        capture_output=True, text=True, timeout=30
    )
    if not probe.stdout.strip():
        raise HTTPException(400, "Video file does not contain an audio stream")

    out = str(Path(input_path).with_suffix(".mp3"))
    result = subprocess.run(
        ["ffmpeg", "-i", input_path, "-vn", "-acodec", "libmp3lame",
         "-ab", "192k", "-ar", "44100", "-y", out],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise HTTPException(500, f"FFmpeg error: {result.stderr[-500:]}")
    return out


# ─────────────────────────────────────────────
# Time formatting
# ─────────────────────────────────────────────
def ms_to_srt(ms: int) -> str:
    s, ms_r = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms_r:03d}"


def ms_to_vtt(ms: int) -> str:
    return ms_to_srt(ms).replace(",", ".")


def ms_to_readable(ms: int) -> str:
    s, _ = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
