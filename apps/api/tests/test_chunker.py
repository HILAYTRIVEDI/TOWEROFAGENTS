import pytest

from rag.chunker import chunk_text


def test_chunker_preserves_overlap_and_metadata() -> None:
    chunks = chunk_text(
        "one two three four five six",
        {"source": "resume.txt"},
        target_words=4,
        overlap_words=1,
    )
    assert [chunk.content for chunk in chunks] == [
        "one two three four",
        "four five six",
    ]
    assert chunks[1].metadata["source"] == "resume.txt"


def test_chunker_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_text("text", {}, target_words=2, overlap_words=2)

