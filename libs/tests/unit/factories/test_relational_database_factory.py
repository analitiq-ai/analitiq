import pytest
import os
from dotenv import load_dotenv
from analitiq.factories.relational_database_factory import RelationalDatabaseFactory
from analitiq.relational_databases.postgres.postgres_rdb import PostgresDatabaseWrapper


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


def test_create_postgres_database(params):

    db = RelationalDatabaseFactory.create_database('postgres', params)
    assert isinstance(db, PostgresDatabaseWrapper)


def test_create_unknown_database():
    params = {}
    with pytest.raises(ValueError) as excinfo:
        RelationalDatabaseFactory.create_database('unknown_db', params)
    assert 'Unknown relational database type: unknown_db' in str(excinfo.value)