import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# AssemblyAI
API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")
BASE_URL = "https://api.assemblyai.com"
JSON_HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}
UPLOAD_HEADERS = {"Authorization": API_KEY}

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Paths
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = Path(tempfile.gettempdir()) / "assembly_transcription"
FONTS_DIR = BASE_DIR / "fonts"
STATIC_DIR = BASE_DIR / "static"

TEMP_DIR.mkdir(exist_ok=True)
FONTS_DIR.mkdir(exist_ok=True)

DEJAVU_PATH = FONTS_DIR / "DejaVuSans.ttf"
DEJAVU_BOLD_PATH = FONTS_DIR / "DejaVuSans-Bold.ttf"

DEJAVU_URLS = [
    "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/main/fonts/DejaVuSans.ttf",
    "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/fonts/DejaVuSans.ttf",
    "https://github.com/matomo-org/travis-scripts/raw/master/fonts/DejaVuSans.ttf",
]

SYSTEM_FONT_CANDIDATES = [
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/opt/homebrew/share/fonts/dejavu-fonts/DejaVuSans.ttf"),
]

# Limits
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB

# File extensions
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".mts"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus", ".aiff"}

# Cache TTL
CACHE_TTL = 300       # 5 min
GEMINI_CACHE_TTL = 600  # 10 min
