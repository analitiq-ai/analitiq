# pylint: disable=redefined-outer-name
import pytest
import os
from dotenv import load_dotenv
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from weaviate.collections.classes.internal import QueryReturn

@pytest.fixture(autouse=True, scope="module")
def params(pytestconfig):
    load_dotenv(f"{pytestconfig.rootpath}/.env", override=True)
    return {
        "collection_name": "test",
        "tenant_name": "test_tenant",
        "type": os.getenv("VDB_TYPE"),
        "host": os.getenv("VDB_HOST"),
        "api_key": os.getenv("VDB_API_KEY"),
    }


@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv(".env", override=True)


@pytest.fixture(scope="module")
def vdb(params):
    handler = VectorDatabaseFactory.connect(params)
    yield handler


test_documents = [
    {
        "document_name": "test_document_1.txt",
        "content": "This is the first test document.",
    },
    {
        "document_name": "test_document_2.txt",
        "content": "Another document for testing.",
    },
    {
        "document_name": "project_plan.txt",
        "content": "This document contains the project plan.",
    },
    {
        "document_name": "summary_report.txt",
        "content": "The summary of all reports."
    },
    {
        "document_name": "test_document_3.txt",
        "content": "This document is for additional tests.",
    },
]


def create_documents(documents, test_dir: str = "test_dir"):
    os.makedirs(test_dir, exist_ok=True)

    for doc in documents:
        with open(os.path.join(test_dir, doc["document_name"]), "w") as f:
            f.write(doc["content"])

    print("Documents created successfully.")

def delete_documents(documents, test_dir: str = "test_dir"):
    for doc in documents:
        try:
            os.remove(os.path.join(test_dir, doc["document_name"]))
            print(f"Deleted {doc['document_name']} successfully.")
        except FileNotFoundError:
            print(f"{doc['document_name']} does not exist.")

    os.rmdir(test_dir)


def test_create_collection(vdb):
    collection_name = vdb.params.get("collection_name")

    with vdb:
        check = vdb.client.collections.exists(collection_name)

    if check:
        vdb.delete_collection(collection_name)

    response = vdb.create_collection(collection_name)
    assert response.name == collection_name.capitalize()

    with vdb:
        check = vdb.client.collections.exists(collection_name)

    assert check == True


def test_create_tenant(vdb):
    tenant_name = vdb.params.get("tenant_name")

    collection_name = vdb.params.get("collection_name")
    vdb.collection_add_tenant(tenant_name)

    with vdb:
        multi_collection = vdb.client.collections.get(collection_name)
        tenants = multi_collection.tenants.get()

    if tenant_name in tenants:
        result = True
    else:
        result = False

    assert result == True


def test_load_single_document(vdb):
    test_document_path = "document.txt"
    with open(test_document_path, "w") as f:
        f.write("This is a test document.")

    docs, chunks = vdb.load_file(test_document_path)

    assert chunks > 0

    os.remove(test_document_path)


def test_load_documents_from_directory(vdb):
    test_dir = "test_dir"
    create_documents(test_documents, test_dir)

    docs, chunks = vdb.load_dir(test_dir, "txt")

    assert chunks >= 3

    delete_documents(test_documents, test_dir)


def test_keyword_search(vdb):
    query = "test document"
    with vdb:
        result = vdb.kw_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_vector_search(vdb):
    query = "test document"

    result = vdb.vector_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_hybrid_search(vdb):
    query = "test document"

    result = vdb.hybrid_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_filter_count__equal(vdb):
    filter_expression = {
        "or": [
            {
                "and": [
                    {
                        "property": "document_name",
                        "operator": "like",
                        "value": "test_document",
                    },
                    {"property": "document_name", "operator": "like", "value": "1"},
                ]
            },
            {
                "and": [
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "test_document_1",
                    },
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "test_document_2",
                    },
                ]
            },
        ]
    }

    result = vdb.filter_count(filter_expression=filter_expression)

    assert result.total_count == 1


def test_filter_count_and(vdb):
    filter_expression = {
        "and": [
            {"property": "document_name", "operator": "like", "value": "test_document"},
            {"property": "content", "operator": "like", "value": "first"},
        ]
    }

    result = vdb.filter_count(filter_expression)

    assert result.total_count == 1


def test_filter_count__or(vdb):
    filter_expression = {
        "or": [
            {"property": "document_name", "operator": "like", "value": "summary"},
            {"property": "content", "operator": "like", "value": "project"},
        ]
    }


    result = vdb.filter_count(filter_expression)

    assert result.total_count == 2


def test_filter_count__simple_and_complex_filter(vdb):
    filter_expression = {
        "and": [
            {"property": "document_name", "operator": "like", "value": "test_document"},
            {
                "or": [
                    {"property": "content", "operator": "like", "value": "tests"},
                    {"property": "content", "operator": "like", "value": "testing"},
                ]
            },
        ]
    }


    result = vdb.filter_count(filter_expression)

    assert result.total_count == 2


def test_filter_count__complex_filter(vdb):
    filter_expression = {
        "and": [
            {
                "or": [
                    {"property": "document_name", "operator": "like", "value": "test"},
                    {
                        "property": "content",
                        "operator": "!=",
                        "value": "This is the first test document.",
                    },
                ]
            },
            {
                "or": [
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "project_plan",
                    },
                    {"property": "content", "operator": "like", "value": "project"},
                ]
            },
        ]
    }

    result = vdb.filter_count(filter_expression)

    assert result.total_count == 1


def test_filter_group_count(vdb):
    filter_expression = {
        "property": "document_name",
        "operator": "like",
        "value": "test",
    }

    result = vdb.filter_group_count(filter_expression, "document_name")

    # Assert that there are exactly 3 AggregateGroup objects
    assert len(result.groups) == 3

    # Assert that each AggregateGroup object has total_count = 1
    for group in result.groups:
        assert group.total_count == 1


def test_search_filter(vdb):
    query = "document"
    filter_expression = {
        "and": [
            {
                "or": [
                    {"property": "document_name", "operator": "like", "value": "test"},
                    {
                        "property": "content",
                        "operator": "!=",
                        "value": "This is the first test document.",
                    },
                ]
            }
        ]
    }

    result = vdb.search_filter(query, filter_expression)

    assert len(result.objects) == 4


def test_filter_count__like(vdb):
    filter_expression = {
        "or": [
            {
                "and": [
                    {"property": "document_name", "operator": "like", "value": "test*"},
                ]
            },
            {
                "and": [
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "project_plan",
                    },
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "test_document_1",
                    },
                ]
            },
        ]
    }

    result = vdb.filter_count(filter_expression)

    assert result.total_count == 3


def test_filter(vdb):
    filter_expression = {
        "and": [
            {"property": "document_name", "operator": "=", "value": "project_plan"},
        ]
    }

    result = vdb.filter(filter_expression)

    assert len(result.objects) == 1


def test_filter_delete(vdb):

    result = vdb.filter_delete('document_name', 'test_document_1')

    assert result.matches == 1
    assert result.successful == 1

def test_delete_on_uuids(vdb):
    result = vdb.delete_many_on_uuids(['12347c94-ee8a-40f9-9a2c-d2ed7003f7dd','12347c94-ee8a-40f9-9a2c-d2ed7003f7df'])
    assert result.matches == 0

def test_load_text(vdb):
    """Test loading manually text and make sure the UUID remains the same """
    vdb.load_text("This is another test document.", "test2", "txt", "4435056b-44b2-4935-a11f-2adb3c06b305", ["tag1","tag2"])

    filter_expression = {
        "and": [
            {"property": "document_uuid", "operator": "=", "value": "4435056b-44b2-4935-a11f-2adb3c06b305"}
        ]
    }

    response = vdb.search_filter('another', filter_expression)
    print(response)
    assert len(response) == 1
"""
def test_delete_collection(vdb):

    collection_name = vdb.params.get("collection_name")

    result = vdb.delete_collection(collection_name)

    assert result == True

    collection_name = vdb.params.get("collection_name")
    with vdb:
        check = vdb.client.collections.exists(collection_name)
    assert check == False
"""