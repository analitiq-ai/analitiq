import os
import unittest
from unittest.mock import patch, MagicMock, create_autospec
from libs.analitiq.vectordb.weaviate import WeaviateHandler
import weaviate
from weaviate.util import generate_uuid5
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant
from typing import Optional
from pydantic import BaseModel

# Existing WeaviateHandler class code
# ... (paste the WeaviateHandler class code here) ...

class TestWeaviateHandler(unittest.TestCase):

    @patch('weaviate.connect_to_wcs')
    @patch('libs.analitiq.vectordb.weaviate.DocumentChunkLoader')
    def setUp(self,  MockChunkLoader, MockConnectToWCS):
        self.mock_client = MockConnectToWCS.return_value
        self.mock_chunk_processor = MockChunkLoader.return_value
        self.params = {
            'host': 'https://test-analitiq-5mwe1rof.weaviate.network',
            'api_key': 'Wy1q2YlOFAMETXA7OeUBAvNS4iUx3qnIpy24',
            'collection_name': 'analitiq123123'
        }
        self.handler = WeaviateHandler(self.params)

    @patch('libs.analitiq.vectordb.weaviate.weaviate.connect_to_wcs')
    def test_connect(self, mock_connect):
        mock_connect.return_value = self.mock_client
        self.mock_client.collections.exists.return_value = False
        self.handler.connect()

        mock_connect.assert_called_once_with(
            cluster_url=self.params['host'],
            auth_credentials=AuthApiKey(self.params['api_key'])
        )
        self.assertEqual(self.handler.client, self.mock_client) 

    def test_create_collection(self):
        self.mock_client.collections.exists.return_value = False
        self.handler.create_collection() 
        self.mock_client.collections.exists.assert_called_with(self.params['collection_name'])
        
    def test_load(self):
      
        # Test case for loading a valid file
        with patch.object(self.handler, '_chunk_load_file_or_directory') as mock_chunk_load:
            test_file = 'test_schema.yml'
            self.handler.load(test_file)
            mock_chunk_load.assert_called_once_with(test_file, "yml")

        # Test case for invalid file extension
        with self.assertRaises(ValueError):
            self.handler.load('test_schema.yml', file_ext='invalid')

        # Test case for non-existent file or directory
        with self.assertRaises(FileNotFoundError):
            self.handler.load('non_existent_file.txt')
            
    
    @patch.object(WeaviateHandler, 'close')
    def test_get_many_like(self, mock_close):
        mock_response = MagicMock()
        self.handler.collection.query.fetch_objects.return_value = mock_response

        result = self.handler.get_many_like('source', 'test')
        print(result)
        self.handler.collection.query.fetch_objects.assert_called_once_with(
            filters=Filter.by_property("source").like("*test*")
        )
        self.assertEqual(result, mock_response)
        mock_close.assert_called_once()

    @patch.object(WeaviateHandler, 'close')
    def test_delete_collection(self, mock_close):
        self.handler.collection.delete.return_value = True

        result = self.handler.delete_collection(self.params['collection_name'])

        self.handler.client.collections.delete.assert_called_once_with(self.params['collection_name'])
        self.assertTrue(result)
        mock_close.assert_called_once()

    @patch.object(WeaviateHandler, 'close')
    def test_delete_many_like(self, mock_close):
        self.handler.collection.data.delete_many.return_value = None

        result = self.handler.delete_many_like('source', 'test')

        self.handler.collection.data.delete_many.assert_called_once_with(
            where=Filter.by_property('source').like("test*")
        )
        self.assertTrue(result)
        mock_close.assert_called_once()

    @patch.object(WeaviateHandler, 'close')
    def test_kw_search(self, mock_close):
        mock_response = MagicMock()
        self.handler.collection.query.bm25.return_value = mock_response

        result = self.handler.kw_search('test query', limit=5)

        self.handler.collection.query.bm25.assert_called_once_with(
            query='test query',
            query_properties=['content'],
            limit=5
        )
        self.assertEqual(result, mock_response)
        mock_close.assert_called_once()

if __name__ == '__main__':
    unittest.main()