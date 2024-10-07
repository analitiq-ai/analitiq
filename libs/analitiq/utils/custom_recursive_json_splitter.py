"""Class will split a json structure in a given format.

Persist a specific metadata info from parent to child groups.
"""
import json
from typing import Dict, Any, List, Iterable
from langchain_text_splitters import RecursiveJsonSplitter
from langchain_community.docstore.document import Document

_DEFAULT_METADATA = {"models": ["name", "description"]}


class CustomRecursiveJsonSplitter(RecursiveJsonSplitter):
    """A Custom JSON Splitter."""

    def __init__(self, max_chunk_size: int = 2000, min_chunk_size: int | None = None):
        """Initialize from parent class."""
        super().__init__(max_chunk_size, min_chunk_size)

    def split_json(self, 
                   json_data: Dict[str, Any],
                   convert_lists: bool = False,
                   metadata: Dict[str, List[str]] = _DEFAULT_METADATA) -> List[Dict]:
        """Split JSON into a list of JSON chunks and adds metadata to each chunk.

        :param json_data: The JSON data to be split.
        :param convert_lists: Whether to convert lists to dictionaries before splitting.
        :param metadata: The metadata to be added to each chunk.
        :return: A list of JSON chunks with metadata.
        """
        if isinstance(json_data, str):
            my_json = json.loads(json_data)
        elif isinstance(json_data, dict):
            my_json = json_data

        models = my_json.get("models")
        if models:
            final_chunks = []
            for model in models:
                model_meta = {"version": my_json.get("version"),
                               "models": [{name: model.get(name) for name 
                                           in _DEFAULT_METADATA.get("models")}]}
                data_to_chunk = {"columns": model.get("columns")}
                chunks = super().split_json(data_to_chunk, convert_lists)
                for chunk in chunks:
                    chunk.update(model_meta)
                final_chunks.extend(chunks)
            return final_chunks
        errmsg = f"""JSON Error. The Json Structure is not following {metadata}"""
        raise KeyError(errmsg)

    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        """Split a list of documents."""
        split_docs: List[Document] = []
        for doc in documents:
            text = doc.page_content
            chunks = self.split_json(text)
            for chunk in chunks:
                split_doc = doc.copy()
                split_doc.page_content = json.dumps(chunk)
                split_docs.append(split_doc)
        return split_docs
