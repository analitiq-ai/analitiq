import pytest
from langchain_community.docstore.document import Document
from libs.analitiq.utils import sql_recursive_text_splitter


def test_from_language():
    """Test from language function."""
    splitter = sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter.from_language("SQL")
    assert isinstance(splitter, sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter)
    assert splitter._separators == [";", "\n", " ", ",", "(", ")"]


def test_from_language_invalid():
    """Test the from language function with invalid values."""
    with pytest.raises(ValueError, match="This splitter only supports SQL language."):
        sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter.from_language("Python")


def test_split_text():
    """Test split text function."""
    splitter = sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter.from_language("SQL")
    text = "SELECT * FROM table1; SELECT * FROM table2;"
    expected = ["SELECT * FROM table1;", "SELECT * FROM table2;"]
    assert splitter.split_text(text) == expected


def test_split_documents():
    """Test split the documents."""
    splitter = sql_recursive_text_splitter.SQLRecursiveCharacterTextSplitter.from_language("SQL")
    doc1 = Document(page_content="SELECT * FROM table1;")
    doc2 = Document(page_content="SELECT * FROM table2;")
    documents = [doc1, doc2]
    split_docs = splitter.split_documents(documents)
    assert len(split_docs) == 2
    assert split_docs[0].page_content == "SELECT * FROM table1;"
    assert split_docs[1].page_content == "SELECT * FROM table2;"
