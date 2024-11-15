# Filename: test_text_loader.py

import pytest
from analitiq.loaders.documents.text_loader import TextLoader
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata, ALLOWED_EXTENSIONS
from analitiq.loaders.documents.utils.common_loader_funcs import get_document_type

# Test cases for TextLoader initialization and loading functionality

def test_text_loader_initialization_with_valid_extension():
    """Test TextLoader initialization with a valid file extension."""
    content = "Sample content"
    filename = "sample.txt"
    extension = "txt"

    loader = TextLoader(content=content, filename=filename, extension=extension)

    assert loader.content == content
    assert loader.filename == filename
    assert loader.extension == extension

def test_text_loader_initialization_with_invalid_extension():
    """Test TextLoader raises ValueError when an invalid extension is provided."""
    content = "Sample content"
    filename = "sample.exe"
    extension = "exe"  # Unsupported extension

    with pytest.raises(ValueError) as exc_info:
        TextLoader(content=content, filename=filename, extension=extension)

    assert f"Extension {extension} not allowed" in str(exc_info.value)
    assert extension not in ALLOWED_EXTENSIONS

def test_text_loader_load_method_with_valid_data(mocker):
    """Test if the load method returns a list of DocumentSchema with valid metadata."""
    content = "Sample content"
    filename = "sample.txt"
    extension = "txt"

    # Mock get_document_type function to return a fixed document type
    mock_document_type = "text"
    mocker.patch("analitiq.loaders.documents.utils.common_loader_funcs.get_document_type", return_value=mock_document_type)

    loader = TextLoader(content=content, filename=filename, extension=extension)
    documents = loader.load()

    # Check that documents list is returned and has one DocumentSchema instance
    assert isinstance(documents, list)
    assert len(documents) == 1
    assert isinstance(documents[0], DocumentSchema)

    # Verify DocumentSchema content and metadata
    document = documents[0]
    assert document.document_content == content
    assert isinstance(document.metadata, DocumentMetadata)
    assert document.metadata.document_name == filename
    assert document.metadata.document_type == mock_document_type

def test_text_loader_load_method_metadata_values(mocker):
    """Test the metadata values returned by the load method."""
    content = "Another sample content"
    filename = "document.md"
    extension = "md"

    # Mock get_document_type function to return 'markdown'
    mock_document_type = "markdown"
    mocker.patch("analitiq.loaders.documents.utils.common_loader_funcs.get_document_type", return_value=mock_document_type)

    loader = TextLoader(content=content, filename=filename, extension=extension)
    documents = loader.load()

    # Validate that the metadata is set correctly
    document = documents[0]
    assert document.metadata.document_name == filename
    assert document.metadata.document_type == mock_document_type

