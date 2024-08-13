import pytest
from unittest.mock import patch, MagicMock
from analitiq.vectordb.weaviate import WeaviateHandler
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter

# Existing WeaviateHandler class code
# ... (paste the WeaviateHandler class code here) ...

@pytest.fixture
def mock_client():
    """Mock the client."""
    with patch("weaviate.connect_to_wcs") as mock_connect:
        mock_client = mock_connect.return_value
        yield mock_client

@pytest.fixture
def mock_chunk_processor():
    """Mock the chunk processor."""
    with patch("analitiq.vectordb.weaviate.DocumentChunkLoader") as MockChunkLoader:
        mock_chunk_processor = MockChunkLoader.return_value
        yield mock_chunk_processor

@pytest.fixture
def params():
    """Mock some parameters."""
    return {
        "host": "https://test-analitiq-5mwe1rof.weaviate.network",
        "api_key": "Wy1q2YlOFAMETXA7OeUBAvNS4iUx3qnIpy24",
        "collection_name": "analitiq123123",
    }

@pytest.fixture
def handler(mock_client, mock_chunk_processor, params):
    """Use the Weaviatehandler with mocked params."""
    return WeaviateHandler(params)

def test_connect(handler, mock_client, params):
    """Test the connect command."""
    mock_client.collections.exists.return_value = False
    handler.connect()

    mock_client.assert_called_once_with(
        cluster_url=params["host"], auth_credentials=AuthApiKey(params["api_key"])
    )
    assert handler.client == mock_client

def test_create_collection(handler, mock_client, params):
    """Test the create collection function."""
    mock_client.collections.exists.return_value = False
    handler.create_collection()
    mock_client.collections.exists.assert_called_with(params["collection_name"])

def test_load(handler, mock_chunk_processor):
    """Test the load function."""
    # Test case for loading a valid file
    test_file = "test_file.txt"
    with patch.object(handler, "_chunk_load_file_or_directory") as mock_chunk_load:
        handler.load(test_file)
        mock_chunk_load.assert_called_once_with(test_file, "txt")

    # Test case for invalid file extension
    with pytest.raises(ValueError):
        handler.load("test_file.txt", file_ext="invalid")

    # Test case for non-existent file or directory
    with pytest.raises(FileNotFoundError):
        handler.load("non_existent_file.txt")

def test_get_many_like(handler, mock_client):
    """Test the get many like function."""
    mock_response = MagicMock()
    handler.collection.query.fetch_objects.return_value = mock_response

    result = handler.get_many_like("source", "test")
    handler.collection.query.fetch_objects.assert_called_once_with(
        filters=Filter.by_property("source").like("*test*")
    )
    assert result == mock_response

def test_delete_collection(handler, mock_client, params):
    """Test the delete collection method."""
    handler.collection.delete.return_value = True

    result = handler.delete_collection(params["collection_name"])

    handler.client.collections.delete.assert_called_once_with(params["collection_name"])
    assert result

def test_delete_many_like(handler, mock_client):
    """Test delete many like this function."""
    handler.collection.data.delete_many.return_value = None

    result = handler.delete_many_like("source", "test")

    handler.collection.data.delete_many.assert_called_once_with(
        where=Filter.by_property("source").like("test*")
    )
    assert result

def test_kw_search(handler, mock_client):
    """Test the kw search."""
    mock_response = MagicMock()
    handler.collection.query.bm25.return_value = mock_response

    result = handler.kw_search("test query", limit=5)

    handler.collection.query.bm25.assert_called_once_with(
        query="test query", query_properties=["content"], limit=5
    )
    assert result == mock_response
