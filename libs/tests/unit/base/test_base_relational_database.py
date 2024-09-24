import pytest
from unittest.mock import patch, MagicMock
from analitiq.databases.relational.postgres.postgres_connector import PostgresConnector
from sqlalchemy.exc import DatabaseError


@pytest.fixture
def db_params():
    return {
        'username': 'user',
        'password': 'pass',
        'host': 'localhost',
        'port': '5432',
        'db_name': 'test_db',
    }


@pytest.fixture
def db_instance(db_params):
    with patch('analitiq.databases.relational.postgres.postgres_connector.create_engine'):
        db = PostgresConnector(db_params)
    return db


def test_get_schema_names(db_instance):
    with patch('analitiq.base.base_relational_database.inspect') as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.get_schema_names.return_value = ['public', 'schema1']
        mock_inspect.return_value = mock_inspector

        schemas = db_instance.get_schema_names()
        assert schemas == ['public', 'schema1']


def test_get_tables_in_schema(db_instance):
    with patch('analitiq.base.base_relational_database.inspect') as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ['table1', 'table2']
        mock_inspect.return_value = mock_inspector

        tables = db_instance.get_tables_in_schema('public')
        assert tables == ['table1', 'table2']


def test_get_schemas_and_tables(db_instance):
    with patch('analitiq.base.base_relational_database.inspect') as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.get_schema_names.return_value = ['public', 'schema1']
        mock_inspector.get_table_names.return_value = ['table1']
        mock_inspector.get_columns.return_value = [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'VARCHAR'},
        ]
        mock_inspect.return_value = mock_inspector

        result = db_instance.get_schemas_and_tables(['public'])
        expected = ['public.table1.id (INTEGER), public.table1.name (VARCHAR)']
        assert result == expected


def test_get_table_columns(db_instance):
    with patch('analitiq.base.base_relational_database.inspect') as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.get_columns.return_value = [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'VARCHAR'},
        ]
        mock_inspect.return_value = mock_inspector

        columns = db_instance.get_table_columns('table1', 'public')
        assert columns == [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'VARCHAR'},
        ]


def test_get_numeric_columns():
    columns = [
        {'name': 'id', 'type': 'INTEGER'},
        {'name': 'name', 'type': 'VARCHAR'},
        {'name': 'value', 'type': 'DECIMAL'},
    ]
    numeric_columns = PostgresConnector.get_numeric_columns(columns)
    assert numeric_columns == {'id': 'INTEGER', 'value': 'DECIMAL'}


def test_get_row_count(db_instance):
    with patch.object(db_instance, 'engine') as mock_engine:
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_result = MagicMock()
        mock_connection.execute.return_value = mock_result
        mock_result.scalar.return_value = 100

        count = db_instance.get_row_count('public', 'table1')
        assert count == 100


def test_get_summary_statistics(db_instance):
    with patch.object(db_instance, 'engine') as mock_engine:
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_result = MagicMock()
        mock_connection.execute.return_value = mock_result
        mock_result.fetchone.return_value = (1, 10, 5.5)

        min_val, max_val, avg_val = db_instance.get_summary_statistics('public', 'table1', 'value')
        assert min_val == 1
        assert max_val == 10
        assert avg_val == 5.5


def test_execute_sql(db_instance):
    with patch('analitiq.base.base_relational_database.read_sql') as mock_read_sql:
        mock_df = MagicMock()
        mock_read_sql.return_value = mock_df

        success, result = db_instance.execute_sql('SELECT * FROM table1')
        assert success is True
        assert result == mock_df


def test_execute_sql_error(db_instance):
    with patch('analitiq.base.base_relational_database.read_sql') as mock_read_sql:
        mock_read_sql.side_effect = DatabaseError(
            statement='SELECT * FROM table1',
            params=None,
            orig=Exception('Database error')
        )

        success, result = db_instance.execute_sql('SELECT * FROM table1')
        assert success is False
        assert result is None


def test_run(db_instance):
    with patch.object(db_instance.db, 'run', return_value='Query result') as mock_run:
        result = db_instance.run('SELECT * FROM table1')
        mock_run.assert_called_once_with('SELECT * FROM table1', include_columns=True)
        assert result == 'Query result'


def test_run_error(db_instance):
    with patch.object(db_instance.db, 'run', side_effect=Exception('Query error')):
        with pytest.raises(Exception) as excinfo:
            db_instance.run('SELECT * FROM table1')
        assert 'Query error' in str(excinfo.value)


def test_create_session(db_params):
    with patch('analitiq.databases.relational.postgres.postgres_connector.create_engine'):
        db = PostgresConnector(db_params)
        session = db.create_session()
        assert session is not None


def test_create_db(db_params):
    with patch('analitiq.databases.relational.postgres.postgres_connector.create_engine'):
        # Patch 'create_db' during initialization to prevent the first call to SQLDatabase
        with patch.object(PostgresConnector, 'create_db') as mock_create_db_init:
            db = PostgresConnector(db_params)
            # Ensure the initialization doesn't call SQLDatabase
            mock_create_db_init.assert_called_once()

        # Now patch 'SQLDatabase' to monitor its calls
        with patch('analitiq.base.base_relational_database.SQLDatabase') as mock_sql_database:
            # Call the actual 'create_db' method
            db_instance = db.create_db()
            mock_sql_database.assert_called_once_with(db.engine)