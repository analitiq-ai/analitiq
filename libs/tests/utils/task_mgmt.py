import unittest
from unittest.mock import MagicMock, call
from analitiq.utils.task_mgmt import TaskManager


class TestCombineTasksPairwise(unittest.TestCase):
    def setUp(self):
        self.task_manager = TaskManager()
        self.llm_mock = MagicMock()
        self.user_prompt = "Please assist in combining these tasks."

    def test_combine_tasks_pairwise(self):
        tasks = {
            "Task1": {"Name": "Query data", "Using": "SQL", "Description": "Query sales database"},
            "Task2": {"Name": "Aggregate data", "Using": "SQL", "Description": "Aggregate sales data"},
            "Task3": {"Name": "Sort data", "Using": "SQL", "Description": "Sort sales data"},
        }

        # Setup the mock to return a response indicating tasks can be combined
        mock_response = MagicMock()
        mock_response.value = "Can combine tasks."
        self.llm_mock.llm_combine_tasks_pairwise.return_value = mock_response

        # Run the combine_tasks_pairwise method
        combined_tasks = self.task_manager.combine_tasks_pairwise(self.llm_mock, self.user_prompt, tasks)

        # Expected result
        expected = {
            "Task1": {
                "Name": "Query data",
                "Using": "SQL",
                "Description": "Query sales database. Aggregate sales data. Sort sales data",
            }
        }
        self.assertEqual(combined_tasks, expected)

    def test_do_not_combine_if_different_tools(self):
        tasks = {
            "Task1": {"Name": "Query data", "Using": "SQL", "Description": "Query sales database"},
            "Task2": {"Name": "Visualize data", "Using": "DataViz", "Description": "Visualize the data"},
        }

        # Run the combine_tasks_pairwise method
        combined_tasks = self.task_manager.combine_tasks_pairwise(self.llm_mock, self.user_prompt, tasks)

        # Expected result, tasks should remain unchanged since they use different tools
        self.assertEqual(combined_tasks, tasks)

    def test_do_combine_only_consecutive_tools(self):
        tasks = {
            "Task1": {"Name": "Query data", "Using": "SQL", "Description": "Query sales database"},
            "Task2": {"Name": "Aggregate data", "Using": "SQL", "Description": "Aggregate sales data"},
            "Task3": {"Name": "Visualize data", "Using": "DataViz", "Description": "Visualize the data"},
            "Task4": {"Name": "Query data", "Using": "SQL", "Description": "Query sales database"},
            "Task5": {"Name": "Aggregate data", "Using": "SQL", "Description": "Aggregate sales data"},
        }

        # Define side_effect function to dynamically respond based on input
        def side_effect(user_prompt, task1, task2):
            if task1["Using"] == task2["Using"]:
                if (task1 is tasks["Task1"] and task2 is tasks["Task2"]) or (
                    task1 is tasks["Task4"] and task2 is tasks["Task5"]
                ):
                    return MagicMock(value="Can combine tasks.")
                elif task1 is tasks["Task2"] and task2 is tasks["Task3"]:
                    return MagicMock(value="Cannot combine tasks.")
            return MagicMock(value="Cannot combine tasks.")

        self.llm_mock.llm_combine_tasks_pairwise.side_effect = side_effect

        # Run the combine_tasks_pairwise method
        combined_tasks = self.task_manager.combine_tasks_pairwise(self.llm_mock, self.user_prompt, tasks)

        expected = {
            "Task1": {
                "Name": "Query data",
                "Using": "SQL",
                "Description": "Query sales database. Aggregate sales data",
            },
            "Task3": {"Name": "Visualize data", "Using": "DataViz", "Description": "Visualize the data"},
            "Task4": {
                "Name": "Query data",
                "Using": "SQL",
                "Description": "Query sales database. Aggregate sales data",
            },
        }

        self.assertEqual(combined_tasks, expected)


if __name__ == "__main__":
    unittest.main()
