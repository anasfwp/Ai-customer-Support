from app.services.chunker import Chunker


def test_paragraphs_survive_and_long_text_is_split():
    paragraphs = [" ".join(f"p{i}w{j}" for j in range(100)) for i in range(10)]
    chunks = Chunker(chunk_size=300, overlap=50).chunk_text("\n\n".join(paragraphs))

    assert len(chunks) == 5  # 3 paragraphs, then 50-word overlap + 2 paragraphs each
    assert all(len(c["content"].split()) <= 350 for c in chunks)
    # consecutive chunks share exactly the 50-word overlap
    assert chunks[1]["content"].split()[:50] == chunks[0]["content"].split()[-50:]


def test_single_huge_paragraph_is_windowed():
    chunks = Chunker(chunk_size=300, overlap=50).chunk_text(" ".join(["word"] * 1000))
    assert len(chunks) > 1 and all(len(c["content"].split()) <= 350 for c in chunks)
