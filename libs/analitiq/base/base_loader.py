"""
Filename: analitiq/base/base_chunker.py

"""

from abc import ABC
from typing import List
from analitiq.loaders.documents.schemas import  DocumentSchema


class BaseLoader(ABC):
    def load(self) -> List[DocumentSchema]:
        raise NotImplementedError
