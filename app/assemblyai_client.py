from datetime import datetime

import requests
from fastapi import HTTPException

from app.config import API_KEY, BASE_URL, JSON_HEADERS, UPLOAD_HEADERS, CACHE_TTL
from app.dependencies import transcript_cache, edit_cache


def get_transcript_cached(tid: str) -> dict:
    """Get transcript data with caching to avoid repeated API calls during export.
    If user edits exist in edit_cache, they override utterance/text fields."""
    now = datetime.now().timestamp()
    if tid in transcript_cache:
        data, ts = transcript_cache[tid]
        if now - ts < CACHE_TTL:
            return _apply_edits(tid, data)
    data = assemblyai_get(f"/v2/transcript/{tid}")
    transcript_cache[tid] = (data, now)
    return _apply_edits(tid, data)


def _apply_edits(tid: str, data: dict) -> dict:
    """Apply user edits from edit_cache over transcript data."""
    edits = edit_cache.get(tid)
    if not edits:
        return data
    patched = dict(data)
    if edits.get("utterances") and patched.get("utterances"):
        edited_utts = edits["utterances"]
        orig_utts = list(patched["utterances"])
        for i, eu in enumerate(edited_utts):
            if i < len(orig_utts) and eu.get("text") is not None:
                orig_utts[i] = dict(orig_utts[i])
                orig_utts[i]["text"] = eu["text"]
        patched["utterances"] = orig_utts
        patched["text"] = " ".join(u.get("text", "") for u in orig_utts)
    elif edits.get("text") is not None:
        patched["text"] = edits["text"]
    return patched


def upload(path: str) -> str:
    with open(path, "rb") as f:
        r = requests.post(f"{BASE_URL}/v2/upload", headers=UPLOAD_HEADERS, data=f)
    if r.status_code != 200:
        raise HTTPException(500, f"Upload failed: {r.text[:300]}")
    return r.json()["upload_url"]


def assemblyai_get(path: str) -> dict:
    r = requests.get(f"{BASE_URL}{path}", headers={"Authorization": API_KEY})
    if r.status_code != 200:
        raise HTTPException(500, f"AssemblyAI error: {r.text[:300]}")
    return r.json()


def assemblyai_get_text(path: str) -> str:
    r = requests.get(f"{BASE_URL}{path}", headers={"Authorization": API_KEY})
    if r.status_code != 200:
        raise HTTPException(500, f"AssemblyAI error: {r.text[:300]}")
    return r.text


def build_request(audio_url: str, cfg: dict) -> dict:
    req: dict = {
        "audio_url": audio_url,
        "speech_models": ["universal-2"],
    }

    # Language
    if cfg.get("language_detection"):
        req["language_detection"] = True
        lang_opts: dict = {}
        if cfg.get("code_switching"):
            lang_opts["code_switching"] = True
            if cfg.get("code_switching_languages"):
                lang_opts["expected_languages"] = cfg["code_switching_languages"]
                lang_opts["fallback_language"] = "auto"
        if cfg.get("language_confidence_threshold"):
            req["language_confidence_threshold"] = float(cfg["language_confidence_threshold"])
        if lang_opts:
            req["language_detection_options"] = lang_opts
    elif cfg.get("language_code"):
        req["language_code"] = cfg["language_code"]

    # Text formatting
    req["punctuate"] = bool(cfg.get("punctuate", True))
    req["format_text"] = bool(cfg.get("format_text", True))
    if cfg.get("disfluencies"):
        req["disfluencies"] = True
    if cfg.get("filter_profanity"):
        req["filter_profanity"] = True
    if cfg.get("remove_audio_tags"):
        req["remove_audio_tags"] = "all"

    # Speaker diarization
    if cfg.get("speaker_labels"):
        req["speaker_labels"] = True
        if cfg.get("speakers_expected"):
            n = int(cfg["speakers_expected"])
            req["speaker_options"] = {
                "min_speakers_expected": max(1, n - 1),
                "max_speakers_expected": n + 1,
            }

    # Multichannel
    if cfg.get("multichannel"):
        req["multichannel"] = True

    # PII
    if cfg.get("redact_pii") and cfg.get("redact_pii_policies"):
        req["redact_pii"] = True
        req["redact_pii_policies"] = cfg["redact_pii_policies"]
        req["redact_pii_sub"] = cfg.get("redact_pii_sub", "entity_name")
        if cfg.get("redact_pii_audio"):
            req["redact_pii_audio"] = True
            req["redact_pii_audio_quality"] = cfg.get("redact_pii_audio_quality", "mp3")
            if cfg.get("redact_pii_audio_method") == "silence":
                req["redact_pii_audio_options"] = {
                    "override_audio_redaction_method": "silence"
                }

    # Intelligence (EN)
    if cfg.get("entity_detection"):
        req["entity_detection"] = True
    if cfg.get("sentiment_analysis"):
        req["sentiment_analysis"] = True
    if cfg.get("iab_categories"):
        req["iab_categories"] = True
    if cfg.get("content_safety"):
        req["content_safety"] = True
        if cfg.get("content_safety_confidence"):
            req["content_safety_confidence"] = int(cfg["content_safety_confidence"])
    if cfg.get("auto_highlights"):
        req["auto_highlights"] = True

    # Medical
    if cfg.get("medical_mode"):
        req["domain"] = "medical-v1"

    # Vocabulary
    if cfg.get("keyterms_prompt"):
        req["keyterms_prompt"] = cfg["keyterms_prompt"]
    if cfg.get("custom_spelling"):
        req["custom_spelling"] = cfg["custom_spelling"]

    # Audio trim
    if cfg.get("audio_start_from"):
        req["audio_start_from"] = int(cfg["audio_start_from"])
    if cfg.get("audio_end_at"):
        req["audio_end_at"] = int(cfg["audio_end_at"])
    if cfg.get("speech_threshold"):
        req["speech_threshold"] = float(cfg["speech_threshold"])

    # Webhook
    if cfg.get("webhook_url"):
        req["webhook_url"] = cfg["webhook_url"]

    # speech_understanding block
    su: dict = {}

    if cfg.get("translation_languages"):
        su["translation"] = {
            "target_languages": cfg["translation_languages"],
            "formal": bool(cfg.get("translation_formal", False)),
            "match_original_utterance": bool(cfg.get("translation_utterance", False)),
        }

    if cfg.get("speaker_identification") and cfg.get("speaker_labels"):
        spk_id: dict = {
            "speaker_type": cfg.get("speaker_type", "name"),
        }
        known = [v.strip() for v in cfg.get("speaker_known_values", []) if v.strip()]
        if known:
            spk_id["known_values"] = known
        su["speaker_identification"] = spk_id

    fmt: dict = {}
    if cfg.get("date_format"):
        fmt["date"] = cfg["date_format"]
    if cfg.get("phone_format"):
        fmt["phone_number"] = cfg["phone_format"]
    if cfg.get("email_format"):
        fmt["email"] = cfg["email_format"]
    if fmt:
        su["custom_formatting"] = fmt

    if su:
        req["speech_understanding"] = {"request": su}

    return req
