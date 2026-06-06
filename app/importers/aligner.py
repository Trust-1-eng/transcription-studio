import re
from difflib import SequenceMatcher


# ─────────────────────────────────────────────
# Contraction mappings
# ─────────────────────────────────────────────
_CONTRACTIONS_RAW = {
    "i'm": "i am", "i'll": "i will", "i've": "i have", "i'd": "i would",
    "you're": "you are", "you'll": "you will", "you've": "you have", "you'd": "you would",
    "he's": "he is", "he'll": "he will", "he'd": "he would",
    "she's": "she is", "she'll": "she will", "she'd": "she would",
    "it's": "it is", "it'll": "it will",
    "we're": "we are", "we'll": "we will", "we've": "we have", "we'd": "we would",
    "they're": "they are", "they'll": "they will", "they've": "they have", "they'd": "they would",
    "that's": "that is", "that'll": "that will",
    "who's": "who is", "who'll": "who will",
    "what's": "what is", "what'll": "what will",
    "where's": "where is", "there's": "there is",
    "here's": "here is", "how's": "how is",
    "isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "won't": "will not", "wouldn't": "would not",
    "can't": "cannot", "couldn't": "could not",
    "shouldn't": "should not", "mustn't": "must not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "let's": "let us",
    "gonna": "going to", "wanna": "want to", "gotta": "got to",
}

# Build lookup keyed by NORMALIZED form (no apostrophe): "im" -> "i am", "dont" -> "do not"
CONTRACTIONS = {}
for contr, expanded in _CONTRACTIONS_RAW.items():
    normalized_key = re.sub(r"[^\w]", "", contr.lower())
    CONTRACTIONS[normalized_key] = expanded


# ─────────────────────────────────────────────
# Non-speech pattern (skip in alignment)
# ─────────────────────────────────────────────
NON_SPEECH_RE = re.compile(
    r"^\[.*\]$"           # [MUSIC], [APPLAUSE], [inaudible], [00:01:23]
    r"|^\(.*\)$"          # (pause), (laughter)
    r"|^\d+\.$"           # "1.", "2." — section numbers
    r"|^#{1,6}$"          # markdown headers
)


def is_non_speech(word: str) -> bool:
    return bool(NON_SPEECH_RE.match(word))


def normalize_word(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower())


def word_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    na, nb = normalize_word(a), normalize_word(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 0.95

    # Check contraction equivalence: "I'm" == "I" (first word of expansion)
    a_expanded = CONTRACTIONS.get(na, "")
    b_expanded = CONTRACTIONS.get(nb, "")
    if a_expanded and a_expanded.split()[0] == nb:
        return 0.85
    if b_expanded and b_expanded.split()[0] == na:
        return 0.85

    len_ratio = min(len(na), len(nb)) / max(len(na), len(nb))
    if (na.startswith(nb) or nb.startswith(na)) and len_ratio >= 0.6:
        return 0.7 * len_ratio

    ratio = SequenceMatcher(None, na, nb).ratio()
    if min(len(na), len(nb)) <= 3 and len_ratio < 0.7:
        ratio *= len_ratio
    return ratio


def _expand_contractions(tokens: list) -> list:
    """Expand contractions in token list for better matching.
    Returns new list with expanded tokens, tracking original indices."""
    result = []
    for i, token in enumerate(tokens):
        normalized = normalize_word(token)
        if normalized in CONTRACTIONS:
            expanded = CONTRACTIONS[normalized].split()
            for ew in expanded:
                result.append({"text": token if len(expanded) == 1 else ew, "orig_idx": i, "is_expansion": True})
        else:
            result.append({"text": token, "orig_idx": i, "is_expansion": False})
    return result


def _find_anchor(edited_tokens: list, ei: int, aai_words: list, search_start: int,
                  anchor_len: int = 3, scan_ahead: int = 20, max_aai_search: int = 50) -> int:
    """Find a sequence of anchor_len consecutive matching words.
    Scans edited_tokens[ei:ei+scan_ahead] trying each as a potential anchor start.
    Limits AAI search to max_aai_search words ahead to avoid jumping to wrong repeat."""
    aai_search_end = min(search_start + max_aai_search, len(aai_words) - anchor_len + 1)
    for look in range(min(scan_ahead, len(edited_tokens) - ei)):
        if ei + look + anchor_len > len(edited_tokens):
            break
        if is_non_speech(edited_tokens[ei + look]):
            continue
        for aj in range(search_start, aai_search_end):
            all_match = True
            for offset in range(anchor_len):
                if word_similarity(edited_tokens[ei + look + offset], aai_words[aj + offset].get("text", "")) < 0.6:
                    all_match = False
                    break
            if all_match:
                if look == 0:
                    return aj
                return -1
    return -1


def align_texts(edited_text: str, aai_words: list, max_gap: int = 10) -> list:
    """
    Align edited transcript text to AssemblyAI word-level timestamps.

    Features:
    - Greedy forward-walk with lookahead window
    - Anchor recovery for large insertions and reordered sections
    - Contraction handling (I'm ↔ I am)
    - Non-speech token skipping ([MUSIC], [00:01:23])
    - Multi-word contraction expansion for better matching

    Returns list of dicts: {"text": str, "start": int, "end": int, "matched": bool}
    """
    edited_tokens = edited_text.split()
    if not edited_tokens or not aai_words:
        return []

    # Pre-process: expand contractions in AAI words for matching
    aai_expanded = []
    for w in aai_words:
        na = normalize_word(w.get("text", ""))
        if na in CONTRACTIONS:
            parts = CONTRACTIONS[na].split()
            share = (w["end"] - w["start"]) / len(parts)
            for pi, part in enumerate(parts):
                aai_expanded.append({
                    "text": part,
                    "start": int(w["start"] + share * pi),
                    "end": int(w["start"] + share * (pi + 1)),
                    "orig_text": w.get("text", ""),
                })
        else:
            aai_expanded.append(w)

    # Also expand contractions in edited tokens
    edited_expanded = []
    edited_orig_map = []  # maps expanded index -> original token index
    for oi, token in enumerate(edited_tokens):
        na = normalize_word(token)
        if na in CONTRACTIONS:
            parts = CONTRACTIONS[na].split()
            for part in parts:
                edited_expanded.append(part)
                edited_orig_map.append(oi)
        else:
            edited_expanded.append(token)
            edited_orig_map.append(oi)

    # Run alignment on expanded sequences
    aligned_expanded = _align_core(edited_expanded, aai_expanded, max_gap)

    # Collapse back to original tokens
    aligned = []
    i = 0
    while i < len(aligned_expanded):
        orig_idx = edited_orig_map[i]
        orig_token = edited_tokens[orig_idx]

        # Collect all expanded entries for this original token
        group = [aligned_expanded[i]]
        i += 1
        while i < len(aligned_expanded) and edited_orig_map[i] == orig_idx:
            group.append(aligned_expanded[i])
            i += 1

        any_matched = any(g["matched"] for g in group)
        if any_matched:
            starts = [g["start"] for g in group if g["matched"]]
            ends = [g["end"] for g in group if g["matched"]]
            aligned.append({
                "text": orig_token,
                "start": min(starts),
                "end": max(ends),
                "matched": True,
            })
        else:
            aligned.append({
                "text": orig_token,
                "start": -1,
                "end": -1,
                "matched": False,
            })

    _interpolate_unmatched(aligned)
    return aligned


def _align_core(edited_tokens: list, aai_words: list, max_gap: int) -> list:
    """Core greedy forward-walk alignment."""
    aligned = []
    j = 0
    consecutive_misses = 0

    for i, edited_word in enumerate(edited_tokens):
        # Skip non-speech tokens
        if is_non_speech(edited_word):
            aligned.append({"text": edited_word, "start": -1, "end": -1, "matched": False})
            continue

        best_score = 0.0
        best_k = -1

        window_end = min(j + max_gap, len(aai_words))
        for k in range(j, window_end):
            score = word_similarity(edited_word, aai_words[k].get("text", ""))
            if score > best_score:
                best_score = score
                best_k = k

        if best_score >= 0.6 and best_k >= 0:
            w = aai_words[best_k]
            aligned.append({
                "text": edited_word,
                "start": w.get("start", 0),
                "end": w.get("end", 0),
                "matched": True,
            })
            j = best_k + 1
            consecutive_misses = 0
        else:
            if consecutive_misses >= 2:
                anchor_j = _find_anchor(edited_tokens, i, aai_words, j)
                if anchor_j >= 0:
                    w = aai_words[anchor_j]
                    aligned.append({
                        "text": edited_word,
                        "start": w.get("start", 0),
                        "end": w.get("end", 0),
                        "matched": True,
                    })
                    j = anchor_j + 1
                    consecutive_misses = 0
                    continue

            aligned.append({"text": edited_word, "start": -1, "end": -1, "matched": False})
            consecutive_misses += 1

    return aligned


def _interpolate_unmatched(aligned: list):
    """Fill in timestamps for unmatched words by interpolating from neighbors."""
    n = len(aligned)
    for i in range(n):
        if aligned[i]["matched"]:
            continue
        prev_end = 0
        prev_idx = i
        for p in range(i - 1, -1, -1):
            if aligned[p]["matched"]:
                prev_end = aligned[p]["end"]
                prev_idx = p
                break
        next_start = prev_end
        next_idx = i
        for q in range(i + 1, n):
            if aligned[q]["matched"]:
                next_start = aligned[q]["start"]
                next_idx = q
                break
        else:
            next_start = prev_end + 500
            next_idx = n

        span = next_idx - prev_idx
        if span <= 0:
            span = 1
        step = (next_start - prev_end) / span
        pos = i - prev_idx
        aligned[i]["start"] = int(prev_end + step * pos)
        aligned[i]["end"] = int(prev_end + step * (pos + 1))


def _is_break_point(word_text: str) -> bool:
    """Check if a word is a natural break point for subtitle splitting."""
    return bool(re.search(r"[.!?,;:\-\u2014]$", word_text))


def _flush_cue(cues: list, current_words: list, current_start: int):
    if current_words:
        cues.append({
            "start": current_start,
            "end": current_words[-1]["end"],
            "text": " ".join(cw["text"] for cw in current_words),
        })


def build_vtt_cues(
    aligned_words: list,
    max_chars_per_line: int = 42,
    max_lines: int = 2,
    max_cue_duration_ms: int = 7000,
) -> list:
    """Group aligned words into subtitle cues.
    Splits at sentence boundaries first, then at commas/natural pauses,
    falls back to character limit only when no break point is found."""
    if not aligned_words:
        return []

    max_chars = max_chars_per_line * max_lines
    cues = []
    current_words = []
    current_start = aligned_words[0]["start"]
    current_len = 0
    # Track last break point within current cue for fallback splitting
    last_break_idx = -1

    for w in aligned_words:
        word_text = w["text"]
        new_len = current_len + len(word_text) + (1 if current_words else 0)
        duration = w["end"] - current_start if current_words else 0

        is_sentence_end = bool(re.search(r"[.!?]$", word_text))
        too_long = new_len > max_chars
        too_slow = duration > max_cue_duration_ms

        if current_words and too_long:
            # Must split — try at last break point, otherwise split here
            if last_break_idx >= 0:
                split_words = current_words[:last_break_idx + 1]
                remain_words = current_words[last_break_idx + 1:]
                _flush_cue(cues, split_words, current_start)
                current_words = remain_words + [w]
                current_start = remain_words[0]["start"] if remain_words else w["start"]
                current_len = sum(len(cw["text"]) for cw in current_words) + len(current_words) - 1
            else:
                _flush_cue(cues, current_words, current_start)
                current_words = [w]
                current_start = w["start"]
                current_len = len(word_text)
            last_break_idx = -1
        elif current_words and too_slow:
            # Duration exceeded — split at last break point if available
            if last_break_idx >= 0:
                split_words = current_words[:last_break_idx + 1]
                remain_words = current_words[last_break_idx + 1:]
                _flush_cue(cues, split_words, current_start)
                current_words = remain_words + [w]
                current_start = remain_words[0]["start"] if remain_words else w["start"]
                current_len = sum(len(cw["text"]) for cw in current_words) + len(current_words) - 1
            else:
                _flush_cue(cues, current_words, current_start)
                current_words = [w]
                current_start = w["start"]
                current_len = len(word_text)
            last_break_idx = -1
        else:
            current_words.append(w)
            current_len = new_len

            if _is_break_point(word_text):
                last_break_idx = len(current_words) - 1

            if is_sentence_end and current_len >= 20:
                _flush_cue(cues, current_words, current_start)
                current_words = []
                current_start = w["end"]
                current_len = 0
                last_break_idx = -1

    _flush_cue(cues, current_words, current_start)
    return cues
