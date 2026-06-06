import io
import csv
import json
import zipfile
from datetime import datetime

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from app.utils import ms_to_readable
from app.dependencies import gemini_cache
from app.assemblyai_client import get_transcript_cached, assemblyai_get, assemblyai_get_text
from app.exporters.helpers import (
    make_doc_header, resolve_speakers, dl_headers, gemini_filename, HEADER_DEFAULT,
)
from app.exporters.text import (
    make_txt, make_verbatim_txt, make_bilingual_txt, make_literary_txt,
    make_paragraphs_txt, make_sentences_txt, make_sentences_srt,
    make_sentences_csv, make_words_csv,
)
from app.exporters.document import (
    make_docx, make_verbatim_docx, make_bilingual_docx, make_interview_docx,
    make_literary_docx, make_paragraphs_docx,
)
from app.exporters.pdf import make_pdf
from app.exporters.table import make_table_docx, make_table_pdf
from app.exporters.subtitles import (
    make_translation_srt, make_translation_vtt, get_translation_results,
)

router = APIRouter()


def _fname(tid: str, ext: str, title_mode: str = None) -> str:
    """Build download filename. title_mode='file' skips Gemini title."""
    return gemini_filename(tid, ext, use_gemini=(title_mode != "file"))


@router.get("/api/export/{tid}/txt")
async def export_txt(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    text = make_txt(data)
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(_fname(tid, "txt", title)))


@router.get("/api/export/{tid}/docx")
async def export_docx(tid: str):
    data = get_transcript_cached(tid)
    content = make_docx(data)
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(_fname(tid, "docx", title)))


@router.get("/api/export/{tid}/pdf")
async def export_pdf(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    gemini = gemini_cache.get(tid)
    gdata = gemini[0] if gemini and not gemini[0].get("error") else {}
    label_map, speaker_count = resolve_speakers(data, gdata)
    hdr = make_doc_header(data)
    hdr["speakers"] = speaker_count
    content = make_pdf(data, gdata.get("title", "Transcript"), header_info=hdr,
                       gdata=gdata, label_map=label_map)
    return Response(content, media_type="application/pdf",
                    headers=dl_headers(_fname(tid, "pdf", title)))


@router.get("/api/export/{tid}/table/docx")
async def export_table_docx(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    content = make_table_docx(data)
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(_fname(tid, "docx", title)))


@router.get("/api/export/{tid}/table/pdf")
async def export_table_pdf(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    content = make_table_pdf(data)
    return Response(content, media_type="application/pdf",
                    headers=dl_headers(_fname(tid, "pdf", title)))


@router.get("/api/export/{tid}/literary/txt")
async def export_literary_txt(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    text = make_literary_txt(data)
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(_fname(tid, "txt", title)))


@router.get("/api/export/{tid}/literary/docx")
async def export_literary_docx(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    content = make_literary_docx(data)
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(_fname(tid, "docx", title)))


@router.get("/api/export/{tid}/bilingual/{lang}/txt")
async def export_bilingual_txt(tid: str, lang: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    translations = get_translation_results(data)
    lang_data = translations.get(lang, {})
    if not lang_data:
        raise HTTPException(404, f"No translation for language: {lang}")
    text = make_bilingual_txt(data, lang_data)
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(_fname(tid, "txt", title)))


@router.get("/api/export/{tid}/bilingual/{lang}/docx")
async def export_bilingual_docx(tid: str, lang: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    translations = get_translation_results(data)
    lang_data = translations.get(lang, {})
    if not lang_data:
        raise HTTPException(404, f"No translation for language: {lang}")
    content = make_bilingual_docx(data, lang_data)
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(_fname(tid, "docx", title)))


@router.get("/api/export/{tid}/interview/docx")
async def export_interview_docx(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    content = make_interview_docx(data)
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(_fname(tid, "docx", title)))


@router.get("/api/export/{tid}/verbatim/txt")
async def export_verbatim_txt(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    text = make_verbatim_txt(data)
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(_fname(tid, "txt", title)))


@router.get("/api/export/{tid}/verbatim/docx")
async def export_verbatim_docx(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    content = make_verbatim_docx(data)
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(_fname(tid, "docx", title)))


@router.get("/api/export/{tid}/md")
async def export_md(tid: str, title: str = Query(None)):
    data = get_transcript_cached(tid)
    gemini = gemini_cache.get(tid)
    gdata = gemini[0] if gemini and not gemini[0].get("error") else {}
    label_map, speaker_count = resolve_speakers(data, gdata)
    hdr = make_doc_header(data)
    hdr["speakers"] = speaker_count
    lb = hdr["labels"]

    lines = [f"# {gdata.get('title', lb['title'])}\n"]
    meta = f"> **{lb['date']}:** {hdr['date']} | **{lb['duration']}:** {hdr['duration']} | **{lb['lang']}:** {hdr['language']}"
    if hdr["speakers"]:
        meta += f" | **{lb['speakers']}:** {hdr['speakers']}"
    lines.append(meta)
    if gdata.get("summary"):
        lines.append(f"\n> *{gdata['summary']}*")
    lines.append(f"\n---\n")

    if data.get("utterances"):
        for u in data["utterances"]:
            ts = ms_to_readable(u.get("start", 0))
            spk = label_map.get(u.get("speaker", ""), u.get("speaker", "Speaker"))
            lines.append(f"**[{ts}] {spk}:** {u.get('text', '')}\n")
    else:
        lines.append(data.get("text", ""))

    content = "\n".join(lines)
    return Response(content.encode("utf-8"), media_type="text/markdown; charset=utf-8",
                    headers=dl_headers(_fname(tid, "md", title)))


@router.get("/api/export/{tid}/srt")
async def export_srt(tid: str, title: str = Query(None)):
    text = assemblyai_get_text(f"/v2/transcript/{tid}/srt")
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(_fname(tid, "srt", title)))


@router.get("/api/export/{tid}/vtt")
async def export_vtt(tid: str, title: str = Query(None)):
    text = assemblyai_get_text(f"/v2/transcript/{tid}/vtt")
    return Response(text.encode("utf-8"), media_type="text/vtt; charset=utf-8",
                    headers=dl_headers(_fname(tid, "vtt", title)))


# --- Paragraphs ---

@router.get("/api/export/{tid}/paragraphs/json")
async def export_paragraphs_json(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/paragraphs")
    content = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(content.encode("utf-8"), media_type="application/json",
                    headers=dl_headers(f"paragraphs_{tid}.json"))


@router.get("/api/export/{tid}/paragraphs/txt")
async def export_paragraphs_txt(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/paragraphs")
    text = make_paragraphs_txt(data.get("paragraphs", []))
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(f"paragraphs_{tid}.txt"))


@router.get("/api/export/{tid}/paragraphs/docx")
async def export_paragraphs_docx(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/paragraphs")
    content = make_paragraphs_docx(data.get("paragraphs", []))
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(f"paragraphs_{tid}.docx"))


@router.get("/api/export/{tid}/paragraphs/pdf")
async def export_paragraphs_pdf(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/paragraphs")
    text = make_paragraphs_txt(data.get("paragraphs", []))
    content = make_pdf(text, "Paragraphs")
    return Response(content, media_type="application/pdf",
                    headers=dl_headers(f"paragraphs_{tid}.pdf"))


@router.get("/api/export/{tid}/paragraphs/md")
async def export_paragraphs_md(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/paragraphs")
    paras = data.get("paragraphs", [])
    lines = ["# Paragraphs\n"]
    for p in paras:
        ts = ms_to_readable(p.get("start", 0))
        lines.append(f"*[{ts}]*\n\n{p.get('text', '')}\n")
    content = "\n".join(lines)
    return Response(content.encode("utf-8"), media_type="text/markdown; charset=utf-8",
                    headers=dl_headers(f"paragraphs_{tid}.md"))


# --- Sentences ---

@router.get("/api/export/{tid}/sentences/json")
async def export_sentences_json(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/sentences")
    content = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(content.encode("utf-8"), media_type="application/json",
                    headers=dl_headers(f"sentences_{tid}.json"))


@router.get("/api/export/{tid}/sentences/txt")
async def export_sentences_txt(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/sentences")
    text = make_sentences_txt(data.get("sentences", []))
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(f"sentences_{tid}.txt"))


@router.get("/api/export/{tid}/sentences/csv")
async def export_sentences_csv(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/sentences")
    text = make_sentences_csv(data.get("sentences", []))
    return Response(text.encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers=dl_headers(f"sentences_{tid}.csv"))


@router.get("/api/export/{tid}/sentences/srt")
async def export_sentences_srt(tid: str):
    data = assemblyai_get(f"/v2/transcript/{tid}/sentences")
    text = make_sentences_srt(data.get("sentences", []))
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(f"sentences_{tid}.srt"))


# --- Words ---

@router.get("/api/export/{tid}/words/json")
async def export_words_json(tid: str):
    data = get_transcript_cached(tid)
    content = json.dumps({"words": data.get("words", [])}, ensure_ascii=False, indent=2)
    return Response(content.encode("utf-8"), media_type="application/json",
                    headers=dl_headers(f"words_{tid}.json"))


@router.get("/api/export/{tid}/words/csv")
async def export_words_csv(tid: str):
    data = get_transcript_cached(tid)
    text = make_words_csv(data.get("words", []))
    return Response(text.encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers=dl_headers(f"words_{tid}.csv"))


# --- Translation ---

@router.get("/api/export/{tid}/translation/{lang}/txt")
async def export_translation_txt(tid: str, lang: str):
    data = get_transcript_cached(tid)
    translations = get_translation_results(data)
    lang_data = translations.get(lang, {})
    text = lang_data.get("text", "No translation available for this language.")
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(f"translation_{lang}_{tid}.txt"))


@router.get("/api/export/{tid}/translation/{lang}/docx")
async def export_translation_docx(tid: str, lang: str):
    data = get_transcript_cached(tid)
    translations = get_translation_results(data)
    lang_data = translations.get(lang, {})
    text = lang_data.get("text", "")
    fake_data = {"text": text}
    content = make_docx(fake_data, f"Translation ({lang.upper()})")
    return Response(content,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=dl_headers(f"translation_{lang}_{tid}.docx"))


@router.get("/api/export/{tid}/translation/{lang}/srt")
async def export_translation_srt(tid: str, lang: str):
    data = get_transcript_cached(tid)
    translations = get_translation_results(data)
    lang_data = translations.get(lang, {})
    text = make_translation_srt(lang_data)
    return Response(text.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(f"translation_{lang}_{tid}.srt"))


@router.get("/api/export/{tid}/translation/{lang}/vtt")
async def export_translation_vtt(tid: str, lang: str):
    data = get_transcript_cached(tid)
    translations = get_translation_results(data)
    lang_data = translations.get(lang, {})
    text = make_translation_vtt(lang_data)
    return Response(text.encode("utf-8"), media_type="text/vtt; charset=utf-8",
                    headers=dl_headers(f"translation_{lang}_{tid}.vtt"))


# --- Redacted audio ---

@router.get("/api/export/{tid}/redacted-audio")
async def export_redacted_audio(tid: str):
    data = get_transcript_cached(tid)
    audio_url = data.get("redacted_audio_url")
    if not audio_url:
        raise HTTPException(404, "No redacted audio available.")
    r = requests.get(audio_url, stream=True)
    fmt = data.get("redact_pii_audio_quality", "mp3")
    return Response(r.content, media_type=f"audio/{fmt}",
                    headers=dl_headers(f"redacted_{tid}.{fmt}"))


# --- Analytics (EN) ---

@router.get("/api/export/{tid}/entities/csv")
async def export_entities_csv(tid: str):
    data = get_transcript_cached(tid)
    entities = data.get("entities") or []
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["entity_type", "text", "start_ms", "end_ms", "time"])
    for e in entities:
        w.writerow([e.get("entity_type"), e.get("text"),
                    e.get("start"), e.get("end"),
                    ms_to_readable(e.get("start", 0))])
    return Response(buf.getvalue().encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers=dl_headers(f"entities_{tid}.csv"))


@router.get("/api/export/{tid}/sentiment/csv")
async def export_sentiment_csv(tid: str):
    data = get_transcript_cached(tid)
    results = data.get("sentiment_analysis_results") or []
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["index", "sentiment", "confidence", "start_ms", "end_ms", "text"])
    for i, s in enumerate(results, 1):
        w.writerow([i, s.get("sentiment"), round(s.get("confidence", 0), 4),
                    s.get("start"), s.get("end"), s.get("text")])
    return Response(buf.getvalue().encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers=dl_headers(f"sentiment_{tid}.csv"))


@router.get("/api/export/{tid}/topics/json")
async def export_topics_json(tid: str):
    data = get_transcript_cached(tid)
    content = json.dumps({"iab_categories_result": data.get("iab_categories_result", {})},
                         ensure_ascii=False, indent=2)
    return Response(content.encode("utf-8"), media_type="application/json",
                    headers=dl_headers(f"topics_{tid}.json"))


@router.get("/api/export/{tid}/highlights/txt")
async def export_highlights_txt(tid: str):
    data = get_transcript_cached(tid)
    results = (data.get("auto_highlights_result") or {}).get("results") or []
    lines = [f"{r.get('rank', 0):.0%}  {r.get('text', '')}" for r in
             sorted(results, key=lambda x: x.get("rank", 0), reverse=True)]
    content = "\n".join(lines)
    return Response(content.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(f"highlights_{tid}.txt"))


@router.get("/api/export/{tid}/summary/txt")
async def export_summary_txt(tid: str):
    data = get_transcript_cached(tid)
    from app.gemini_service import get_gemini_cached
    text = data.get("text", "")
    language = data.get("language_code", "en")
    has_speakers = bool(data.get("utterances"))
    spk_labels = list({u.get("speaker") for u in (data.get("utterances") or []) if u.get("speaker")})
    
    gdata = get_gemini_cached(tid, text, language, has_speakers, spk_labels if spk_labels else None)
    
    if gdata.get("error"):
        return Response("Summary not available.", media_type="text/plain; charset=utf-8")
        
    sum_lines = []
    title = gdata.get("title") or "AI Analysis"
    sum_lines.append(f"=== {title.upper()} ===\n")
    
    if gdata.get("summary"):
        sum_lines.append("--- КОНСПЕКТ / SUMMARY ---")
        sum_lines.append(gdata['summary'] + "\n")
    
    if gdata.get("chapters"):
        sum_lines.append("--- ОСНОВНІ МОМЕНТИ / CHAPTERS ---")
        for ch in gdata["chapters"]:
            ts = ms_to_readable(ch.get("start", 0))
            sum_lines.append(f"[{ts}] {ch.get('headline')}")
            if ch.get("summary"):
                sum_lines.append(f"   > {ch['summary']}")
        sum_lines.append("")

    if gdata.get("notes"):
        sum_lines.append("--- КОНСПЕКТ / NOTES ---")
        for note in gdata["notes"]:
            sum_lines.append(f"• {note}")
        sum_lines.append("")

    if gdata.get("topics"):
        sum_lines.append("--- ТЕМИ / TOPICS ---")
        sum_lines.append(", ".join(gdata['topics']) + "\n")

    sum_lines.append(f"Дата обробки: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    content = "\n".join(sum_lines)
    return Response(content.encode("utf-8"), media_type="text/plain; charset=utf-8",
                    headers=dl_headers(f"summary_{tid}.txt"))


# --- ZIP bundle ---

@router.post("/api/export/{tid}/zip")
async def export_zip(tid: str, request: Request):
    body = await request.json()
    formats = body.get("formats", [])
    title_mode = body.get("title_mode")

    data = get_transcript_cached(tid)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        def add(name: str, content: bytes | str):
            if isinstance(content, str):
                content = content.encode("utf-8")
            zf.writestr(name, content)

        _gc = gemini_cache.get(tid)
        _gd = _gc[0] if _gc and not _gc[0].get("error") else {}
        
        # Fallback: if Gemini data is missing from cache, fetch it on the fly
        if not _gd:
            from app.gemini_service import get_gemini_cached
            text = data.get("text", "")
            if len(text) >= 20:
                language = data.get("language_code", "en")
                has_speakers = bool(data.get("utterances"))
                spk_labels = list({u.get("speaker") for u in (data.get("utterances") or []) if u.get("speaker")})
                result = get_gemini_cached(tid, text, language, has_speakers, spk_labels if spk_labels else None)
                if not result.get("error"):
                    _gd = result
                    gemini_cache[tid] = [_gd]

        _lm, _sc = resolve_speakers(data, _gd)

        if "txt" in formats:
            add("transcript.txt", make_txt(data, label_map=_lm, speaker_count=_sc))
        if "md" in formats:
            hdr = make_doc_header(data)
            hdr["speakers"] = _sc
            lb = hdr["labels"]
            md_lines = [f"# {_gd.get('title', lb['title'])}\n"]
            meta = f"> **{lb['date']}:** {hdr['date']} | **{lb['duration']}:** {hdr['duration']} | **{lb['lang']}:** {hdr['language']}"
            if hdr["speakers"]:
                meta += f" | **{lb['speakers']}:** {hdr['speakers']}"
            md_lines.append(meta)
            if _gd.get("summary"):
                md_lines.append(f"\n> *{_gd['summary']}*")
            md_lines.append(f"\n---\n")
            if data.get("utterances"):
                for u in data["utterances"]:
                    ts = ms_to_readable(u.get("start", 0))
                    spk = _lm.get(u.get("speaker", ""), u.get("speaker", "Speaker"))
                    md_lines.append(f"**[{ts}] {spk}:** {u.get('text', '')}\n")
            else:
                md_lines.append(data.get("text", ""))
            add("transcript.md", "\n".join(md_lines))
        if "docx" in formats:
            add("transcript.docx", make_docx(data, label_map=_lm, speaker_count=_sc))
        if "pdf" in formats:
            _hdr = make_doc_header(data)
            _hdr["speakers"] = _sc
            add("transcript.pdf", make_pdf(data, _gd.get("title", "Transcript"), header_info=_hdr, gdata=_gd, label_map=_lm))
        if "table_docx" in formats:
            add("table.docx", make_table_docx(data, label_map=_lm, speaker_count=_sc))
        if "table_pdf" in formats:
            _hdr2 = make_doc_header(data)
            _hdr2["speakers"] = _sc
            add("table.pdf", make_table_pdf(data, label_map=_lm, speaker_count=_sc))
        if "literary_txt" in formats:
            add("literary.txt", make_literary_txt(data, label_map=_lm, speaker_count=_sc))
        if "literary_docx" in formats:
            add("literary.docx", make_literary_docx(data, label_map=_lm, speaker_count=_sc))
        if "interview_docx" in formats:
            add("interview.docx", make_interview_docx(data, label_map=_lm, speaker_count=_sc))
        if "verbatim_txt" in formats:
            add("verbatim.txt", make_verbatim_txt(data, label_map=_lm, speaker_count=_sc))
        if "verbatim_docx" in formats:
            add("verbatim.docx", make_verbatim_docx(data, label_map=_lm, speaker_count=_sc))
        if "srt" in formats:
            add("captions.srt", assemblyai_get_text(f"/v2/transcript/{tid}/srt"))
        if "vtt" in formats:
            add("captions.vtt", assemblyai_get_text(f"/v2/transcript/{tid}/vtt"))
        if "paragraphs_txt" in formats:
            p_data = assemblyai_get(f"/v2/transcript/{tid}/paragraphs")
            add("paragraphs.txt", make_paragraphs_txt(p_data.get("paragraphs", [])))
        if "paragraphs_json" in formats:
            p_data = assemblyai_get(f"/v2/transcript/{tid}/paragraphs")
            add("paragraphs.json", json.dumps(p_data, ensure_ascii=False, indent=2))
        if "sentences_txt" in formats:
            s_data = assemblyai_get(f"/v2/transcript/{tid}/sentences")
            add("sentences_timestamped.txt", make_sentences_txt(s_data.get("sentences", [])))
        if "sentences_csv" in formats:
            s_data = assemblyai_get(f"/v2/transcript/{tid}/sentences")
            add("sentences.csv", make_sentences_csv(s_data.get("sentences", [])))
        if "sentences_srt" in formats:
            s_data = assemblyai_get(f"/v2/transcript/{tid}/sentences")
            add("sentences.srt", make_sentences_srt(s_data.get("sentences", [])))
        if "words_json" in formats:
            add("words.json", json.dumps({"words": data.get("words", [])}, ensure_ascii=False, indent=2))
        if "words_csv" in formats:
            add("words.csv", make_words_csv(data.get("words", [])))

        translations = get_translation_results(data)
        for lang, lang_data in translations.items():
            if f"translation_{lang}_txt" in formats:
                add(f"translation_{lang}.txt", lang_data.get("text", ""))
            if f"translation_{lang}_srt" in formats:
                add(f"translation_{lang}.srt", make_translation_srt(lang_data))
            if f"bilingual_{lang}_txt" in formats:
                add(f"bilingual_{lang}.txt", make_bilingual_txt(data, lang_data, label_map=_lm, speaker_count=_sc))
            if f"bilingual_{lang}_docx" in formats:
                add(f"bilingual_{lang}.docx", make_bilingual_docx(data, lang_data, label_map=_lm, speaker_count=_sc))

        if "entities_csv" in formats and data.get("entities"):
            buf2 = io.StringIO()
            w = csv.writer(buf2)
            w.writerow(["entity_type", "text", "start_ms", "end_ms"])
            for e in data["entities"]:
                w.writerow([e.get("entity_type"), e.get("text"), e.get("start"), e.get("end")])
            add("entities.csv", buf2.getvalue())

        if _gd:
            gdata = _gd
            add("ai_analysis.json", json.dumps(gdata, ensure_ascii=False, indent=2))
            
            # Create a clean summary.txt for the client
            sum_lines = []
            title = gdata.get("title") or "AI Analysis"
            sum_lines.append(f"=== {title.upper()} ===\n")
            
            if gdata.get("summary"):
                sum_lines.append("--- SUMMARY ---")
                sum_lines.append(gdata['summary'] + "\n")

            if gdata.get("notes"):
                sum_lines.append("--- КОНСПЕКТ / NOTES ---")
                for note in gdata["notes"]:
                    sum_lines.append(f"• {note}")
                sum_lines.append("")

            if gdata.get("chapters"):
                sum_lines.append("--- ОСНОВНІ МОМЕНТИ / CHAPTERS ---")
                for ch in gdata["chapters"]:
                    ts = ms_to_readable(ch.get("start", 0))
                    sum_lines.append(f"[{ts}] {ch.get('headline')}")
                    if ch.get("summary"):
                        sum_lines.append(f"   > {ch['summary']}")
                sum_lines.append("")

            if gdata.get("topics"):
                sum_lines.append("--- ТЕМИ / TOPICS ---")
                sum_lines.append(", ".join(gdata['topics']) + "\n")

            sum_lines.append(f"Дата обробки: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
            add("summary.txt", "\n".join(sum_lines))

    buf.seek(0)
    return Response(buf.read(), media_type="application/zip",
                    headers=dl_headers(_fname(tid, "zip", title_mode)))
