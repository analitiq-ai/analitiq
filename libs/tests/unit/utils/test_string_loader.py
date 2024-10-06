import pytest
from langchain_core.documents import Document
from analitiq.utils.string_loader import StringDocumentLoader

strings = [
    ("This is a test document.", "test1.txt"),
    ("This is another test document.", "test2.txt"),
]

def test_string_document_loader_init():
    """Test the initialization of the StringDocumentLoader."""
    loader = StringDocumentLoader(strings)
    assert loader.strings == strings

def test_string_document_loader_lazy_load():
    """Test the lazy_load method of the StringDocumentLoader."""
    loader = StringDocumentLoader(strings)
    documents = list(loader.lazy_load())
    assert len(documents) == 2
    for i, document in enumerate(documents):
        assert document.page_content == strings[i][0]
        assert document.metadata["source"] == strings[i][1]
