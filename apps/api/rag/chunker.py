from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    metadata: dict[str, Any]


def chunk_text(
    text: str,
    metadata: dict[str, Any],
    target_words: int = 800,
    overlap_words: int = 120,
) -> list[TextChunk]:
    if target_words <= 0:
        raise ValueError("target_words must be positive")
    if overlap_words < 0 or overlap_words >= target_words:
        raise ValueError("overlap_words must be between 0 and target_words")

    words = text.split()
    if not words:
        return []

    step = target_words - overlap_words
    chunks: list[TextChunk] = []
    for index, start in enumerate(range(0, len(words), step)):
        content = " ".join(words[start : start + target_words])
        if not content:
            break
        chunks.append(TextChunk(index=index, content=content, metadata=dict(metadata)))
        if start + target_words >= len(words):
            break
    return chunks

