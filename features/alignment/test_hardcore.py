"""
Hardcore stress tests — scenarios that WILL happen with real client data.
Tests edge cases that simple tests miss.
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.importers.aligner import align_texts, build_vtt_cues, word_similarity


def make_aai_words(text: str, wpm: int = 150) -> list:
    words = text.split()
    ms_per_word = 60_000 / wpm
    result = []
    t = 500
    for w in words:
        duration = max(150, int(ms_per_word * (len(w) / 5)))
        gap = random.randint(50, 200)
        result.append({"text": w, "start": int(t), "end": int(t + duration)})
        t += duration + gap
    return result


def measure(edited, aai_words, label):
    aligned = align_texts(edited, aai_words)
    total = len(aligned)
    matched = sum(1 for w in aligned if w["matched"])
    match_rate = matched / total if total else 0
    cues = build_vtt_cues(aligned)

    # Check cue overlaps
    overlaps = 0
    for i in range(1, len(cues)):
        if cues[i]["start"] < cues[i - 1]["end"]:
            overlaps += 1

    # Check monotonicity (timestamps should mostly increase)
    non_monotonic = 0
    for i in range(1, len(aligned)):
        if aligned[i]["start"] < aligned[i - 1]["start"] and aligned[i]["matched"]:
            non_monotonic += 1

    # Max gap between consecutive cues
    max_cue_gap = 0
    for i in range(1, len(cues)):
        gap = cues[i]["start"] - cues[i - 1]["end"]
        max_cue_gap = max(max_cue_gap, gap)

    return {
        "label": label,
        "total": total,
        "matched": matched,
        "rate": round(match_rate * 100, 1),
        "cues": len(cues),
        "overlaps": overlaps,
        "non_mono": non_monotonic,
        "max_gap": max_cue_gap,
    }


def print_report(results):
    print("\n" + "=" * 100)
    print(f"{'Scenario':<50} {'Words':>6} {'Match%':>7} {'Miss':>5} {'Cues':>5} {'Ovrlp':>6} {'NoMono':>7} {'MaxGap':>7}")
    print("-" * 100)
    for r in results:
        flag = ""
        if r["rate"] < 70:
            flag = " !!!"
        elif r["rate"] < 85:
            flag = " !"
        if r["overlaps"] > 0:
            flag += " [OVERLAP]"
        if r["non_mono"] > 0:
            flag += " [NON-MONO]"
        print(f"{r['label']:<50} {r['total']:>6} {r['rate']:>6.1f}% {r['total']-r['matched']:>5} {r['cues']:>5} {r['overlaps']:>6} {r['non_mono']:>7} {r['max_gap']:>6}ms{flag}")
    print("=" * 100)

    avg = sum(r["rate"] for r in results) / len(results)
    fails = [r for r in results if r["rate"] < 70]
    warns = [r for r in results if 70 <= r["rate"] < 85]
    overlaps = sum(r["overlaps"] for r in results)
    non_monos = sum(r["non_mono"] for r in results)
    print(f"\nAvg: {avg:.1f}% | Fails (<70%): {len(fails)} | Warnings (<85%): {len(warns)} | Overlaps: {overlaps} | Non-monotonic: {non_monos}")


# ─────────────────────────────────────────────
# SCENARIO GROUP 1: Contractions & Expansions
# ─────────────────────────────────────────────

def test_contractions():
    """AAI outputs contractions, editor expanded them."""
    aai_text = "I'm gonna don't won't can't shouldn't wouldn't it's that's we're they're he's she's"
    aai = make_aai_words(aai_text)
    edited = "I am going to do not will not cannot should not would not it is that is we are they are he is she is"
    return measure(edited, aai, "Contractions expanded")


def test_contractions_reverse():
    """Editor uses contractions, AAI expanded."""
    aai_text = "I am going to do not will not cannot should not"
    aai = make_aai_words(aai_text)
    edited = "I'm gonna don't won't can't shouldn't"
    return measure(edited, aai, "Contractions collapsed")


# ─────────────────────────────────────────────
# SCENARIO GROUP 2: Annotations & Markers
# ─────────────────────────────────────────────

def test_timestamps_in_text():
    """Editor left timestamps in the transcript."""
    aai_text = "Welcome everyone today we discuss machine learning fundamentals first topic is supervised learning"
    aai = make_aai_words(aai_text)
    edited = "[00:00:01] Welcome everyone. [00:00:05] Today we discuss machine learning fundamentals. [00:00:15] First topic is supervised learning."
    return measure(edited, aai, "Timestamps in edited text")


def test_annotations():
    """Editor added non-speech annotations."""
    aai_text = "Hello everyone welcome to the show today we have a special guest"
    aai = make_aai_words(aai_text)
    edited = "[INTRO MUSIC] Hello everyone, welcome to the show. [APPLAUSE] Today we have a special guest. [LAUGHTER]"
    return measure(edited, aai, "Annotations [MUSIC] [APPLAUSE]")


def test_inaudible_marks():
    """Editor marked inaudible sections."""
    aai_text = "The results showed that approximately thirty percent of patients had significant improvement"
    aai = make_aai_words(aai_text)
    edited = "The results showed that approximately [inaudible] percent of patients had significant improvement"
    return measure(edited, aai, "Inaudible markers")


# ─────────────────────────────────────────────
# SCENARIO GROUP 3: Repeated Phrases
# ─────────────────────────────────────────────

def test_repeated_phrases():
    """Same phrase appears multiple times — alignment must not jump ahead."""
    aai_text = "thank you very much for joining us today thank you very much for your time thank you very much for watching"
    aai = make_aai_words(aai_text)
    edited = "Thank you very much for joining us today. Thank you very much for your time. Thank you very much for watching."
    return measure(edited, aai, "Repeated phrases (3x)")


def test_repeated_short():
    """Repeated short phrases with minor variations."""
    aai_text = "yes yes I agree yes absolutely yes that is correct yes"
    aai = make_aai_words(aai_text)
    edited = "Yes, yes. I agree. Yes, absolutely. Yes, that is correct. Yes."
    return measure(edited, aai, "Repeated 'yes' (6x)")


# ─────────────────────────────────────────────
# SCENARIO GROUP 4: Numbers & Dates
# ─────────────────────────────────────────────

def test_numbers_spelled_vs_digits():
    """Numbers: spelled out in AAI, digits in edited."""
    aai_text = "we had three hundred forty two participants and the study ran from twenty twenty one to twenty twenty three the budget was one point five million dollars"
    aai = make_aai_words(aai_text)
    edited = "We had 342 participants and the study ran from 2021 to 2023. The budget was $1.5 million."
    return measure(edited, aai, "Numbers: spelled vs digits")


def test_numbers_digits_vs_spelled():
    """Numbers: digits in AAI, spelled out in edited."""
    aai_text = "the team scored 3 goals in the 1st half and 2 in the 2nd totaling 5 goals"
    aai = make_aai_words(aai_text)
    edited = "The team scored three goals in the first half and two in the second, totaling five goals."
    return measure(edited, aai, "Numbers: digits vs spelled")


def test_dates_and_times():
    """Dates and times in different formats."""
    aai_text = "the meeting is on january fifteenth twenty twenty six at two thirty pm"
    aai = make_aai_words(aai_text)
    edited = "The meeting is on January 15, 2026 at 2:30 PM."
    return measure(edited, aai, "Dates/times format mismatch")


# ─────────────────────────────────────────────
# SCENARIO GROUP 5: Multi-speaker chaos
# ─────────────────────────────────────────────

def test_multi_speaker_labels():
    """Speaker labels in edited text that don't exist in audio."""
    aai_text = "so what do you think about the proposal I think it is excellent we should proceed immediately but what about the budget the budget is approved"
    aai = make_aai_words(aai_text)
    edited = """MODERATOR: So what do you think about the proposal?
DR. SMITH: I think it is excellent. We should proceed immediately.
MODERATOR: But what about the budget?
CFO: The budget is approved."""
    edited = " ".join(edited.split())
    return measure(edited, aai, "Multi-speaker labels in text")


def test_cross_talk():
    """AAI captured crosstalk fragments that editor cleaned up."""
    aai_text = "I think the I think I think the best approach is to wait for for the results before making any decisions"
    aai = make_aai_words(aai_text)
    edited = "I think the best approach is to wait for the results before making any decisions."
    return measure(edited, aai, "Crosstalk/stuttering cleaned")


# ─────────────────────────────────────────────
# SCENARIO GROUP 6: Language edge cases
# ─────────────────────────────────────────────

def test_hyphenated():
    """Hyphenated words vs separate words."""
    aai_text = "this is a well known state of the art machine learning algorithm for real time processing"
    aai = make_aai_words(aai_text)
    edited = "This is a well-known, state-of-the-art machine-learning algorithm for real-time processing."
    return measure(edited, aai, "Hyphenated compounds")


def test_abbreviations():
    """Abbreviations and acronyms."""
    aai_text = "the CEO of NASA discussed AI and ML with the FBI and the CIA at the UN headquarters"
    aai = make_aai_words(aai_text)
    edited = "The C.E.O. of N.A.S.A. discussed A.I. and M.L. with the F.B.I. and the C.I.A. at the U.N. headquarters."
    return measure(edited, aai, "Abbreviations with dots")


def test_unicode_special():
    """Unicode characters: em-dashes, quotes, ellipsis."""
    aai_text = "he said well I do not know maybe we should wait and see"
    aai = make_aai_words(aai_text)
    edited = 'He said, "Well\u2026 I don\u2019t know \u2014 maybe we should wait and see."'
    return measure(edited, aai, "Unicode: em-dash, smart quotes")


# ─────────────────────────────────────────────
# SCENARIO GROUP 7: Scale & Endurance
# ─────────────────────────────────────────────

LONG_LECTURE = """
Good morning everyone today we will cover advanced neural network architectures specifically
transformers and attention mechanisms the transformer architecture was introduced in the paper
attention is all you need by vaswani and colleagues in two thousand seventeen before transformers
the dominant approach for sequence modeling was recurrent neural networks or RNNs and long short
term memory networks or LSTMs these models process sequences one token at a time which makes them
slow to train on long sequences transformers solve this problem with the self attention mechanism
which allows the model to look at all positions in the input simultaneously the key innovation is
the scaled dot product attention formula where queries keys and values are computed from the input
embeddings multi head attention extends this by running multiple attention operations in parallel
each head can learn to focus on different aspects of the input for example one head might capture
syntactic relationships while another captures semantic ones the transformer encoder consists of
multiple layers each containing a multi head attention sublayer followed by a feed forward network
residual connections and layer normalization are applied around each sublayer the decoder has an
additional cross attention layer that attends to the encoder output this architecture has proven
remarkably effective for machine translation language modeling text generation question answering
and many other natural language processing tasks recent developments include models like BERT
GPT and T five which have set new benchmarks across virtually every NLP task
""".strip()


def test_60min_lecture():
    """Simulating ~60 minutes of continuous lecture."""
    full_text = " ".join([LONG_LECTURE] * 10)  # ~2000 words
    aai = make_aai_words(full_text)
    # Editor: minor corrections throughout
    edited = full_text.replace("two thousand seventeen", "2017")
    edited = edited.replace("RNNs", "Recurrent Neural Networks")
    edited = edited.replace("LSTMs", "Long Short-Term Memory networks")
    edited = edited.replace("BERT", "B.E.R.T.")
    edited = edited.replace("GPT", "G.P.T.")
    return measure(edited, aai, "60min lecture (~2000 words)")


def test_120min_mixed():
    """Simulating ~120 minutes with heavy edits throughout."""
    full_text = " ".join([LONG_LECTURE] * 20)  # ~4000 words
    aai = make_aai_words(full_text)
    # Heavier edits
    edited = full_text.replace("two thousand seventeen", "2017")
    edited = edited.replace("Good morning everyone today", "Good morning, everyone. Today")
    edited = edited.replace("for example one head", "For example, one head")
    edited = edited.replace("the dominant approach for sequence modeling was", "the main approach to sequence modeling used to be")
    return measure(edited, aai, "120min mixed edits (~4000 words)")


# ─────────────────────────────────────────────
# SCENARIO GROUP 8: AAI hallucinations
# ─────────────────────────────────────────────

def test_aai_hallucinated_words():
    """AAI added words that were never spoken (hallucination)."""
    real_text = "The experiment showed promising results for cancer treatment"
    aai_text = "The uh experiment um showed like promising results you know for cancer treatment yeah"
    aai = make_aai_words(aai_text)
    return measure(real_text, aai, "AAI hallucinated fillers")


def test_aai_wrong_words():
    """AAI transcribed wrong words (low confidence)."""
    aai_text = "the patients received a placebo controlled trial with double blind methodology"
    aai = make_aai_words(aai_text)
    # AAI got some medical terms wrong
    aai[3]["text"] = "place bow"  # placebo
    aai[5]["text"] = "trawl"  # trial
    aai[7]["text"] = "dubble"  # double
    edited = "The patients received a placebo-controlled trial with double-blind methodology."
    return measure(edited, aai, "AAI wrong medical terms")


def test_aai_merged_words():
    """AAI merged two words into one or split one into two."""
    aai_text = "the healthcare system needs reform immediately"
    aai = make_aai_words(aai_text)
    # AAI split "healthcare" into "health care"
    split_aai = []
    for w in aai:
        if w["text"] == "healthcare":
            mid = (w["start"] + w["end"]) // 2
            split_aai.append({"text": "health", "start": w["start"], "end": mid})
            split_aai.append({"text": "care", "start": mid, "end": w["end"]})
        else:
            split_aai.append(w)
    edited = "The healthcare system needs reform immediately."
    return measure(edited, split_aai, "AAI split 'healthcare' → 2 words")


# ─────────────────────────────────────────────
# SCENARIO GROUP 9: Worst cases
# ─────────────────────────────────────────────

def test_completely_different():
    """Editor's text is completely different from audio (wrong file)."""
    aai = make_aai_words("The weather forecast for tomorrow shows rain and thunderstorms across the region")
    edited = "Financial markets saw significant gains yesterday as tech stocks rallied across all major exchanges."
    return measure(edited, aai, "WRONG FILE (completely different)")


def test_empty_gaps():
    """Long silence gaps in audio between spoken sections."""
    words = []
    t = 0
    # Section 1: 0-5s
    for w in "Welcome to the presentation".split():
        words.append({"text": w, "start": t, "end": t + 300})
        t += 400
    # 30 second gap (silence/music)
    t += 30000
    # Section 2: 35-40s
    for w in "Let us begin with the first topic".split():
        words.append({"text": w, "start": t, "end": t + 300})
        t += 400
    # 20 second gap
    t += 20000
    # Section 3: 60-65s
    for w in "Thank you for listening today".split():
        words.append({"text": w, "start": t, "end": t + 300})
        t += 400

    edited = "Welcome to the presentation. Let us begin with the first topic. Thank you for listening today."
    return measure(edited, words, "Long silence gaps (30s+)")


def test_paragraph_breaks():
    """Editor added paragraph structure with headers."""
    aai_text = "introduction this paper presents a novel approach to natural language processing methodology we collected data from three sources results our approach achieved ninety five percent accuracy conclusion further research is needed"
    aai = make_aai_words(aai_text)
    edited = """1. INTRODUCTION

This paper presents a novel approach to natural language processing.

2. METHODOLOGY

We collected data from three sources.

3. RESULTS

Our approach achieved 95% accuracy.

4. CONCLUSION

Further research is needed."""
    edited = " ".join(edited.split())
    return measure(edited, aai, "Paragraph headers + structure")


# ─────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────

if __name__ == "__main__":
    random.seed(42)

    tests = [
        # Contractions
        test_contractions,
        test_contractions_reverse,
        # Annotations
        test_timestamps_in_text,
        test_annotations,
        test_inaudible_marks,
        # Repeated
        test_repeated_phrases,
        test_repeated_short,
        # Numbers
        test_numbers_spelled_vs_digits,
        test_numbers_digits_vs_spelled,
        test_dates_and_times,
        # Multi-speaker
        test_multi_speaker_labels,
        test_cross_talk,
        # Language
        test_hyphenated,
        test_abbreviations,
        test_unicode_special,
        # Scale
        test_60min_lecture,
        test_120min_mixed,
        # AAI errors
        test_aai_hallucinated_words,
        test_aai_wrong_words,
        test_aai_merged_words,
        # Worst cases
        test_completely_different,
        test_empty_gaps,
        test_paragraph_breaks,
    ]

    results = []
    for t in tests:
        r = t()
        results.append(r)

    print_report(results)

    # Detailed failure analysis
    print("\n--- CRITICAL FAILURES (match < 70%) ---")
    for r in results:
        if r["rate"] < 70:
            print(f"  {r['label']}: {r['rate']}% ({r['matched']}/{r['total']} matched)")

    print("\n--- WARNINGS (70-85%) ---")
    for r in results:
        if 70 <= r["rate"] < 85:
            print(f"  {r['label']}: {r['rate']}% ({r['matched']}/{r['total']} matched)")

    print("\n--- QUALITY ISSUES ---")
    for r in results:
        if r["overlaps"] > 0:
            print(f"  {r['label']}: {r['overlaps']} cue overlaps!")
        if r["non_mono"] > 0:
            print(f"  {r['label']}: {r['non_mono']} non-monotonic timestamps!")
