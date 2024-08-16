import pytest
from analitiq.utils import document_processor


def test_is_python_code():
    """Test the is python function."""
    loader = document_processor.DocumentChunkLoader(project_name="TestProject")
    python_code = 'print("Hello World")'
    assert loader._is_python_code(python_code) is True
    sql_code = "SELECT * FROM table"
    assert loader._is_python_code(sql_code) is False


def test_is_sql_statements():
    """Test the is sql statements."""
    loader = document_processor.DocumentChunkLoader(project_name="TestProject")
    sql_code = "SELECT * FROM table"
    assert loader._is_sql_statements(sql_code) is True
    python_code = 'print("Hello World")'
    assert loader._is_sql_statements(python_code) is False


def test_chunk_text():
    """TEst the chunk function."""
    text = "This is a test text, it should be split into chunks. please chunk it in a better way."
    expected = [
        "This is a test text, it should",
        ",hould be split into chunks. pl",
        ",s. please chunk it in a better",
        ",etter way.",
    ]

    loader = document_processor.DocumentChunkLoader(project_name="TestProject")
    result = loader.chunk_text(text, chunk_size=30, chunk_overlap=5, token=",")
    assert result == expected

    # Edge case: empty text
    text = ""
    expected = []
    assert loader.chunk_text(text, chunk_size=20, chunk_overlap=5, token=",") == expected
