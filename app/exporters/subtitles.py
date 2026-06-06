from app.utils import ms_to_srt, ms_to_vtt


def make_translation_srt(translation: dict) -> str:
    utterances = translation.get("utterances") or []
    if not utterances:
        return ""
    parts = []
    for i, u in enumerate(utterances, 1):
        start = ms_to_srt(u.get("start", 0))
        end = ms_to_srt(u.get("end", 0))
        parts.append(f"{i}\n{start} --> {end}\n{u.get('text', '')}\n")
    return "\n".join(parts)


def make_translation_vtt(translation: dict) -> str:
    utterances = translation.get("utterances") or []
    if not utterances:
        return ""
    lines = ["WEBVTT\n"]
    for u in utterances:
        start = ms_to_vtt(u.get("start", 0))
        end = ms_to_vtt(u.get("end", 0))
        lines.append(f"{start} --> {end}\n{u.get('text', '')}\n")
    return "\n".join(lines)


def make_aligned_srt(cues: list) -> str:
    if not cues:
        return ""
    parts = []
    for i, c in enumerate(cues, 1):
        start = ms_to_srt(c.get("start", 0))
        end = ms_to_srt(c.get("end", 0))
        parts.append(f"{i}\n{start} --> {end}\n{c.get('text', '')}\n")
    return "\n".join(parts)


def make_aligned_vtt(cues: list) -> str:
    if not cues:
        return ""
    lines = ["WEBVTT\n"]
    for c in cues:
        start = ms_to_vtt(c.get("start", 0))
        end = ms_to_vtt(c.get("end", 0))
        lines.append(f"{start} --> {end}\n{c.get('text', '')}\n")
    return "\n".join(lines)


def get_translation_results(data: dict) -> dict:
    """Extract translation results from API response.
    Collects both top-level translated_texts AND per-utterance translations."""
    result = {}

    # 1. Top-level translated_texts (full text)
    tt = data.get("translated_texts")
    if isinstance(tt, list):
        for item in tt:
            lang = item.get("language")
            if lang:
                result[lang] = item
    elif isinstance(tt, dict):
        for lang, val in tt.items():
            result[lang] = {"text": val} if isinstance(val, str) else val

    # 2. Per-utterance translations from utterances[].translated_texts
    for u in data.get("utterances") or []:
        utt_trans = u.get("translated_texts")
        if not isinstance(utt_trans, dict):
            continue
        for lang, text in utt_trans.items():
            if lang not in result:
                result[lang] = {"text": ""}
            if "utterances" not in result[lang]:
                result[lang]["utterances"] = []
            result[lang]["utterances"].append({
                "text": text,
                "start": u.get("start"),
                "end": u.get("end"),
                "speaker": u.get("speaker"),
            })

    return result
