import os
import pathlib
import tempfile

import pytest
from langchain_core.documents.base import Document

from analitiq.utils import document_processor


@pytest.fixture(name="tmp_dir")
def fixture_tmp_dir() -> pathlib.Path:
    """Create a temporary test dir for testing file loading functions."""
    tmp_dir = tempfile.mkdtemp()
    return pathlib.Path(tmp_dir)

def test_is_python_code():
    """Test the is python function."""
    loader = document_processor.DocumentProcessor(project_name="TestProject")
    python_code = 'print("Hello World")'
    assert loader.is_python_code(python_code) is True
    sql_code = "SELECT * FROM table"
    assert loader.is_python_code(sql_code) is False


def test_is_sql_statements():
    """Test the is sql statements."""
    loader = document_processor.DocumentProcessor(project_name="TestProject")
    sql_code = "SELECT * FROM table"
    assert loader.is_sql_statements(sql_code) is True
    python_code = 'print("Hello World")'
    assert loader.is_sql_statements(python_code) is False


def test_chunk_text():
    """TEst the chunk function."""
    text = "This is a test text, it should be split into chunks. please chunk it in a better way."
    expected = [
        "This is a test text",
        "text, it should be split into ",
        "nto chunks. please chunk it in",
        "t in a better way.",
    ]

    result = document_processor.chunk_text(text, chunk_size=30, chunk_overlap=5, token=",")
    assert result == expected

    # Edge case: empty text
    text = ""
    expected = []
    assert document_processor.chunk_text(text, chunk_size=20, chunk_overlap=5, token=",") == expected


def test_load_documents_strings():
    """Test the load documents function."""
    processor = document_processor.DocumentProcessor("example")
    testdata = [("I'm an example text", "text.txt")]

    docs = processor.load_documents(testdata)
    assert len(docs) == 1
    assert docs[0].page_content == testdata[0][0]
    assert docs[0].metadata.get("source") == testdata[0][1]


def test_load_single_yml_document(tmp_dir):
    """Test the loading of a single yml document."""
    processor = document_processor.DocumentProcessor("example")
    file_contents = {
        "test.yaml": "key: value\nnumber: 12345"
    }
    for filename, content in file_contents.items():
        file_path = tmp_dir / filename
        with open(file_path, "w") as f:
            f.write(content)

    expect_yaml_result = Document(page_content='{"key": "value", "number": 12345}',
                                metadata={"source": str(tmp_dir / "test.yaml")})

    docs = processor.load_documents(tmp_dir / "test.yaml")
    assert len(docs) == 1
    assert expect_yaml_result in docs


def test_load_documents_yaml_mixed(tmp_dir):
    """Test the loading of documents from dir with different file types."""
    processor = document_processor.DocumentProcessor("example")

    file_contents = {
        "test.txt": "This is a dummy text file. please load it correctly",
        "test.sql": "-- This is a dummy SQL file.\nSELECT * FROM dummy_table;\n",
        "test.yaml": "key: value\nnumber: 12345"
    }

    for filename, content in file_contents.items():
        file_path = tmp_dir / filename
        with open(file_path, "w") as f:
            f.write(content)

    expect_txt_result = Document(page_content="This is a dummy text file. please load it correctly",
                                  metadata={"source": str(tmp_dir / "test.txt")})
    expect_sql_result = Document(page_content="-- This is a dummy SQL file.\nSELECT * FROM dummy_table;\n",
                                  metadata={"source": str(tmp_dir / "test.sql")})
    expect_yaml_result = Document(page_content='{"key": "value", "number": 12345}',
                                metadata={"source": str(tmp_dir / "test.yaml")})

    docs = processor.load_documents(tmp_dir)
    assert len(docs) == 3
    assert expect_sql_result in docs
    assert expect_yaml_result in docs
    assert expect_txt_result in docs
