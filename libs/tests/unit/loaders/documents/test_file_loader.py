# Filename: test_file_loader.py

import pytest
import yaml
import json
from analitiq.loaders.documents.file_loader import FileLoader, ALLOWED_EXTENSIONS
from analitiq.loaders.documents.schemas import DocumentSchema

# Test setup and teardown functions
@pytest.fixture
def create_temp_file(tmp_path):
    """Fixture that creates a temporary file with a specific extension and optional content."""
    def _create_temp_file(extension, content="Test content"):
        file_path = tmp_path / f"test_file{extension}"
        file_path.write_text(content)
        return file_path
    return _create_temp_file

# Test cases

def test_file_loader_initialization_with_supported_extensions(create_temp_file):
    """Test if FileLoader initializes with supported file extensions."""
    for extension in ALLOWED_EXTENSIONS:
        file_path = create_temp_file("." + extension)
        loader = FileLoader(str(file_path))
        print(loader.file_path)
        print(file_path)
        assert loader.file_path == file_path

def test_file_loader_unsupported_extension(create_temp_file):
    """Test if FileLoader raises ValueError with unsupported file extensions."""
    unsupported_file = create_temp_file(".exe")
    with pytest.raises(ValueError) as exc_info:
        FileLoader(str(unsupported_file))
    assert f"Extension {unsupported_file.suffix[1:]} not allowed" in str(exc_info.value)

def test_file_loader_non_existent_file():
    """Test if FileLoader raises FileNotFoundError for a non-existent file."""
    non_existent_path = "/path/to/non_existent_file.txt"
    with pytest.raises(FileNotFoundError) as exc_info:
        FileLoader(non_existent_path)
    assert f"The file {non_existent_path} does not exist" in str(exc_info.value)

def test_load_method_with_text_file(create_temp_file):
    """Test if the load method reads content from a text file and converts it to DocumentSchema."""
    file_path = create_temp_file(".txt", "Test content")

    # Create FileLoader instance
    loader = FileLoader(str(file_path))

    # Load and validate document content
    documents = loader.load()
    assert isinstance(documents, list)
    assert len(documents) == 1
    assert isinstance(documents[0], DocumentSchema)
    assert documents[0].document_content == "Test content"
    assert documents[0].metadata.document_name == "test_file"
    assert documents[0].metadata.document_type == "text"

def test_load_method_with_yaml_file(create_temp_file):
    """Test if the load method reads content from a YAML file and converts it to DocumentSchema."""
    yaml_content = "key: value\nanother_key: another_value"
    file_path = create_temp_file(".yml", yaml_content)

    # Create FileLoader instance
    loader = FileLoader(str(file_path))

    # Load and validate document content
    documents = loader.load()
    assert isinstance(documents, list)
    assert len(documents) == 1
    assert isinstance(documents[0], DocumentSchema)

    # Convert document_content from JSON string to dictionary
    actual_content = json.loads(documents[0].document_content)

    # Parse yaml_content to compare with loaded document content
    expected_content = yaml.safe_load(yaml_content)

    assert actual_content == expected_content
    assert documents[0].metadata.document_name == "test_file"
    assert documents[0].metadata.document_type == "yaml"
