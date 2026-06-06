from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from app.assemblyai_client import get_transcript_cached
from app.dependencies import alignment_cache
from app.importers.text_extract import extract_text
from app.importers.aligner import align_texts, build_vtt_cues
from app.exporters.subtitles import make_aligned_vtt, make_aligned_srt

router = APIRouter()


@router.post("/api/align/{tid}/upload")
async def upload_edited_transcript(tid: str, file: UploadFile = File(...)):
    data = get_transcript_cached(tid)
    words = data.get("words") or []
    if not words:
        raise HTTPException(400, "This transcript has no word-level timestamps. Re-transcribe with default settings.")

    file_bytes = await file.read()
    try:
        edited_text = extract_text(file.filename or "file.txt", file_bytes)
    except ValueError as e:
        raise HTTPException(400, str(e))

    aligned = align_texts(edited_text, words)
    matched = sum(1 for w in aligned if w["matched"])
    match_rate = matched / len(aligned) if aligned else 0.0

    cues = build_vtt_cues(aligned)

    alignment_cache[tid] = {
        "edited_text": edited_text,
        "aligned_words": aligned,
        "cues": cues,
    }

    warning = None
    if match_rate < 0.5:
        warning = "Low match rate — the uploaded transcript may not correspond to this audio."

    return {
        "ok": True,
        "word_count_edited": len(aligned),
        "word_count_aai": len(words),
        "match_rate": round(match_rate, 3),
        "cue_count": len(cues),
        "warning": warning,
        "preview": [{"start": c["start"], "end": c["end"], "text": c["text"]} for c in cues[:5]],
    }


@router.get("/api/align/{tid}/vtt")
async def export_aligned_vtt(tid: str):
    cached = alignment_cache.get(tid)
    if not cached:
        raise HTTPException(404, "No alignment found. Upload an edited transcript first.")
    content = make_aligned_vtt(cached["cues"])
    return Response(
        content=content,
        media_type="text/vtt",
        headers={"Content-Disposition": f"attachment; filename=aligned_{tid}.vtt"},
    )


@router.get("/api/align/{tid}/srt")
async def export_aligned_srt(tid: str):
    cached = alignment_cache.get(tid)
    if not cached:
        raise HTTPException(404, "No alignment found. Upload an edited transcript first.")
    content = make_aligned_srt(cached["cues"])
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=aligned_{tid}.srt"},
    )
