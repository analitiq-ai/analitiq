from typing import Union, List, Dict, Any, Optional
from pydantic import BaseModel


class VectoreStoreCollection(BaseModel):
    name: str
    metadata: Union[Dict[str, Any], None] = None


class FileMetadata(BaseModel):
    company_name: str
    document_name: str
    document_type: str
    document_categories: List[str]
    url: str


class DocChunk(BaseModel):
    """Represents a chunk of text in a document."""

    project_name: str = None
    document_name: str = None
    document_type: Optional[str] = None
    content: str = None
    source: str
    document_num_char: int
    chunk_num_char: int
