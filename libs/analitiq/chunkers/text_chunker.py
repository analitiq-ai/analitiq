"""
Filename: analitiq/chunkers/text_chunker.py

Class will split a text into text chunks
"""

from typing import List
from analitiq.base.base_chunker import BaseChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from analitiq.base.base_chunker import CHUNK_SIZE, CHUNK_OVERLAP
from analitiq.loaders.documents.schemas import  Chunk, DocumentSchema
from analitiq.utils.keyword_extractions import extract_keywords


class TextChunker(BaseChunker):
    def __init__(self, max_chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: DocumentSchema) -> List[Chunk]:
        if document.document_content == '':
            return None

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(self.max_chunk_size),
            chunk_overlap=int(self.chunk_overlap),
            length_function=len,
        )

        #langchain_document = Document(page_content=document.document_content)
        chunks = splitter.split_text(document.document_content)
        return_chunks = []
        for chunk in chunks:
            chunk_obj = Chunk(
                content=chunk,
                document_num_char=len(document.document_content),
                document_name=document.metadata.document_name,
                document_uuid = document.uuid,
                chunk_num_char=len(chunk),
                content_kw = extract_keywords(chunk)
                )
            return_chunks.append(chunk_obj)


        return return_chunks
