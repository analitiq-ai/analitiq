# tests/unit/chunkers/test_json_chunker.py


import json
from analitiq.chunkers.json_chunker import JsonChunker
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata, Chunk
CHUNK_SIZE = 35

def create_document(content: dict, document_name: str = "test_document") -> DocumentSchema:
    """Helper function to create a DocumentSchema instance."""
    doc_metadata = DocumentMetadata(
        document_name=document_name
    )
    doc = DocumentSchema(
        document_content=json.dumps(content, ensure_ascii=False),  # Convert dict to JSON string
        metadata=doc_metadata
    )
    return doc

def test_simple_json():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"key": "value"}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [json.dumps({"key": "value"}, ensure_ascii=False)]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_nested_json():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"my_data": {"key1": "value1", "key2": "value2"}}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [
        json.dumps({"my_data": {"key1": "value1"}}, ensure_ascii=False),
        json.dumps({"my_data": {"key2": "value2"}}, ensure_ascii=False)
    ]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_list_in_json():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"list": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [
        json.dumps({"list": [1, 2, 3, 4, 5, 6, 7, 8]}, ensure_ascii=False),
        json.dumps({"list": [9, 10, 11, 12, 13]}, ensure_ascii=False)
    ]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_large_values():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"key": "a" * 50}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [json.dumps({"key": "a" * 50}, ensure_ascii=False)]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_empty_json():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = []
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_single_large_value_exceeding_max_length():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"key": "a" * (CHUNK_SIZE + 50)}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [json.dumps({"key": "a" * (CHUNK_SIZE + 50)}, ensure_ascii=False)]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

# TODO the chunks are slightly larger than what is expected.
def test_complex_nested_json():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {
        "level1": {
            "level2": {
                "level3a": {"key1": "value1", "key2": "value2"},
                "level3b": "value3"
            },
            "level2b": ["item1", "item2", {"key3": "value4"}]
        },
        "level1b": "value5"
    }
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [
        json.dumps({"level1": {"level2": {"level3a": {"key1": "value1"}}}}, ensure_ascii=False),
        json.dumps({"level1": {"level2": {"level3a": {"key2": "value2"}}}}, ensure_ascii=False),
        json.dumps({"level1": {"level2": {"level3b": "value3"}}}, ensure_ascii=False),
        json.dumps({"level1": {"level2b": ["item1"]}}, ensure_ascii=False),
        json.dumps({"level1": {"level2b": ["item2"]}}, ensure_ascii=False),
        json.dumps({"level1": {"level2b": [{"key3": "value4"}]}}, ensure_ascii=False),
        json.dumps({"level1b": "value5"}, ensure_ascii=False)
    ]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_json_with_multiple_types():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {
        "int": 1,
        "float": 1.5,
        "string": "text",
        "bool": True,
        "none": None,
        "list": [1, "two", {"three": 3}]
    }
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [
        json.dumps({"int": 1, "float": 1.5}, ensure_ascii=False),
        json.dumps({"string": "text", "bool": True}, ensure_ascii=False),
        json.dumps({"none": None}, ensure_ascii=False),
        json.dumps({"list": [1, "two", {"three": 3}]}, ensure_ascii=False)
    ]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_large_nested_list():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"numbers": list(range(10))}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    # Adjust expected_contents based on CHUNK_SIZE and actual splitting behavior
    expected_contents = [
        json.dumps({"numbers": data["numbers"][0:7]}, ensure_ascii=False),
        json.dumps({"numbers": data["numbers"][7:10]}, ensure_ascii=False)
    ]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_unicode_characters():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"greeting": "こんにちは世界"}  # "Hello World" in Japanese
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [json.dumps({"greeting": "こんにちは世界"}, ensure_ascii=False)]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents

def test_special_characters():
    chunker = JsonChunker(CHUNK_SIZE)
    data = {"path": "C:\\Users\\name\\file.txt"}
    doc = create_document(data)
    result_chunks = chunker.chunk(doc)
    expected_contents = [json.dumps({"path": "C:\\Users\\name\\file.txt"}, ensure_ascii=False)]
    result_contents = [chunk.content for chunk in result_chunks]
    assert result_contents == expected_contents
