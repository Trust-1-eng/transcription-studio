"""
Stress tests for alignment algorithm.
Measures match rate, timing drift, and edge case handling
across realistic scenarios with large data arrays.
"""
import sys
import random
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.importers.aligner import align_texts, build_vtt_cues, word_similarity


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_aai_words(text: str, wpm: int = 150) -> list:
    """Generate realistic AssemblyAI word-level timestamps from text."""
    words = text.split()
    ms_per_word = 60_000 / wpm
    result = []
    t = 500  # start offset
    for w in words:
        duration = max(150, int(ms_per_word * (len(w) / 5)))
        gap = random.randint(50, 200)
        result.append({"text": w, "start": int(t), "end": int(t + duration)})
        t += duration + gap
    return result


def measure_alignment(edited: str, aai_words: list, label: str) -> dict:
    """Run alignment and measure quality metrics."""
    aligned = align_texts(edited, aai_words)
    total = len(aligned)
    matched = sum(1 for w in aligned if w["matched"])
    match_rate = matched / total if total else 0

    # Timing drift: for matched words, check if timing is within original range
    drifts = []
    for w in aligned:
        if not w["matched"]:
            continue
        # Find the original AAI word by matching start time
        for aw in aai_words:
            if aw["start"] == w["start"]:
                drifts.append(0)
                break

    # For unmatched words: measure interpolation error (distance from nearest matched neighbor)
    interpolation_gaps = []
    for i, w in enumerate(aligned):
        if w["matched"]:
            continue
        # Find nearest matched word timing
        prev_end = 0
        next_start = aligned[-1]["end"] if aligned else 0
        for p in range(i - 1, -1, -1):
            if aligned[p]["matched"]:
                prev_end = aligned[p]["end"]
                break
        for q in range(i + 1, len(aligned)):
            if aligned[q]["matched"]:
                next_start = aligned[q]["start"]
                break
        gap = next_start - prev_end
        interpolation_gaps.append(gap)

    cues = build_vtt_cues(aligned)

    # Check cue quality
    overlaps = 0
    for i in range(1, len(cues)):
        if cues[i]["start"] < cues[i - 1]["end"]:
            overlaps += 1

    result = {
        "label": label,
        "total_words": total,
        "matched": matched,
        "unmatched": total - matched,
        "match_rate": round(match_rate * 100, 1),
        "cue_count": len(cues),
        "cue_overlaps": overlaps,
        "avg_interpolation_gap_ms": round(sum(interpolation_gaps) / len(interpolation_gaps)) if interpolation_gaps else 0,
        "max_interpolation_gap_ms": max(interpolation_gaps) if interpolation_gaps else 0,
    }
    return result


def print_report(results: list):
    """Print formatted test report."""
    print("\n" + "=" * 90)
    print(f"{'Scenario':<40} {'Words':>6} {'Match%':>7} {'Unmatch':>8} {'Cues':>5} {'AvgDrift':>9} {'MaxDrift':>9}")
    print("-" * 90)
    for r in results:
        print(f"{r['label']:<40} {r['total_words']:>6} {r['match_rate']:>6.1f}% {r['unmatched']:>8} {r['cue_count']:>5} {r['avg_interpolation_gap_ms']:>7}ms {r['max_interpolation_gap_ms']:>7}ms")
    print("=" * 90)

    # Summary
    avg_match = sum(r["match_rate"] for r in results) / len(results)
    min_match = min(r["match_rate"] for r in results)
    total_overlaps = sum(r["cue_overlaps"] for r in results)
    print(f"\nAvg match rate: {avg_match:.1f}%  |  Min: {min_match:.1f}%  |  Cue overlaps: {total_overlaps}")


# ─────────────────────────────────────────────
# Test scenarios
# ─────────────────────────────────────────────

LECTURE_TEXT = """
Good morning everyone. Today we are going to discuss the fundamentals of machine learning.
Machine learning is a subset of artificial intelligence that focuses on building systems
that can learn from data. There are three main types of machine learning: supervised learning,
unsupervised learning, and reinforcement learning. In supervised learning, we have labeled
training data. The algorithm learns a mapping function from input to output. Common examples
include image classification, spam detection, and speech recognition. Unsupervised learning
deals with unlabeled data. The system tries to find hidden patterns or structures.
Clustering and dimensionality reduction are common techniques. Reinforcement learning
involves an agent that learns to make decisions by interacting with an environment.
The agent receives rewards or penalties based on its actions. This approach is used in
robotics, game playing, and autonomous driving. Now let us look at some practical
applications. Dr. Smith published a landmark paper in twenty nineteen about neural
architecture search. Professor Johnson from MIT extended this work in twenty twenty one.
Their findings showed that automated model selection can outperform manual feature
engineering in seventy five percent of cases. Thank you for your attention.
Any questions?
""".strip()

INTERVIEW_TEXT = """
John: Welcome to the show. Today we have Dr. Sarah Martinez with us.
Sarah: Thank you for having me, John. It is great to be here.
John: So tell us about your latest research at the Stanford Medical Center.
Sarah: Well, we have been studying the effects of intermittent fasting on
cognitive performance. Our team of twelve researchers conducted a double blind
study with three hundred participants over six months.
John: That sounds like a significant study. What were the main findings?
Sarah: The results were quite surprising actually. We found that participants
who followed a sixteen eight fasting protocol showed a twenty three percent
improvement in working memory tasks. Even more interesting, the control group
showed no significant change.
John: Twenty three percent is impressive. Were there any negative side effects?
Sarah: Some participants reported initial fatigue during the first two weeks,
but this resolved on its own. We monitored blood markers throughout the study
and found no adverse effects. In fact, inflammatory markers decreased by
about fifteen percent on average.
John: Fascinating. What are the next steps for your research?
Sarah: We are planning a larger follow up study with one thousand participants.
We also want to explore different fasting protocols and their effects on
long term cognitive health. The National Institutes of Health has already
approved our funding proposal.
John: That is wonderful news. Thank you so much for sharing this with us today.
Sarah: My pleasure. Thank you for the opportunity.
""".strip()


def test_1_exact_match():
    """Scenario: transcript matches audio exactly."""
    aai = make_aai_words(LECTURE_TEXT)
    return measure_alignment(LECTURE_TEXT, aai, "1. Exact match (ideal)")


def test_2_punctuation_changes():
    """Scenario: editor adds/changes punctuation only."""
    aai = make_aai_words(LECTURE_TEXT)
    edited = LECTURE_TEXT.replace(". ", ".\n").replace(",", ";")
    edited = " ".join(edited.split())
    return measure_alignment(edited, aai, "2. Punctuation changes")


def test_3_name_corrections():
    """Scenario: editor corrects names and technical terms."""
    aai_text = LECTURE_TEXT.replace("Dr. Smith", "dr smith").replace("Professor Johnson", "professor johnson")
    aai_text = aai_text.replace("Stanford", "stanford").replace("MIT", "M I T")
    aai = make_aai_words(aai_text)
    return measure_alignment(LECTURE_TEXT, aai, "3. Name corrections")


def test_4_filler_removal():
    """Scenario: AI transcribed fillers, editor removed them."""
    fillers = ["um", "uh", "like", "you know", "so", "basically"]
    words = LECTURE_TEXT.split()
    aai_words_text = []
    for i, w in enumerate(words):
        aai_words_text.append(w)
        if i % 8 == 0 and i > 0:
            aai_words_text.append(random.choice(fillers))
    aai_text = " ".join(aai_words_text)
    aai = make_aai_words(aai_text)
    return measure_alignment(LECTURE_TEXT, aai, "4. Filler words removed")


def test_5_word_insertions():
    """Scenario: editor added clarifying words not in audio."""
    words = LECTURE_TEXT.split()
    insertions = ["[applause]", "specifically", "importantly", "notably", "essentially"]
    edited_words = []
    for i, w in enumerate(words):
        edited_words.append(w)
        if i % 15 == 0 and i > 0:
            edited_words.append(random.choice(insertions))
    edited = " ".join(edited_words)
    aai = make_aai_words(LECTURE_TEXT)
    return measure_alignment(edited, aai, "5. Editor added words")


def test_6_number_formatting():
    """Scenario: numbers written differently."""
    aai_text = LECTURE_TEXT.replace("twenty nineteen", "2019")
    aai_text = aai_text.replace("twenty twenty one", "2021")
    aai_text = aai_text.replace("seventy five", "75")
    aai_text = aai_text.replace("three", "3").replace("twelve", "12")
    aai = make_aai_words(aai_text)
    return measure_alignment(LECTURE_TEXT, aai, "6. Number format mismatch")


def test_7_interview_speakers():
    """Scenario: multi-speaker interview with name labels."""
    # AAI transcribes without speaker names in text
    aai_text = INTERVIEW_TEXT.replace("John: ", "").replace("Sarah: ", "")
    aai = make_aai_words(aai_text)
    return measure_alignment(INTERVIEW_TEXT, aai, "7. Interview with speaker labels")


def test_8_heavy_edits():
    """Scenario: editor rewrote sentences significantly."""
    aai = make_aai_words(LECTURE_TEXT)
    edited = LECTURE_TEXT.replace(
        "Machine learning is a subset of artificial intelligence that focuses on building systems",
        "ML is a branch of AI dedicated to creating systems"
    ).replace(
        "There are three main types of machine learning",
        "Three primary categories of ML exist"
    ).replace(
        "Thank you for your attention",
        "Thank you all for listening today"
    )
    return measure_alignment(edited, aai, "8. Heavy sentence rewrites")


def test_9_long_document():
    """Scenario: long document (simulating 10+ minutes of audio)."""
    long_text = " ".join([LECTURE_TEXT] * 5)
    aai = make_aai_words(long_text)
    return measure_alignment(long_text, aai, "9. Long document (5x repeat)")


def test_10_mixed_edits():
    """Scenario: realistic mix of all edit types."""
    aai_text = INTERVIEW_TEXT.replace("John: ", "").replace("Sarah: ", "")
    aai_text = aai_text.replace("Dr.", "doctor").replace("twenty three", "23")
    # Add fillers in AAI
    words = aai_text.split()
    aai_with_fillers = []
    for i, w in enumerate(words):
        aai_with_fillers.append(w)
        if i % 12 == 0 and i > 0:
            aai_with_fillers.append("um")
    aai = make_aai_words(" ".join(aai_with_fillers))
    # Edited has speaker names, corrected names, no fillers
    return measure_alignment(INTERVIEW_TEXT, aai, "10. Mixed edits (realistic)")


def test_11_aai_errors():
    """Scenario: AAI made transcription errors that editor fixed."""
    aai_text = LECTURE_TEXT.replace("artificial intelligence", "artifical inteligence")
    aai_text = aai_text.replace("reinforcement", "reenforcement")
    aai_text = aai_text.replace("dimensionality", "dimensionnality")
    aai_text = aai_text.replace("autonomous", "autonamous")
    aai = make_aai_words(aai_text)
    return measure_alignment(LECTURE_TEXT, aai, "11. AAI spelling errors fixed")


def test_12_sentence_reorder():
    """Scenario: editor reordered some sentences (worst case)."""
    sentences = LECTURE_TEXT.split(". ")
    # Swap 2 sentences
    if len(sentences) > 5:
        sentences[2], sentences[4] = sentences[4], sentences[2]
    edited = ". ".join(sentences)
    aai = make_aai_words(LECTURE_TEXT)
    return measure_alignment(edited, aai, "12. Sentence reorder (worst case)")


def test_13_cyrillic():
    """Scenario: Ukrainian/Russian text."""
    ukr_text = "Доброго ранку всім Сьогодні ми будемо обговорювати основи машинного навчання Машинне навчання це підмножина штучного інтелекту"
    aai = make_aai_words(ukr_text)
    edited = "Доброго ранку всім. Сьогодні ми будемо обговорювати основи машинного навчання. Машинне навчання — це підмножина штучного інтелекту."
    return measure_alignment(edited, aai, "13. Cyrillic (Ukrainian)")


def test_14_short_words():
    """Scenario: many short common words (a, I, the, is)."""
    text = "I am a student and I want to be a doctor but it is not easy to do so I will try my best"
    aai = make_aai_words(text)
    edited = "I am a student, and I want to be a doctor, but it is not easy to do, so I will try my best."
    return measure_alignment(edited, aai, "14. Many short common words")


def test_15_window_exhaustion():
    """Scenario: large block of inserted text exceeds max_gap window.
    Note: 9 of 19 words are insertions that don't exist in audio.
    Real word match rate should be 100% (10/10 real words matched)."""
    aai = make_aai_words("Hello world this is a test of the alignment system")
    edited = "Hello world INSERTED BLOCK ONE TWO THREE FOUR FIVE SIX SEVEN this is a test of the alignment system"
    return measure_alignment(edited, aai, "15. Large insert (9/19 fake)")


# ─────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────

if __name__ == "__main__":
    random.seed(42)

    tests = [
        test_1_exact_match,
        test_2_punctuation_changes,
        test_3_name_corrections,
        test_4_filler_removal,
        test_5_word_insertions,
        test_6_number_formatting,
        test_7_interview_speakers,
        test_8_heavy_edits,
        test_9_long_document,
        test_10_mixed_edits,
        test_11_aai_errors,
        test_12_sentence_reorder,
        test_13_cyrillic,
        test_14_short_words,
        test_15_window_exhaustion,
    ]

    results = []
    for t in tests:
        r = t()
        results.append(r)

    print_report(results)

    # Identify problem scenarios
    print("\n--- PROBLEM SCENARIOS (match < 80%) ---")
    problems = [r for r in results if r["match_rate"] < 80]
    if problems:
        for r in problems:
            print(f"  {r['label']}: {r['match_rate']}% match, {r['unmatched']} unmatched words")
    else:
        print("  None! All scenarios above 80%.")

    print("\n--- TIMING QUALITY ---")
    high_drift = [r for r in results if r["max_interpolation_gap_ms"] > 2000]
    if high_drift:
        for r in high_drift:
            print(f"  {r['label']}: max interpolation gap {r['max_interpolation_gap_ms']}ms")
    else:
        print("  All interpolation gaps under 2000ms.")

    # Assertions
    passing = [r for r in results if r["match_rate"] >= 70]
    print(f"\n--- VERDICT: {len(passing)}/{len(results)} scenarios >= 70% match rate ---")
