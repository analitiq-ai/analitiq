# Filename: test_directory_loader.py

import pytest
from analitiq.loaders.documents.directory_loader import DirectoryLoader
from analitiq.loaders.documents.schemas import DocumentSchema

# Fixtures for creating a mock directory structure and loaders
@pytest.fixture
def mock_directory(tmp_path):
    """Fixture that sets up a temporary directory with files of various extensions."""
    # Create a mock directory structure
    (tmp_path / "test1.txt").write_text("Sample text content")
    (tmp_path / "test2.yaml").write_text("Sample YAML content")
    (tmp_path / "test3.pdf").write_text("Sample PDF content")
    return tmp_path

# Test cases

def test_directory_loader_initialization_with_valid_directory(mock_directory):
    """Test if DirectoryLoader initializes with a valid directory."""
    loader = DirectoryLoader(directory_path=str(mock_directory))
    assert loader.directory_path == mock_directory
    assert loader.extension is None
    assert loader.glob_pattern == "**/*.*"

def test_directory_loader_initialization_with_invalid_directory():
    """Test if DirectoryLoader raises FileNotFoundError for a non-existent directory."""
    with pytest.raises(FileNotFoundError) as exc_info:
        DirectoryLoader(directory_path="/non/existent/directory")
    assert "does not exist" in str(exc_info.value)

def test_directory_loader_initialization_with_valid_extension():
    """Test if DirectoryLoader initializes correctly with a valid extension."""
    loader = DirectoryLoader(directory_path=".", extension=".txt")
    assert loader.extension == "txt"
    assert loader.glob_pattern == "**/*.txt"

def test_directory_loader_initialization_with_invalid_extension():
    """Test if DirectoryLoader raises ValueError for an invalid extension."""
    with pytest.raises(ValueError) as exc_info:
        DirectoryLoader(directory_path=".", extension="exe")
    assert "Extension exe not allowed" in str(exc_info.value)

def test_directory_loader_load_all_files(mock_directory):
    """Test if DirectoryLoader loads all files in the directory."""
    # Initialize DirectoryLoader without mocks so it actually loads the documents
    loader = DirectoryLoader(directory_path=str(mock_directory), special_loaders={"yaml": None})
    documents = loader.load()

    # Assertions to ensure documents are loaded correctly
    assert isinstance(documents, list)
    assert len(documents) > 0
    assert all(isinstance(doc, DocumentSchema) for doc in documents)

    assert any(doc.metadata.document_name == "test1" for doc in documents)
    assert any(doc.metadata.document_name == "test2" for doc in documents)

def test_directory_loader_load_with_specific_extension(mock_directory):
    """Test if DirectoryLoader loads only files with a specific extension."""
    loader = DirectoryLoader(directory_path=str(mock_directory), extension="txt")
    documents = loader.load()

    # Assertions to ensure only txt files are loaded
    assert isinstance(documents, list)
    assert len(documents) == 1
    assert all(isinstance(doc, DocumentSchema) for doc in documents)
    metadata = documents[0].metadata
    assert metadata.document_name == "test1"

def test_directory_loader_special_loader_invocation(mock_directory):
    """Test if DirectoryLoader uses special loader for specific file types."""
    # Pass a special loader for YAML files
    loader = DirectoryLoader(directory_path=str(mock_directory), special_loaders={"yaml": None})
    documents = loader.load()

    # Assertions to ensure special loader is used correctly
    assert isinstance(documents, list)
    assert len(documents) > 0

    assert any(doc.metadata.document_name == "test2" for doc in documents)
