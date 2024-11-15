# test_sql_chunker.py

import pytest
from analitiq.chunkers.sql_chunker import SQLChunker
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata


def create_document(content: str, document_name: str = "test_sql_file") -> DocumentSchema:
    """Helper function to create a DocumentSchema instance."""
    doc_metadata = DocumentMetadata(
        document_name=document_name
    )
    return DocumentSchema(
        document_content=content,
        metadata=doc_metadata
    )


def test_single_sql_statement():
    chunker = SQLChunker()
    data = "SELECT * FROM table;"
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: The entire SQL statement remains intact in one chunk
    assert len(result_chunks) == 1
    assert result_chunks[0].content.strip() == data.strip()
    assert result_chunks[0].chunk_num_char == len(data.strip())


def test_multiple_sql_statements():
    chunker = SQLChunker()
    data = """
SELECT * FROM table1;
SELECT column1, column2 FROM table2 WHERE column3 = 'value';
INSERT INTO table3 (column1, column2) VALUES ('value1', 'value2');
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Each SQL statement is kept as a separate chunk
    expected_contents = [
        "SELECT * FROM table1;",
        "SELECT column1, column2 FROM table2 WHERE column3 = 'value';",
        "INSERT INTO table3 (column1, column2) VALUES ('value1', 'value2');"
    ]

    assert len(result_chunks) == len(expected_contents)
    assert [chunk.content.strip() for chunk in result_chunks] == expected_contents


def test_multiline_sql_statement():
    chunker = SQLChunker()
    data = """
SELECT column1,
       column2,
       column3
FROM table1
WHERE column4 = 'value';
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Multiline SQL statement remains intact
    assert len(result_chunks) == 1
    assert result_chunks[0].content.strip() == data.strip()


def test_nested_sql_query():
    chunker = SQLChunker()
    data = """
SELECT column1, column2
FROM table1
WHERE column3 IN (
    SELECT column3
    FROM table2
    WHERE column4 = 'value'
);
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Nested query remains intact in one chunk
    assert len(result_chunks) == 1
    assert result_chunks[0].content.strip() == data.strip()


def test_empty_sql():
    chunker = SQLChunker()
    data = ""  # Empty SQL content
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: No chunks are created for empty content
    assert result_chunks is None


def test_sql_with_comments():
    chunker = SQLChunker()
    data = """
-- This is a comment
SELECT * FROM table1; -- Another comment
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: The entire SQL statement including comments remains intact
    assert len(result_chunks) == 1
    assert result_chunks[0].content.strip() == data.strip()


def test_sql_with_special_characters():
    chunker = SQLChunker()
    data = """
SELECT "column@name" AS "special!column"
FROM table_name
WHERE "column#1" = 'value%';
"""
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)

    # Expected: Special characters are preserved, and the query remains intact
    assert len(result_chunks) == 1
    assert result_chunks[0].content.strip() == data.strip()


# Run the tests
if __name__ == "__main__":
    pytest.main()
