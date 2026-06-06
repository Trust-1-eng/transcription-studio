"""Integration tests for alignment API endpoints.
Tests against a mock transcript cached in memory (no real AssemblyAI needed)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import io
from docx import Document
from main import app
from fastapi.testclient import TestClient
from app.dependencies import transcript_cache, alignment_cache
from time import time

client = TestClient(app)

MOCK_TID = "test_alignment_001"
MOCK_WORDS = [
    {"text": "The", "start": 100, "end": 200, "confidence": 0.99},
    {"text": "quick", "start": 300, "end": 500, "confidence": 0.99},
    {"text": "brown", "start": 600, "end": 800, "confidence": 0.99},
    {"text": "fox", "start": 900, "end": 1100, "confidence": 0.99},
    {"text": "jumps", "start": 1200, "end": 1500, "confidence": 0.99},
    {"text": "over", "start": 1600, "end": 1800, "confidence": 0.98},
    {"text": "the", "start": 1900, "end": 2000, "confidence": 0.99},
    {"text": "lazy", "start": 2100, "end": 2300, "confidence": 0.97},
    {"text": "dog", "start": 2400, "end": 2700, "confidence": 0.99},
    {"text": "and", "start": 2800, "end": 2900, "confidence": 0.98},
    {"text": "then", "start": 3000, "end": 3200, "confidence": 0.97},
    {"text": "it", "start": 3300, "end": 3400, "confidence": 0.99},
    {"text": "ran", "start": 3500, "end": 3700, "confidence": 0.98},
    {"text": "away", "start": 3800, "end": 4100, "confidence": 0.99},
]


def _make_docx(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def setup():
    """Inject mock transcript into cache."""
    transcript_cache[MOCK_TID] = ({
        "id": MOCK_TID,
        "status": "completed",
        "text": " ".join(w["text"] for w in MOCK_WORDS),
        "words": MOCK_WORDS,
        "utterances": [{"text": " ".join(w["text"] for w in MOCK_WORDS), "start": 100, "end": 4100, "speaker": "A"}],
    }, time())


def test_upload_docx():
    setup()
    docx_bytes = _make_docx("The quick brown fox jumps over the lazy dog and then it ran away.")
    r = client.post(
        f"/api/align/{MOCK_TID}/upload",
        files={"file": ("transcript.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert r.status_code == 200, f"Upload failed: {r.text}"
    data = r.json()
    print(f"  Upload OK: match_rate={data['match_rate']}, cues={data['cue_count']}")
    assert data["ok"] is True
    assert data["match_rate"] >= 0.8
    assert data["cue_count"] >= 1
    assert data["warning"] is None


def test_upload_edited_docx():
    setup()
    # Edited text: changed "fox" to "Fox", added "Dr." before "dog"
    docx_bytes = _make_docx("The quick brown Fox jumps over the lazy Dr. dog and then it ran away.")
    r = client.post(
        f"/api/align/{MOCK_TID}/upload",
        files={"file": ("edited.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert r.status_code == 200
    data = r.json()
    print(f"  Edited upload: match_rate={data['match_rate']}, cues={data['cue_count']}")
    assert data["match_rate"] >= 0.7  # still high despite edits


def test_export_vtt():
    setup()
    docx_bytes = _make_docx("The quick brown fox jumps over the lazy dog and then it ran away.")
    client.post(
        f"/api/align/{MOCK_TID}/upload",
        files={"file": ("transcript.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    r = client.get(f"/api/align/{MOCK_TID}/vtt")
    assert r.status_code == 200
    content = r.text
    print(f"  VTT export: {len(content)} chars")
    assert content.startswith("WEBVTT")
    assert "-->" in content
    assert "quick brown fox" in content


def test_export_srt():
    setup()
    docx_bytes = _make_docx("The quick brown fox jumps over the lazy dog and then it ran away.")
    client.post(
        f"/api/align/{MOCK_TID}/upload",
        files={"file": ("transcript.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    r = client.get(f"/api/align/{MOCK_TID}/srt")
    assert r.status_code == 200
    content = r.text
    print(f"  SRT export: {len(content)} chars")
    assert "-->" in content


def test_export_without_upload():
    r = client.get("/api/align/nonexistent/vtt")
    assert r.status_code == 404


def test_upload_unsupported_format():
    setup()
    r = client.post(
        f"/api/align/{MOCK_TID}/upload",
        files={"file": ("test.txt", b"some text content", "text/plain")},
    )
    assert r.status_code == 400
    assert "Unsupported" in r.json()["detail"]


def cleanup():
    alignment_cache.pop(MOCK_TID, None)
    transcript_cache.pop(MOCK_TID, None)


if __name__ == "__main__":
    print("Running alignment API tests...\n")
    test_upload_docx()
    test_upload_edited_docx()
    test_export_vtt()
    test_export_srt()
    test_export_without_upload()
    test_upload_unsupported_format()
    cleanup()
    print("\nAll API tests passed!")
