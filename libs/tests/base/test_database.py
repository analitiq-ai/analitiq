import unittest
from unittest.mock import MagicMock
from libs.analitiq.base.Database import DatabaseWrapper

class TestDatabaseWrapper(unittest.TestCase):
    def setUp(self):
        # Mocking the parameters dictionary for the database connection
        self.params = {
            "type": "postgres",
            "user": "postgres",
            "password": "root",
            "host": "localhost",
            "port": "5432",
            "dbname": "analitiq",
            "db_schemas": ["schema1", "schema2"]
        }

        # Mocking the DatabaseWrapper class with MagicMock
        self.database_wrapper = DatabaseWrapper(self.params)

    def tearDown(self):
        pass

    def test_get_schema_names(self):
        # Mocking the inspector and its method get_schema_names
        inspector_mock = MagicMock()
        inspector_mock.get_schema_names.return_value = [ 'information_schema',"public", "schema1", "schema2"]

        # Setting the inspector attribute of the engine to the mocked inspector
        self.database_wrapper.engine.inspector = inspector_mock

        # Calling the method to test
        schema_names = self.database_wrapper.get_schema_names()

        # Asserting the returned schema names
        self.assertEqual(schema_names, [ 'information_schema',"public", "schema1", "schema2"])

    def test_get_tables_in_schema(self):
        # Mocking the inspector and its method get_table_names
        inspector_mock = MagicMock()
        inspector_mock.get_table_names.return_value = ["table1", "table2"]

        # Setting the inspector attribute of the engine to the mocked inspector
        self.database_wrapper.engine.inspector = inspector_mock

        # Calling the method to test
        table_names = self.database_wrapper.get_tables_in_schema("schema1")

        # Asserting the returned table names
        self.assertEqual(table_names, ["table1", "table2"])

    def test_get_schemas_and_tables(self):
        # Mocking the inspector and its methods get_schema_names and get_table_names
        inspector_mock = MagicMock()
        inspector_mock.get_schema_names.return_value = [ 'information_schema', "schema1", "schema2"]
        inspector_mock.get_table_names.side_effect = [["table1", "table2"], []]

        # Setting the inspector attribute of the engine to the mocked inspector
        self.database_wrapper.engine.inspector = inspector_mock

        # Calling the method to test
        schemas_and_tables = self.database_wrapper.get_schemas_and_tables([  "schema1", "schema2" ])
        # Asserting the returned schema and table details
        expected_response = ['schema1.table1.column1 (TEXT), schema1.table1.column2 (INTEGER)', 'schema1.table2.column1 (TEXT)']
        self.assertEqual(schemas_and_tables, expected_response)


if __name__ == '__main__':
    unittest.main()
