# tests/unit/chunkers/test_python_chunker.py

import pytest
from analitiq.chunkers.python_chunker import PythonChunker
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata, Chunk

CHUNK_SIZE = 50  # Define the chunk size for testing
CHUNK_OVERLAP = 10  # Define the overlap for testing


def create_document(content: str, document_name: str = "test_python_file") -> DocumentSchema:
    """Helper function to create a DocumentSchema instance."""
    doc_metadata = DocumentMetadata(
        document_name=document_name
    )
    return DocumentSchema(
        document_content=content,
        metadata=doc_metadata
    )


def test_simple_function():
    chunker = PythonChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    data = """
def add(a, b):
    return a + b
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: The entire function fits into one chunk
    assert len(result_chunks) == 1
    assert result_chunks[0].content.strip() == data.strip()
    assert result_chunks[0].chunk_num_char == len(data.strip())


def test_multiple_functions():
    chunker = PythonChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    data = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Each function fits into separate chunks based on CHUNK_SIZE
    expected_contents = [
        "def add(a, b):\n    return a + b",
        "def subtract(a, b):\n    return a - b",
        "def multiply(a, b):\n    return a * b"
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content.strip() for chunk in result_chunks] == expected_contents


def test_large_code_block():
    chunker = PythonChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    data = """
    def large_function():
        x = 0
        for i in range(100):
            x += i
        return x
    """
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Code is split into multiple chunks with overlap
    expected_contents = [
        "def large_function():\n        x = 0",
        "for i in range(100):\n            x += i",
        "return x"
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content.strip() for chunk in result_chunks] == expected_contents


def test_empty_file():
    chunker = PythonChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    data = ""  # Empty content
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: No chunks are created for an empty file
    assert result_chunks == []


def test_multiline_function():
    chunker = PythonChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    data = """
def long_function(a, b, c, d, e):
    result = (a + b +
              c + d +
              e)
    return result
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Function fits in 3 chunks
    assert len(result_chunks) == 3


def test_class_with_methods():
    chunker = PythonChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    data = """
class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        pass
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Class and methods are split into chunks
    expected_contents = [
        'class MyClass:\n    def method_one(self):',
        'pass',
        'def method_two(self):\n        pass'
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content.strip() for chunk in result_chunks] == expected_contents


def test_nested_code_blocks():
    chunker = PythonChunker(max_chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    data = """
def outer_function():
    def inner_function():
        return "Hello, World!"
    return inner_function()
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Nested functions are split into chunks
    expected_contents = [
        "def outer_function():\n    def inner_function():",
        'return "Hello, World!"',
        'return inner_function()'
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content.strip() for chunk in result_chunks] == expected_contents


# Run the tests
if __name__ == "__main__":
    pytest.main()
