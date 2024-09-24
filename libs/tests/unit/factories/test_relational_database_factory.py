# pylint: disable=redefined-outer-name

import pytest
import os
from dotenv import load_dotenv
from analitiq.factories.relational_database_factory import RelationalDatabaseFactory
from analitiq.databases.relational.postgres.postgres_connector import PostgresConnector


@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv(".env", override=True)


@pytest.fixture(autouse=True, scope="module")
def params():
    return {
        "username": os.getenv("DB_USERNAME"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "db_name": os.getenv("DB_NAME"),
        "db_schemas": [os.getenv("DB_SCHEMAS")],
    }


def test_create_postgres_database(params):
    params["type"] = "postgres"
    db = RelationalDatabaseFactory.create_database(params)
    assert isinstance(db, PostgresConnector)


def submit_empty_params():
    params = {}
    with pytest.raises(ValueError) as excinfo:
        RelationalDatabaseFactory.create_database(params)
    assert "Unknown relational database type: unknown_db" in str(excinfo.value)


def test_create_unknown_database(params):
    params["type"] = "oracle"
    with pytest.raises(ValueError) as excinfo:
        RelationalDatabaseFactory.create_database(params)
    assert f"Unknown relational database type: {params['type']}" in str(excinfo.value)
