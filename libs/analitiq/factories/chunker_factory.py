"""
Filename: chunker_factory.py

"""
from analitiq.base.base_chunker import BaseChunker

class ChunkerFactory:
    @staticmethod
    def get_chunker(document_type: str) -> BaseChunker:
        if document_type == 'sql':
            from analitiq.chunkers.sql_chunker import SQLChunker
            return SQLChunker()
        elif document_type == 'python':
            from analitiq.chunkers.python_chunker import PythonChunker
            return PythonChunker()
        elif document_type == 'yaml':
            from analitiq.chunkers.json_chunker import JsonChunker
            return JsonChunker()
        else:
            from analitiq.chunkers.text_chunker import TextChunker
            return TextChunker()
