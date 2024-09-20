import pytest
import os
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock
from analitiq.databases.relational.postgres.postgres_connector import PostgresConnector


@pytest.fixture(autouse=True, scope='module')
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv('.env', override=True)


@pytest.fixture(autouse=True, scope="module")
def params():
    return {
        'username': os.getenv('DB_USERNAME'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'db_name': os.getenv('DB_NAME'),
        'db_schemas': [os.getenv('DB_SCHEMAS')]
    }


def test_create_engine_without_schemas():
    params = {
        'username': 'user',
        'password': 'pass',
        'host': 'localhost',
        'port': '5432',
        'db_name': 'test_db',
    }
    with patch('analitiq.databases.relational.postgres.postgres_connector.create_engine') as mock_create_engine:
        db = PostgresConnector(params)
        expected_connection_string = 'postgresql+psycopg2://user:pass@localhost:5432/test_db'
        mock_create_engine.assert_called_once_with(expected_connection_string, **{})


def test_create_engine_with_schemas():
    params = {
        'username': 'user',
        'password': 'pass',
        'host': 'localhost',
        'port': '5432',
        'db_name': 'test_db',
        'db_schemas': ['public', 'schema1'],
    }
    with patch('analitiq.databases.relational.postgres.postgres_connector.create_engine') as mock_create_engine:
        db = PostgresConnector(params)
        expected_connection_string = 'postgresql+psycopg2://user:pass@localhost:5432/test_db'
        engine_options = {'connect_args': {'options': '-csearch_path=public,schema1'}}
        mock_create_engine.assert_called_once_with(expected_connection_string, **engine_options)
