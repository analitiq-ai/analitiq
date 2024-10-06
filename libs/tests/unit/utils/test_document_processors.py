from analitiq.utils import document_processor


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
    testdata = [
        ("I'm an example text", "text.txt")
    ]

    docs = processor.load_documents(testdata)
    assert len(docs) == 1
    assert docs[0].page_content == testdata[0][0]
    assert docs[0].metadata.get("source") == testdata[0][1]

