from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


def current_timestamp():
    return datetime.utcnow().isoformat()


class DocumentTypeEnum(str, Enum):
    txt = 'txt'
    yaml = 'yaml'
    yml = 'yaml'
    py = 'python'
    sql = 'sql'
    md = 'markup'
    pdf = 'pdf'
    json = 'json'


class DocumentSourceEnum(str, Enum):
    sys = 'system'
    upl = 'upload'


class DocumentSchema(BaseModel):
    """ Schema for DynamoDB document object"""
    uuid: str
    document_name: str
    document_content: str
    document_type: DocumentTypeEnum = DocumentTypeEnum.txt
    document_source: DocumentSourceEnum = DocumentSourceEnum.upl
    document_tags: Optional[List[str]] = []
    created_ts: str = Field(default_factory=current_timestamp)
    updated_ts: str = Field(default_factory=current_timestamp)
    deleted_ts: Optional[str] = None


class Chunk(BaseModel):
    """Represents a chunk of text in a document.

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

    content: str = None
    document_name: str = None
    document_type: DocumentTypeEnum = 'txt'
    document_source: str
    document_num_char: int
    document_uuid: str = None
    chunk_num_char: int
    content_kw: str = None
    created_ts: datetime = Field(default_factory=current_timestamp)
