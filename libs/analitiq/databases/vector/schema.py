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


class DocumentMetadata(BaseModel):
    """

    Class representing metadata for a document.

    :param document_name: The name of the document.
    :param document_type: The type of the document. Defaults to DocumentTypeEnum.txt.
    :param document_source: The source of the document. Defaults to DocumentSourceEnum.upl.
    :param document_tags: Optional list of tags associated with the document.
    :param created_ts: The timestamp when the document metadata was created.

    """
    document_name: str
    document_type: DocumentTypeEnum = DocumentTypeEnum.txt
    document_source: DocumentSourceEnum = DocumentSourceEnum.upl
    document_tags: Optional[List[str]] = None
    created_ts: str = Field(default_factory=current_timestamp)


class DocumentSchema(DocumentMetadata):
    """

    class DocumentSchema(DocumentMetadata):
        uuid: str
        document_content: str
        updated_ts: str = Field(default_factory=current_timestamp)
        deleted_ts: Optional[str] = None

    """
    uuid: str
    document_content: str
    updated_ts: str = Field(default_factory=current_timestamp)
    deleted_ts: Optional[str] = None


class Chunk(DocumentMetadata):
    """

    class Chunk(DocumentMetadata):
        content: str = None
        document_num_char: int
        document_uuid: str = None
        chunk_num_char: int
        content_kw: str = None

    """
    content: str = None
    document_num_char: int
    document_uuid: str = None
    chunk_num_char: int
    content_kw: str = None
