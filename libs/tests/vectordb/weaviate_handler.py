import pytest
import os
from libs.analitiq.vectordb.weaviate_handler import WeaviateHandler
from weaviate.collections.classes.internal import QueryReturn

COLLECTION_NAME = "test_collection"

@pytest.fixture(scope="module")
def params():
    return {
        "collection_name": COLLECTION_NAME,
        "host": "https://gfypabwerr6kjeih1h2n7a.c0.europe-west3.gcp.weaviate.cloud",
        "api_key": "q9K1RP97dZpvWFNIh6BEbxziR9G5uWVsWg0I",
    }

@pytest.fixture(scope="module")
def weaviate_handler(params):
    handler = WeaviateHandler(params)
    handler.connect()
    yield handler
    handler.close()


def test_create_collection(weaviate_handler):
    check = weaviate_handler.client.collections.exists(COLLECTION_NAME)
    if check:
        weaviate_handler.delete_collection(COLLECTION_NAME)

    weaviate_handler.client.connect()
    collection_name = weaviate_handler.create_collection(COLLECTION_NAME)
    assert collection_name == COLLECTION_NAME

    weaviate_handler.client.connect()
    check = weaviate_handler.client.collections.exists(COLLECTION_NAME)
    assert check == True


def test_load_single_document(weaviate_handler):
    test_document_path = "test_document.txt"
    with open(test_document_path, "w") as f:
        f.write("This is a test document.")

    response = weaviate_handler.load_file(test_document_path)

    assert response > 0

    os.remove(test_document_path)


def test_load_documents_from_directory(weaviate_handler):
    test_dir = "test_dir"
    os.makedirs(test_dir, exist_ok=True)

    for i in range(3):
        with open(os.path.join(test_dir, f"test_document_{i}.txt"), "w") as f:
            f.write(f"This is test document {i}.")

    response = weaviate_handler.load_dir(test_dir, "txt")

    assert response >= 3

    for i in range(3):
        os.remove(os.path.join(test_dir, f"test_document_{i}.txt"))
    os.rmdir(test_dir)


def test_keyword_search(weaviate_handler):
    query = "test document"
    result = weaviate_handler.kw_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_vector_search(weaviate_handler):
    query = "test document"
    result = weaviate_handler.vector_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_hybrid_search(weaviate_handler):
    query = "test document"
    result = weaviate_handler.hybrid_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def count_objects_grouped_by(weaviate_handler):
    expected_result_as_str = "[<AggregateGroup with a grouped_by <GroupedBy with a prop 'document_name', and a value 'test_document.txt'>, and a total_count 1>, <AggregateGroup with a grouped_by <GroupedBy with a prop 'document_name', and a value 'test_document_1.txt'>, and a total_count 1>, <AggregateGroup with a grouped_by <GroupedBy with a prop 'document_name', and a value 'test_document_0.txt'>, and a total_count 1>, <AggregateGroup with a grouped_by <GroupedBy with a prop 'document_name', and a value 'test_document_2.txt'>, and a total_count 1>]"

    result = weaviate_handler.count_objects_grouped_by("document_name")
    result_as_str = str(result)
    assert result_as_str == expected_result_as_str, "Result is not matching the expected structure"


def test_delete_collection(weaviate_handler):
    weaviate_handler.client.connect()
    result = weaviate_handler.delete_collection(COLLECTION_NAME)
    assert result == True

    weaviate_handler.client.connect()
    check = weaviate_handler.client.collections.exists(COLLECTION_NAME)
    assert check == False
