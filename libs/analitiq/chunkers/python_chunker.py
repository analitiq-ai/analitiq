"""
Filename: analitiq/chunkers/python_chunker.py
"""

from typing import List
from analitiq.base.base_chunker import BaseChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.docstore.document import Document
from analitiq.base.base_chunker import CHUNK_SIZE, CHUNK_OVERLAP
from analitiq.loaders.documents.schemas import  Chunk, DocumentSchema
from analitiq.utils.keyword_extractions import extract_keywords


class PythonChunker(BaseChunker):
    def __init__(self, max_chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: DocumentSchema) -> List[Chunk]:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=int(self.max_chunk_size),
            chunk_overlap=int(self.chunk_overlap)
        )

        langchain_document = Document(page_content=document.document_content)

        chunks = splitter.split_documents([langchain_document])

        return_chunks = []
        for chunk in chunks:
            chunk_text = chunk.page_content
            chunk_obj = Chunk(
                content=chunk_text,
                document_num_char=len(document.document_content),
                document_name=document.metadata.document_name,
                document_uuid = document.uuid,
                chunk_num_char=len(chunk_text),
                content_kw = extract_keywords(chunk_text)
            )
            return_chunks.append(chunk_obj)


        return return_chunks

