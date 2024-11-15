# test_text_chunker.py

import pytest
from analitiq.chunkers.text_chunker import TextChunker
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata, Chunk

CHUNK_SIZE = 10  # Set the chunk size to 10 for testing
CHUNK_OVERLAP = 2  # Adjust if overlap is defined differently in your implementation


def create_document(content: str, document_name: str = "test_document") -> DocumentSchema:
    """Helper function to create a DocumentSchema instance."""
    doc_metadata = DocumentMetadata(
        document_name=document_name
    )
    return DocumentSchema(
        document_content=content,
        metadata=doc_metadata
    )

def get_chunker():
    return TextChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

def test_simple_text():
    chunker = get_chunker()
    data = "abcdefghij"  # Exactly 10 characters
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    print(result_chunks)
    assert len(result_chunks) == 1
    assert result_chunks[0].content == "abcdefghij"
    assert result_chunks[0].chunk_num_char == 10


def test_long_text():
    chunker = get_chunker()
    data = "abcdefghijklmnoprstuvwxyz"  # 26 characters
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected chunks considering CHUNK_SIZE = 10 and CHUNK_OVERLAP = 2
    expected_contents = [
        "abcdefghij",  # First 10 chars
        "ijklmnoprs",  # Overlap of 2: 'ij' + next 8 chars
        "rstuvwxyz"     # Remaining chars
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content for chunk in result_chunks] == expected_contents


def test_empty_text():
    chunker = get_chunker()
    data = ""  # Empty content
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    assert result_chunks is None


def test_text_with_overlap():
    chunker = get_chunker()
    data = "123456789012345678901234"  # 24 characters
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected chunks considering CHUNK_SIZE = 10 and CHUNK_OVERLAP = 2
    expected_contents = [
        "1234567890",  # First 10 chars
        "9012345678",  # Overlap of 2: '89' + next 8 chars
        "78901234"    # Remaining chars
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content for chunk in result_chunks] == expected_contents


def test_multiline_text():
    chunker = get_chunker()
    data = "Line 1\nLine 2\nLine 3"
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected chunks considering CHUNK_SIZE = 10 and CHUNK_OVERLAP = 2
    expected_contents = [
        "Line 1",  # First 10 chars
        "Line 2", # Overlap of 2 + next 8 chars
        "Line 3"  # Continuing with overlap
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content for chunk in result_chunks] == expected_contents


def test_unicode_text():
    chunker = get_chunker()
    data = "こんにちは世界こんにちは世界"  # Japanese text (20 characters)
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected chunks considering CHUNK_SIZE = 10
    expected_contents = [
        "こんにちは世界こんに",  # First 10 chars
        "んにちは世界"   # Next 10 chars
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content for chunk in result_chunks] == expected_contents


def test_special_characters_text():
    chunker = get_chunker()
    data = "C:\\Path\\To\\File.txt"
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected chunks considering CHUNK_SIZE = 10
    expected_contents = [
        "C:\\Path\\To",  # First 10 chars
        "To\\File.tx", # Overlap + next 8 chars
        "txt"         # Remaining chars
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content for chunk in result_chunks] == expected_contents


def test_text_with_spaces():
    chunker = get_chunker()
    data = "The quick brown fox jumps over the lazy dog"
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected chunks considering CHUNK_SIZE = 10
    expected_contents = [
        "The quick",  # First 10 chars
        "brown fox",  # Overlap + next 8 chars
        "jumps",  # Overlap + next 8 chars
        "over the",  # Continuing with overlap
        "lazy dog",  # Final chunk
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content for chunk in result_chunks] == expected_contents


def test_long_text_without_overlap():
    """Test without overlap (set CHUNK_OVERLAP = 0)."""
    chunker = get_chunker()
    data = "abcdefghijklmnop"  # 16 characters
    doc = create_document(data)

    # Temporarily override CHUNK_OVERLAP to 0
    global CHUNK_OVERLAP
    CHUNK_OVERLAP = 0

    chunker = get_chunker()
    result_chunks = chunker.chunk(doc)

    # Expected chunks considering CHUNK_SIZE = 10 and CHUNK_OVERLAP = 0
    expected_contents = [
        "abcdefghij",  # First 10 chars
        "klmnop"       # Remaining chars
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content for chunk in result_chunks] == expected_contents


# Run the tests
if __name__ == "__main__":
    pytest.main()
