# File: test_weaviate.py
import unittest
from unittest.mock import patch, MagicMock
from libs.analitiq.vectordb.weaviate import WeaviateHandler


class TestWeaviateHandler(unittest.TestCase):

    @patch('libs.analitiq.vectordb.weaviate.BaseVDBHandler.__init__')
    @patch('libs.analitiq.vectordb.weaviate.WeaviateHandler.try_connect')
    def test_constructor(self, mock_try_connect, mock_init):
        mock_try_connect.return_value = True
        obj = WeaviateHandler({"any_param": "any_value"})
        self.assertIsNotNone(obj)
        self.assertTrue(mock_init.called)
        self.assertTrue(mock_try_connect.called)

    @patch('libs.analitiq.vectordb.weaviate.weaviate.connect_to_wcs')
    @patch('libs.analitiq.vectordb.weaviate.WeaviateHandler.create_collection')
    def test_connect(self, mock_create_collection, mock_connect_to_wcs):
        client = MagicMock()
        client.collections.exists.return_value = False
        mock_connect_to_wcs.return_value = client
        obj = WeaviateHandler({"host": "any_host", "api_key": "any_key", "collection_name": "any_name"})
        obj.connect()
        self.assertTrue(mock_connect_to_wcs.called)
        self.assertTrue(client.collections.exists.called)
        self.assertTrue(mock_create_collection.called)

    @patch('libs.analitiq.vectordb.weaviate.os.path')
    def test_load(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.isdir.return_value = False
        mock_path.splitext.return_value = ["some_path", ".py"]
        obj = WeaviateHandler({"collection_name": "any_name"})
        obj._chunk_load_file_or_directory = MagicMock()
        obj.load("/some/path")
        self.assertTrue(obj._chunk_load_file_or_directory.called)

    # Add more tests as per your methods in the WeaviateHandler


if __name__ == "__main__":
    unittest.main()

