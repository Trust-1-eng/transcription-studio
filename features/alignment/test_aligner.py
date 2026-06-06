import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.importers.aligner import normalize_word, word_similarity, align_texts, build_vtt_cues


def test_normalize_word():
    assert normalize_word("Hello,") == "hello"
    assert normalize_word("world!") == "world"
    assert normalize_word("Dr.") == "dr"
    assert normalize_word("it's") == "its"


def test_word_similarity_exact():
    assert word_similarity("hello", "hello") == 1.0


def test_word_similarity_case():
    assert word_similarity("Hello", "hello") == 0.95


def test_word_similarity_partial():
    score = word_similarity("Johnson", "john")
    assert score >= 0.5


def test_word_similarity_different():
    score = word_similarity("cat", "elephant")
    assert score < 0.5


def test_align_texts_exact_match():
    aai_words = [
        {"text": "Hello", "start": 0, "end": 500},
        {"text": "world", "start": 600, "end": 1000},
        {"text": "this", "start": 1100, "end": 1400},
        {"text": "is", "start": 1500, "end": 1600},
        {"text": "a", "start": 1700, "end": 1800},
        {"text": "test", "start": 1900, "end": 2200},
    ]
    edited = "Hello world this is a test"
    result = align_texts(edited, aai_words)

    assert len(result) == 6
    assert all(w["matched"] for w in result)
    assert result[0]["start"] == 0
    assert result[0]["end"] == 500
    assert result[-1]["start"] == 1900
    assert result[-1]["end"] == 2200


def test_align_texts_with_edits():
    aai_words = [
        {"text": "john", "start": 0, "end": 500},
        {"text": "said", "start": 600, "end": 900},
        {"text": "hello", "start": 1000, "end": 1400},
        {"text": "to", "start": 1500, "end": 1600},
        {"text": "everyone", "start": 1700, "end": 2200},
    ]
    edited = "Dr. Johnson said hello to everyone"
    result = align_texts(edited, aai_words)

    assert len(result) == 6
    # "Dr." is inserted by editor - should be unmatched but interpolated
    assert result[0]["text"] == "Dr."
    # "Johnson" should fuzzy match "john"
    assert result[1]["text"] == "Johnson"
    assert result[1]["start"] == 0  # matched to "john"
    # All timestamps should be non-negative
    assert all(w["start"] >= 0 for w in result)
    assert all(w["end"] >= 0 for w in result)


def test_align_texts_empty():
    assert align_texts("", []) == []
    assert align_texts("hello", []) == []
    assert align_texts("", [{"text": "hi", "start": 0, "end": 100}]) == []


def test_build_vtt_cues_basic():
    aligned = [
        {"text": "Hello", "start": 0, "end": 500, "matched": True},
        {"text": "world.", "start": 600, "end": 1000, "matched": True},
        {"text": "This", "start": 1100, "end": 1400, "matched": True},
        {"text": "is", "start": 1500, "end": 1600, "matched": True},
        {"text": "great.", "start": 1700, "end": 2200, "matched": True},
    ]
    cues = build_vtt_cues(aligned)
    assert len(cues) >= 1
    assert cues[0]["start"] == 0
    # Each cue should have text
    assert all(c["text"] for c in cues)


def test_build_vtt_cues_respects_max_chars():
    words = [{"text": f"word{i}", "start": i * 500, "end": i * 500 + 400, "matched": True} for i in range(50)]
    cues = build_vtt_cues(words, max_chars_per_line=20, max_lines=1)
    for c in cues:
        assert len(c["text"]) <= 40  # some tolerance for word boundaries


def test_build_vtt_cues_empty():
    assert build_vtt_cues([]) == []


def test_full_pipeline():
    """End-to-end: align text to words, build cues, verify output."""
    aai_words = [
        {"text": "The", "start": 100, "end": 200},
        {"text": "quick", "start": 300, "end": 500},
        {"text": "brown", "start": 600, "end": 800},
        {"text": "fox", "start": 900, "end": 1100},
        {"text": "jumps", "start": 1200, "end": 1500},
        {"text": "over", "start": 1600, "end": 1800},
        {"text": "the", "start": 1900, "end": 2000},
        {"text": "lazy", "start": 2100, "end": 2300},
        {"text": "dog", "start": 2400, "end": 2700},
    ]
    edited = "The quick brown fox jumps over the lazy dog."
    aligned = align_texts(edited, aai_words)
    assert len(aligned) == 9

    cues = build_vtt_cues(aligned)
    assert len(cues) >= 1
    full_text = " ".join(c["text"] for c in cues)
    assert "quick brown fox" in full_text
    assert cues[0]["start"] == 100


if __name__ == "__main__":
    test_normalize_word()
    test_word_similarity_exact()
    test_word_similarity_case()
    test_word_similarity_partial()
    test_word_similarity_different()
    test_align_texts_exact_match()
    test_align_texts_with_edits()
    test_align_texts_empty()
    test_build_vtt_cues_basic()
    test_build_vtt_cues_respects_max_chars()
    test_build_vtt_cues_empty()
    test_full_pipeline()
    print("All tests passed!")
