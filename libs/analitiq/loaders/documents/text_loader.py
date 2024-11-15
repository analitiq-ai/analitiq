"""
Filename: analitiq/loaders/documents/text_loader.py
"""

from typing import List
from langchain_core.document_loaders import BaseLoader
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata
from analitiq.loaders.documents.utils.common_loader_funcs import get_document_type
from analitiq.loaders.documents.schemas import DocumentSchema, ALLOWED_EXTENSIONS
from analitiq.logger.logger import initialize_logging
logger, chat_logger = initialize_logging()

class TextLoader(BaseLoader):
    def __init__(self, content: str, filename: str, extension: str):
        logger.info("Text loader initialized")
        self.content = content
        self.filename = filename
        self.extension = extension

        # if file is empty, pass
        if len(content) == 0:
            raise ValueError(f"Content cannot be empty. Please provide document text for loading.")

        if self.extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension {extension} not allowed. Allowed extensions are {ALLOWED_EXTENSIONS}.")


    def load(self) -> List[DocumentSchema]:

        metadata = DocumentMetadata(
            document_name=self.filename,
            document_type=get_document_type(self.extension)
        )

        return [DocumentSchema(document_content=self.content, metadata=metadata)]
