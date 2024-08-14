import tempfile
import pathlib

from unittest.mock import patch
import pytest

from analitiq.vectordb.weaviate import WeaviateHandler


@pytest.fixture(name="mock_client", autouse=True)
def mock_client_fixture():
    """Mock the client."""
    with patch("weaviate.connect_to_wcs") as mock_connect:
        mock_client = mock_connect.return_value
        yield mock_client


@pytest.fixture(name="mock_chunk_processer", autouse=True)
def mock_chunk_processor_fixture():
    """Mock the chunk processor."""
    with patch("analitiq.vectordb.weaviate.DocumentChunkLoader") as MockChunkLoader:
        mock_chunk_processor = MockChunkLoader.return_value
        yield mock_chunk_processor


@pytest.fixture(name="params", autouse=True)
def params_fixture():
    """Mock some parameters."""
    return {
        "host": "https://test-analitiq-5mwe1rof.weaviate.network",
        "api_key": "Wy1q2YlOFAMETXA7OeUBAvNS4iUx3qnIpy24",
        "collection_name": "analitiq123123",
    }


@pytest.fixture(name="handler")
def handler_fixture(params):
    """Use the Weaviatehandler with mocked params."""
    return WeaviateHandler(params)


def test_connect(handler, mock_client):
    """Test the connect command."""
    mock_client.collections.exists.return_value = False
    handler.connect()

    assert handler.client == mock_client


def test_create_collection(handler, mock_client, params):
    """Test the create collection function."""
    mock_client.collections.exists.return_value = False
    handler.create_collection()
    mock_client.collections.exists.assert_called_with(params["collection_name"])


def test_load(handler):
    """Test the load function."""
    # Create a temporary text file with dummy text
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
        temp_file.write(b"This is a dummy text for unit tests.")

        # Test case for loading a valid file
        with patch.object(handler, "_chunk_load_file_or_directory") as mock_chunk_load:
            handler.load(temp_file.name)
            mock_chunk_load.assert_called_once_with(temp_file.name, "txt")

    pathlib.Path(temp_file.name).unlink()

    # Test case for missing file
    with pytest.raises(FileNotFoundError):
        handler.load("test_file.txt", file_ext="invalid")
