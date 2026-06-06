# Transcript Alignment

Sync client-provided edited transcripts (DOCX/PDF) with AssemblyAI word-level timestamps to produce VTT/SRT subtitle files.

## Use Case

Client provides edited transcripts + original videos. We need VTT subtitles where:
- **Text** = client's edited transcript (corrected names, spelling, terminology)
- **Timing** = AssemblyAI's word-level timestamps from audio

## Workflow

1. Upload video -> AssemblyAI transcribes -> `words[]` with ms timestamps
2. Upload client's DOCX/PDF transcript
3. System extracts text and aligns to AssemblyAI timestamps
4. Export VTT/SRT with client's text + AI timing

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/align/{tid}/upload` | Upload DOCX/PDF, align to transcript |
| GET | `/api/align/{tid}/vtt` | Export aligned VTT |
| GET | `/api/align/{tid}/srt` | Export aligned SRT |

## Algorithm

Greedy forward-walk with lookahead window (O(n)):
- Tokenize both texts into words
- Two pointers walk both sequences
- For each edited word, find best match in AAI words within window of 5
- Matched -> take AAI timestamp. Unmatched -> interpolate from neighbors

## Files

| File | Purpose |
|------|---------|
| `app/importers/text_extract.py` | Extract text from DOCX/PDF |
| `app/importers/aligner.py` | Alignment algorithm + VTT cue builder |
| `app/routes/alignment.py` | API endpoints |
| `app/exporters/subtitles.py` | `make_aligned_vtt/srt` functions |

## Testing

```bash
python -m pytest features/alignment/ -v
```
