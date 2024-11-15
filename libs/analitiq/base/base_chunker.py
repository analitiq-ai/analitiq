"""
Filename: analitiq/base/base_chunker.py

"""

from abc import ABC
from typing import List
from analitiq.loaders.documents.schemas import  Chunk, DocumentSchema

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

class BaseChunker(ABC):
    def chunk(self, document: DocumentSchema) -> List[Chunk]:
        raise NotImplementedError
