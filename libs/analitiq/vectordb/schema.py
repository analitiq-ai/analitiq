from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Chunk(BaseModel):
    """Represents a chunk of text in a document.

    :param project_name: The name of the project the chunk belongs to.
    :type project_name: str
    :param document_name: The name of the document the chunk belongs to.
    :type document_name: str
    :param document_type: The type of the document. (optional)
    :type document_type: str, optional
    :param content: The content of the chunk.
    :type content: str
    :param source: The source of the chunk.
    :type source: str
    :param document_num_char: The number of characters in the document.
    :type document_num_char: int
    :param chunk_num_char: The number of characters in the chunk.
    :type chunk_num_char: int
    :param content_kw: the keywords for keyword search in the chunks
    :type content_kw: str
    """

    project_name: str = None
    document_name: str = None
    document_type: Optional[str] = None
    content: str = None
    source: str
    date_loaded: Optional[datetime] = None
    document_num_char: int
    chunk_num_char: int
    content_kw: str = None
