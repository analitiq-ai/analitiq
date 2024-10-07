import pytest
from langchain_community.docstore.document import Document
from analitiq.utils.custom_recursive_json_splitter import CustomRecursiveJsonSplitter

@pytest.fixture(name="splitter")
def fixture_splitter():
    """Create the Splitter Instance."""
    return CustomRecursiveJsonSplitter(max_chunk_size=2000)

def test_split_json_valid_data(splitter):
    """Test the split json function with valid data."""
    json_input = {
        "models": [
            {"name": "Model1", "description": "First model", "columns": [{"field1": "value1"}]},
            {"name": "Model2", "description": "Second model", "columns": [{"field2": "value2"}]}
        ],
        "version": "1.0"
    }
    result = splitter.split_json(json_input)
    assert len(result) == 2, "Should return 2 chunks for 2 models"
    assert "version" in result[0], "Metadata should include version"
    assert "models" in result[0], "Metadata should include models"

def test_split_json_no_models(splitter):
    """Test the split json model with missing models key."""
    json_input = {"version": "1.0"}
    with pytest.raises(KeyError) as excinfo:
        splitter.split_json(json_input)
    assert "JSON Error" in str(excinfo.value), "Should raise KeyError for missing models"

def test_split_documents(splitter):
    """Test the split document function."""
    documents = [Document(page_content="""{\"models\": [{\"name\":
                           \"Model1\", \"description\": \"Test\", \"columns\": [{\"field1\": \"value1\"}]}],
                           \"version\": \"1.0\"}""")]
    result = splitter.split_documents(documents)
    assert len(result) == 1, "Should return 1 split document"
    assert "version" in result[0].page_content, "Document content should include version in metadata"
