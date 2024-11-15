"""
Filename: analitiq/chunkers/json_chunker.py

Class will split a json structure in a given format.

Persist a specific metadata info from parent to child groups.
"""
import json
from typing import List, Iterable
from analitiq.base.base_chunker import BaseChunker
from analitiq.utils.keyword_extractions import extract_keywords
from analitiq.base.base_chunker import CHUNK_SIZE
from analitiq.loaders.documents.schemas import  Chunk, DocumentSchema
from langchain_text_splitters import RecursiveJsonSplitter
from langchain_community.docstore.document import Document
from analitiq.logger.logger import initialize_logging
logger, chat_logger = initialize_logging()


class JsonChunker(BaseChunker):
    def __init__(self, max_chunk_size: int = CHUNK_SIZE, min_chunk_size: int | None = None):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk(self, document: DocumentSchema) -> List[Chunk]:
        splitter = CustomRecursiveJsonSplitter(self.max_chunk_size, self.min_chunk_size)

        return splitter.split_documents([document])


class CustomRecursiveJsonSplitter(RecursiveJsonSplitter):
    """A Custom JSON Splitter class.
    Splits a JSON dictionary into chunks of a defined maximum length while preserving the hierarchy. Recursively traverse the JSON structure and partition it accordingly.
    """

    def __init__(self, max_chunk_size: int, min_chunk_size: int | None = None):
        """Initialize from parent class."""
        super().__init__(max_chunk_size, min_chunk_size)

    @staticmethod
    def check_json(document: DocumentSchema):
        # First we try to check if the document is even a json
        try:
            json_content = json.loads(document.document_content)
            return json_content
        except json.JSONDecodeError as e:
            logger.error(f"Document {document.document_name} is not a valid JSON")
            raise e  # Re-raise the caught exception
            return False

    def split_json(self, node, max_length):
        """

        :param node:
        :param max_length:
        :return:
        """
        chunks = []
        def _split_json(node, path):
            if isinstance(node, dict):
                current_chunk = {}
                for key, value in node.items():
                    temp_chunk = {**current_chunk, key: value}
                    chunk_with_hierarchy = rebuild_hierarchy(path, temp_chunk)
                    serialized_chunk = json.dumps(chunk_with_hierarchy)
                    if len(serialized_chunk) <= max_length:
                        current_chunk[key] = value
                    else:
                        if current_chunk:
                            chunk_to_add = rebuild_hierarchy(path, current_chunk)
                            chunks.append(chunk_to_add)
                            current_chunk = {key: value}
                        else:
                            if isinstance(value, (dict, list)):
                                _split_json(value, path + [key])
                            else:
                                chunk_to_add = rebuild_hierarchy(path + [key], value)
                                chunks.append(chunk_to_add)
                if current_chunk:
                    chunk_to_add = rebuild_hierarchy(path, current_chunk)
                    chunks.append(chunk_to_add)
            elif isinstance(node, list):
                current_chunk = []
                for idx, item in enumerate(node):
                    temp_chunk = current_chunk + [item]
                    chunk_with_hierarchy = rebuild_hierarchy(path, temp_chunk)
                    serialized_chunk = json.dumps(chunk_with_hierarchy)
                    if len(serialized_chunk) <= max_length:
                        current_chunk.append(item)
                    else:
                        if current_chunk:
                            chunk_to_add = rebuild_hierarchy(path, current_chunk)
                            chunks.append(chunk_to_add)
                            current_chunk = [item]
                        else:
                            if isinstance(item, (dict, list)):
                                _split_json(item, path + [idx])
                            else:
                                chunk_to_add = rebuild_hierarchy(path + [idx], item)
                                chunks.append(chunk_to_add)
                if current_chunk:
                    chunk_to_add = rebuild_hierarchy(path, current_chunk)
                    chunks.append(chunk_to_add)
            else:
                chunk_with_hierarchy = rebuild_hierarchy(path, node)
                serialized_chunk = json.dumps(chunk_with_hierarchy)
                if len(serialized_chunk) <= max_length:
                    chunks.append(chunk_with_hierarchy)
                else:
                    chunks.append(chunk_with_hierarchy)

        def rebuild_hierarchy(path, node):
            for key in reversed(path):
                node = {key: node}
            return node

        _split_json(node, [])
        return chunks

    def split_documents(self, documents: Iterable[DocumentSchema]) -> List[Document]:
        """Split a list of documents in defined chunks."""
        return_chunks: List[Chunk] = []
        for doc in documents:
            document_content_json = self.check_json(doc)
            if not document_content_json:
                continue
            logger.info(f"Splitting json into chunks of size {self.max_chunk_size}")
            chunks = self.split_json(document_content_json, self.max_chunk_size)
            for chunk in chunks:
                split_doc = doc.model_copy()
                chunk_as_text = json.dumps(chunk, ensure_ascii=False)

                chunk_obj = Chunk(
                    content=chunk_as_text,
                    document_name=doc.metadata.document_name,
                    document_num_char=len(json.dumps(document_content_json, ensure_ascii=False)),
                    document_uuid = doc.uuid,
                    chunk_num_char=len(chunk_as_text),
                    content_kw = extract_keywords(chunk_as_text)
                )
                return_chunks.append(chunk_obj)
        return return_chunks
