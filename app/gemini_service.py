import json
import time
from datetime import datetime

import requests

from app.config import GEMINI_API_KEY, GEMINI_URL, GEMINI_CACHE_TTL
from app.dependencies import gemini_cache

_LANG_FULL = {
    "en": "English", "uk": "Ukrainian", "ru": "Russian", "de": "German",
    "fr": "French", "es": "Spanish", "it": "Italian", "pt": "Portuguese",
    "pl": "Polish", "nl": "Dutch", "ja": "Japanese", "zh": "Chinese",
    "ko": "Korean", "ar": "Arabic", "tr": "Turkish",
}


def gemini_analyze(text: str, language: str, has_speakers: bool, speaker_labels: list = None, opts: dict = None) -> dict:
    """Call Gemini Flash once with bundled analysis prompt. Returns dict or {error:...}."""
    if not GEMINI_API_KEY:
        return {"error": "Gemini not configured"}

    if opts is None:
        opts = {}
    want_summary = opts.get("summary", True)
    want_notes = opts.get("notes", False)
    want_speakers = opts.get("speakers", True)

    lang_name = _LANG_FULL.get(language, "English")

    if len(text) > 10000:
        text = text[:5000] + "\n...\n" + text[-5000:]

    # Build JSON schema dynamically based on options
    fields = []
    rules = []

    fields.append(f'"title": "Short professional title (max 8 words) in {lang_name}"')

    if want_summary:
        fields.append(f'"summary": "2-3 sentence summary in {lang_name}"')

    if want_notes:
        fields.append(f'"notes": ["Detailed point 1 in {lang_name}", "Detailed point 2", ...up to 15]')
        rules.append(f"notes: 8-15 detailed bullet points covering all key ideas, arguments, and conclusions in {lang_name}. Each point should be a complete thought, not just a keyword.")

    fields.append('"topics": ["keyword1", "keyword2", ...up to 8]')
    fields.append(f'"sentiment": {{"overall": "POSITIVE|NEGATIVE|NEUTRAL|MIXED", "score": <-1.0 to 1.0>, "details": "1 sentence in {lang_name}"}}')
    fields.append(f'"key_moments": [{{"text": "exact quote", "reason": "why important, in {lang_name}"}}]')

    speakers_rule = ""
    if want_speakers and has_speakers:
        if speaker_labels:
            labels_example = ", ".join(f'"{lbl}": {{"name": "Full name in {lang_name}", "role": "Role or description in {lang_name}"}}' for lbl in speaker_labels[:6])
            fields.append(f'"speakers": {{{labels_example}}}')
            speakers_rule = f"\n- speakers: map each speaker label key to an object with 'name' (full name written in {lang_name} script) and 'role'. Use the EXACT label keys provided."
        else:
            fields.append(f'"speakers": {{"Speaker A": {{"name": "Full name in {lang_name}", "role": "Role in {lang_name}"}}}}')
            speakers_rule = f"\n- speakers: map speaker labels to objects with 'name' (full name in {lang_name} script) and 'role'."

    fields_str = ",\n  ".join(fields)
    rules_str = ", ".join(["topics 5-8 keywords", "key_moments max 3", f"all text in {lang_name}"])
    if rules:
        rules_str += "\n- " + "\n- ".join(rules)

    prompt = (
        f"You are a transcript analyst. Analyze this {lang_name} transcript. Return ONLY valid JSON:\n"
        "{\n"
        f"  {fields_str}\n"
        "}\n"
        f"Rules: {rules_str}{speakers_rule}\n\n"
        f"TRANSCRIPT:\n{text}"
    )

    max_tokens = 4096 if want_notes else 2048

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    for attempt in range(2):
        try:
            r = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=45,
            )
            if r.status_code == 429 or r.status_code >= 500:
                if attempt == 0:
                    time.sleep(2)
                    continue
                return {"error": f"Gemini {r.status_code}"}
            if r.status_code != 200:
                return {"error": f"Gemini error {r.status_code}: {r.text[:200]}"}

            resp = r.json()
            text_out = resp["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text_out)

        except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
            if attempt == 0:
                time.sleep(1)
                continue
            return {"error": str(e)[:200]}

    return {"error": "Gemini failed after retries"}


def get_gemini_cached(tid: str, text: str, language: str, has_speakers: bool, speaker_labels: list = None, opts: dict = None) -> dict:
    cache_key = f"{tid}:{hash(json.dumps(opts or {}, sort_keys=True))}"
    now = datetime.now().timestamp()
    if cache_key in gemini_cache:
        data, ts = gemini_cache[cache_key]
        if now - ts < GEMINI_CACHE_TTL:
            return data
    result = gemini_analyze(text, language, has_speakers, speaker_labels, opts)
    gemini_cache[cache_key] = (result, now)
    return result
