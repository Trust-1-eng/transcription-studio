import re
from datetime import datetime
from urllib.parse import quote

from app.dependencies import gemini_cache

# Localized labels for document header
HEADER_LABELS = {
    "ru": {"title": "СТЕНОГРАММА", "date": "Дата", "duration": "Длительность", "lang": "Язык", "speakers": "Спикеры"},
    "uk": {"title": "СТЕНОГРАМА", "date": "Дата", "duration": "Тривалість", "lang": "Мова", "speakers": "Спікери"},
}
HEADER_DEFAULT = {"title": "TRANSCRIPT", "date": "Date", "duration": "Duration", "lang": "Language", "speakers": "Speakers"}


def make_doc_header(data: dict) -> dict:
    """Build document header metadata from transcript data."""
    duration_ms = data.get("audio_duration", 0)
    if isinstance(duration_ms, (int, float)) and duration_ms > 0:
        total_sec = int(duration_ms)
        h, rem = divmod(total_sec, 3600)
        m, s = divmod(rem, 60)
        duration_str = f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"
    else:
        duration_str = "—"

    lang = data.get("language_code", "")
    _lang_names = {
        "en": "English", "uk": "Українська", "ru": "Русский", "de": "Deutsch",
        "fr": "Français", "es": "Español", "it": "Italiano", "pt": "Português",
        "pl": "Polski", "nl": "Nederlands", "ja": "日本語", "zh": "中文",
        "ko": "한국어", "ar": "العربية", "tr": "Türkçe", "cs": "Čeština",
        "sv": "Svenska", "da": "Dansk", "fi": "Suomi", "no": "Norsk",
    }
    lang_name = _lang_names.get(lang, lang.upper() if lang else "—")

    speakers = set()
    for u in (data.get("utterances") or []):
        if u.get("speaker"):
            speakers.add(u["speaker"])

    labels = HEADER_LABELS.get(lang, HEADER_DEFAULT)

    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "duration": duration_str,
        "language": lang_name,
        "speakers": len(speakers),
        "transcript_id": data.get("id", ""),
        "labels": labels,
    }


def resolve_speakers(data: dict, gdata: dict = None) -> tuple:
    """Resolve raw AssemblyAI speaker labels to clean display names.
    Returns (label_map: dict, unique_count: int).
    """
    raw_labels = set()
    for u in (data.get("utterances") or []):
        if u.get("speaker"):
            raw_labels.add(u["speaker"])
    if not raw_labels:
        return {}, 0

    label_map: dict = {}

    # Source 1: AssemblyAI speaker_identification mapping (A->Name)
    aai_mapping = (data.get("speech_understanding", {})
                   .get("response", {})
                   .get("speaker_identification", {})
                   .get("mapping", {}))

    # Source 2: Gemini speakers (Speaker A->Name or raw_label->Name)
    # Supports both old format (string) and new format ({"name": ..., "role": ...})
    gem_speakers_raw = gdata.get("speakers", {}) if gdata else {}
    gem_speakers = {}
    for k, v in gem_speakers_raw.items():
        if isinstance(v, dict):
            gem_speakers[k] = v.get("name", k)
        else:
            gem_speakers[k] = v

    for raw in raw_labels:
        if raw in gem_speakers:
            label_map[raw] = gem_speakers[raw]
            continue

        stripped = re.sub(r'\s*-\s*\d+$', '', raw)

        if len(raw) == 1 and raw in aai_mapping:
            label_map[raw] = aai_mapping[raw]
            continue

        if stripped != raw:
            label_map[raw] = stripped
            continue

        if len(raw) <= 2 and raw.isalpha():
            gem_key = f"Speaker {raw}"
            if gem_key in gem_speakers:
                label_map[raw] = gem_speakers[gem_key]
                continue

        label_map[raw] = raw

    unique_count = len(set(label_map.values()))
    return label_map, unique_count


def dl_headers(filename: str) -> dict:
    safe = quote(filename, safe="")
    return {
        "Content-Disposition": f"attachment; filename=\"{safe}\"; filename*=UTF-8''{safe}"
    }


def gemini_filename(tid: str, ext: str, use_gemini: bool = True) -> str:
    """Build filename: Gemini title -> original filename -> transcript ID.
    If use_gemini=False, skip Gemini title and prefer original filename."""
    from app.dependencies import filename_cache
    if use_gemini:
        gc = gemini_cache.get(tid)
        if gc and not gc[0].get("error") and gc[0].get("title"):
            title = gc[0]["title"]
            safe = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            if safe:
                return f"{safe[:80]}.{ext}"
    orig = filename_cache.get(tid)
    if orig:
        # Strip original extension, use new ext
        base = orig.rsplit(".", 1)[0] if "." in orig else orig
        safe = "".join(c for c in base if c.isalnum() or c in " -_").strip()
        if safe:
            return f"{safe[:80]}.{ext}"
    return f"transcript_{tid[:8]}.{ext}"
