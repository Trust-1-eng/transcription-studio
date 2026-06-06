import csv
import io

from app.utils import ms_to_readable, ms_to_srt
from app.dependencies import gemini_cache
from app.exporters.helpers import make_doc_header, resolve_speakers


def make_txt(data: dict, include_header: bool = True, label_map: dict = None, speaker_count: int = None) -> str:
    lines = []
    tid = data.get("id", "")
    gemini = gemini_cache.get(tid)
    gdata = gemini[0] if gemini and not gemini[0].get("error") else {}
    if label_map is None:
        label_map, speaker_count = resolve_speakers(data, gdata)

    if include_header:
        hdr = make_doc_header(data)
        if speaker_count is not None:
            hdr["speakers"] = speaker_count
        lb = hdr["labels"]
        lines.append(f"{'='*60}")
        lines.append(f"  {gdata.get('title', lb['title'])}")
        lines.append(f"  {lb['date']}: {hdr['date']}  |  {lb['duration']}: {hdr['duration']}  |  {lb['lang']}: {hdr['language']}")
        if hdr["speakers"]:
            lines.append(f"  {lb['speakers']}: {hdr['speakers']}")
        if gdata.get("summary"):
            lines.append(f"  {gdata['summary']}")
        lines.append(f"{'='*60}\n")

    if data.get("utterances"):
        for u in data["utterances"]:
            ts = ms_to_readable(u.get("start", 0))
            spk = label_map.get(u.get("speaker", ""), u.get("speaker", "Speaker"))
            lines.append(f"[{ts}] {spk}: {u.get('text', '')}\n")
        return "\n".join(lines)

    lines.append(data.get("text", ""))
    return "\n".join(lines)


PAUSE_THRESHOLD_MS = 3000  # 3+ seconds gap = (пауза)
LONG_PAUSE_THRESHOLD_MS = 8000  # 8+ seconds = (довга пауза)


def make_verbatim_txt(data: dict, label_map: dict = None, speaker_count: int = None) -> str:
    lines = []
    tid = data.get("id", "")
    gemini = gemini_cache.get(tid)
    gdata = gemini[0] if gemini and not gemini[0].get("error") else {}
    if label_map is None:
        label_map, speaker_count = resolve_speakers(data, gdata)

    utterances = data.get("utterances", [])
    if not utterances:
        lines.append(data.get("text", ""))
        return "\n".join(lines)

    for i, u in enumerate(utterances):
        ts = ms_to_readable(u.get("start", 0))
        spk = label_map.get(u.get("speaker", ""), u.get("speaker", "Speaker"))
        text = u.get("text", "")

        # Check for pause before this utterance
        if i > 0:
            prev = utterances[i - 1]
            gap = u.get("start", 0) - prev.get("end", prev.get("start", 0))
            if gap >= LONG_PAUSE_THRESHOLD_MS:
                lines.append(f"    (довга пауза — {gap / 1000:.0f} сек)\n")
            elif gap >= PAUSE_THRESHOLD_MS:
                lines.append(f"    (пауза — {gap / 1000:.0f} сек)\n")

            # Check for interruption (overlap)
            if gap < -200:  # > 200ms overlap = real interruption, not just timing noise
                lines.append(f"    (перебив)\n")

        lines.append(f"[{ts}] {spk}: {text}\n")

    return "\n".join(lines)


def make_bilingual_txt(data: dict, translation: dict, label_map: dict = None, speaker_count: int = None) -> str:
    lines = []
    tid = data.get("id", "")
    gemini = gemini_cache.get(tid)
    gdata = gemini[0] if gemini and not gemini[0].get("error") else {}
    if label_map is None:
        label_map, speaker_count = resolve_speakers(data, gdata)

    orig_utts = data.get("utterances", [])
    trans_utts = translation.get("utterances", [])

    if orig_utts and trans_utts:
        # Match by index — AssemblyAI aligns translation utterances with originals
        for i, u in enumerate(orig_utts):
            ts = ms_to_readable(u.get("start", 0))
            spk = label_map.get(u.get("speaker", ""), u.get("speaker", "Speaker"))
            lines.append(f"[{ts}] {spk}: {u.get('text', '')}")
            if i < len(trans_utts):
                lines.append(f"       \u2192 {trans_utts[i].get('text', '')}")
            lines.append("")
    elif orig_utts:
        trans_text = translation.get("text", "")
        lines.append(f"--- ОРИГІНАЛ ---\n")
        for u in orig_utts:
            ts = ms_to_readable(u.get("start", 0))
            spk = label_map.get(u.get("speaker", ""), u.get("speaker", "Speaker"))
            lines.append(f"[{ts}] {spk}: {u.get('text', '')}")
        lines.append(f"\n{'='*60}")
        lines.append(f"--- ПЕРЕКЛАД ---\n")
        if trans_text:
            lines.append(trans_text)
        else:
            lines.append("(Текст перекладу недоступний)")
    else:
        orig_text = data.get("text", "")
        trans_text = translation.get("text", "")
        lines.append(f"--- ОРИГІНАЛ ---\n")
        lines.append(orig_text)
        lines.append(f"\n{'='*60}")
        lines.append(f"--- ПЕРЕКЛАД ---\n")
        if trans_text:
            lines.append(trans_text)
        else:
            lines.append("(Текст перекладу недоступний)")

    return "\n".join(lines)


def make_literary_txt(data: dict, label_map: dict = None, speaker_count: int = None) -> str:
    lines = []
    tid = data.get("id", "")
    gemini = gemini_cache.get(tid)
    gdata = gemini[0] if gemini and not gemini[0].get("error") else {}
    if label_map is None:
        label_map, speaker_count = resolve_speakers(data, gdata)

    if data.get("utterances"):
        prev_speaker = None
        for u in data["utterances"]:
            spk = label_map.get(u.get("speaker", ""), u.get("speaker", ""))
            text = u.get("text", "")
            if spk and spk != prev_speaker:
                lines.append(f"\u2014 {spk}: {text}\n")
            else:
                lines.append(f"\u2014 {text}\n")
            prev_speaker = spk
        return "\n".join(lines)

    lines.append(data.get("text", ""))
    return "\n".join(lines)


def make_paragraphs_txt(paragraphs: list) -> str:
    return "\n\n".join(p.get("text", "") for p in paragraphs)


def make_sentences_txt(sentences: list) -> str:
    lines = []
    for s in sentences:
        ts = ms_to_readable(s.get("start", 0))
        lines.append(f"[{ts}] {s.get('text', '')}")
    return "\n".join(lines)


def make_sentences_srt(sentences: list) -> str:
    parts = []
    for i, s in enumerate(sentences, 1):
        start = ms_to_srt(s.get("start", 0))
        end = ms_to_srt(s.get("end", 0))
        parts.append(f"{i}\n{start} --> {end}\n{s.get('text', '')}\n")
    return "\n".join(parts)


def make_sentences_csv(sentences: list) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["index", "start_ms", "end_ms", "time", "text", "confidence"])
    for i, s in enumerate(sentences, 1):
        w.writerow([
            i,
            s.get("start", 0),
            s.get("end", 0),
            ms_to_readable(s.get("start", 0)),
            s.get("text", ""),
            round(s.get("confidence", 0), 4),
        ])
    return buf.getvalue()


def make_words_csv(words: list) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["index", "start_ms", "end_ms", "time", "word", "confidence", "speaker"])
    for i, wd in enumerate(words, 1):
        w.writerow([
            i,
            wd.get("start", 0),
            wd.get("end", 0),
            ms_to_readable(wd.get("start", 0)),
            wd.get("text", ""),
            round(wd.get("confidence", 0), 4),
            wd.get("speaker", ""),
        ])
    return buf.getvalue()
