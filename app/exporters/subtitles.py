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


def get_translation_results(data: dict) -> dict:
    """Extract translation results from API response."""
    tt = data.get("translated_texts")
    if not tt:
        return {}
    
    result = {}
    # AssemblyAI can return translated_texts as a list of objects or a dict
    if isinstance(tt, list):
        for item in tt:
            lang = item.get("language")
            if lang:
                result[lang] = item
    elif isinstance(tt, dict):
        for lang, val in tt.items():
            result[lang] = {"text": val} if isinstance(val, str) else val
            
    return result
