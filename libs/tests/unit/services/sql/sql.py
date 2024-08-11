import unittest
from unittest.mock import patch, MagicMock
from analitiq.agents.sql.sql import Sql


class TestSqlMethods(unittest.TestCase):
    def setUp(self):
        # Patch the dependencies
        self.patcher_db = patch("analitiq.base.GlobalConfig.get_database")
        self.patcher_llm = patch("analitiq.base.GlobalConfig.get_llm")
        self.mock_db = self.patcher_db.start()
        self.mock_llm = self.patcher_llm.start()

        # Create an instance of the Sql class
        self.sql_instance = Sql()

        # Setup mock responses for db and llm
        self.sql_instance.db.get_usable_table_names = MagicMock(return_value=["sales", "users"])
        self.sql_instance.llm.invoke = MagicMock()

    def tearDown(self):
        self.patcher_db.stop()
        self.patcher_llm.stop()

    def test_get_sql_v2_success(self):
        # Input setup
        user_prompt = "Query sales data to get customers and sales volume."
        relevant_tables = "sales: customer, sales_amount"

        # Mock LLM response
        self.sql_instance.llm.invoke = MagicMock(
            return_value={
                "sql": "SELECT customer, SUM(sales_amount) AS total_sales FROM sales GROUP BY customer ORDER BY total_sales DESC LIMIT 10"
            }
        )

        # Execute the method
        sql_query = self.sql_instance.get_sql_v2(user_prompt, relevant_tables)
        expected_sql = "SELECT customer, SUM(sales_amount) AS total_sales FROM sales GROUP BY customer ORDER BY total_sales DESC LIMIT 10"
        self.assertEqual(sql_query, expected_sql)

    def test_get_sql_v2_no_tables_found(self):
        user_prompt = "Query data."
        relevant_tables = ""

        # Expected behavior when no tables are found
        self.sql_instance.llm.invoke = MagicMock(return_value={"sql": ""})

        # Execute the method
        sql_query = self.sql_instance.get_sql_v2(user_prompt, relevant_tables)
        self.assertEqual(sql_query, "")

    def test_get_sql_v2_error_handling(self):
        user_prompt = "Complex query generating an error."
        relevant_tables = "sales: customer, sales_amount"
        last_error = {"response": "error", "error": "Syntax error"}

        # Simulate an error from the LLM
        self.sql_instance.llm.invoke = MagicMock(side_effect=Exception("Failed to generate SQL"))

        # Test error handling
        with self.assertRaises(Exception):
            self.sql_instance.get_sql_v2(user_prompt, relevant_tables, last_error)

    def test_get_sql_failover_success(self):
        user_prompt = "Query sales data to get customers and sales volume, aggregate by customer, and sort by total sales to get top 10 customers."
        relevant_tables = """
        sales: customer, sales_amount
        users: customer, name
        """

        # Simulate failover scenario
        self.sql_instance.llm.invoke = MagicMock(
            return_value={"sql": "SELECT customer, SUM(sales_amount) FROM sales GROUP BY customer"}
        )

        # Execute the method
        sql_query = self.sql_instance.get_sql_failover(user_prompt, relevant_tables)
        self.assertIn("FROM sales", sql_query)

    def test_get_sql_failover_fallback(self):
        user_prompt = "Query sales data to get customers and sales volume, aggregate by customer, and sort by total sales to get top 10 customers."
        relevant_tables = """
        sales: customer, sales_amount
        users: customer, name
        """

        # Force primary method to fail and check fallback
        self.sql_instance.llm.invoke = MagicMock(side_effect=Exception("Primary method failed"))

        # Check if the method properly handles the failover
        sql_query = self.sql_instance.get_sql_failover(user_prompt, relevant_tables)
        self.assertIn("FROM sales", sql_query)  # Assuming the fallback generates a valid SQL still


if __name__ == "__main__":
    unittest.main()
