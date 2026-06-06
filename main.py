import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import STATIC_DIR
from app.utils import ensure_font
from app.dependencies import temp_files, temp_lock
from app.routes.core import router as core_router
from app.routes.export import router as export_router


# ─────────────────────────────────────────────
# Temp file cleanup (runs every hour)
# ─────────────────────────────────────────────
def _cleanup_old_files():
    cutoff = datetime.now() - timedelta(hours=2)
    with temp_lock:
        stale = [fid for fid, info in temp_files.items() if info["created"] < cutoff]
        for fid in stale:
            try:
                os.remove(temp_files[fid]["path"])
            except Exception:
                pass
            del temp_files[fid]
    _schedule_cleanup()


def _schedule_cleanup():
    t = threading.Timer(3600, _cleanup_old_files)
    t.daemon = True
    t.start()


# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_font()
    _schedule_cleanup()
    yield


app = FastAPI(title="AssemblyAI Transcription Studio", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(core_router)
app.include_router(export_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
