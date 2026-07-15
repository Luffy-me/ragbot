from app.rag.chunking import split_pages_into_chunks


def test_split_pages_preserves_page_and_overlap():
    pages = [(1, "a" * 120), (2, "b" * 80)]
    chunks = split_pages_into_chunks(pages, chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 3
    assert chunks[0].page == 1
    assert chunks[-1].page == 2
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_clean_empty_pages_are_skipped():
    chunks = split_pages_into_chunks([(1, ""), (2, "hello world")], chunk_size=50, chunk_overlap=5)
    assert len(chunks) == 1
    assert chunks[0].text == "hello world"
