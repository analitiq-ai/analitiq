"""
Filename: analitiq/loaders/documents/directory_loader.py
"""

from pathlib import Path
from typing import List, Optional, Dict
from analitiq.loaders.documents.schemas import DocumentSchema
from langchain_core.document_loaders import BaseLoader
from langchain_community.document_loaders import TextLoader
from analitiq.factories.loader_factory import DocumentLoaderFactory
from analitiq.loaders.documents.schemas import ALLOWED_EXTENSIONS
from analitiq.loaders.documents.utils.common_loader_funcs import convert_to_document_schema, split_filename, get_document_type
from analitiq.logger.logger import initialize_logging
logger, chat_logger = initialize_logging()

class DirectoryLoader:
    def __init__(self, directory_path: str, extension: Optional[str] = None,
                 glob_loader=TextLoader, special_loaders: Optional[Dict[str, BaseLoader]] = None):
        logger.info("Directory loader initialized")
        self.directory_path = Path(directory_path)
        if not self.directory_path.exists() or not self.directory_path.is_dir():
            raise FileNotFoundError(f"The directory {self.directory_path} does not exist.")

        # Manage extensions and validate
        self.extension = extension.lstrip('.') if extension else None
        if self.extension and self.extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension {self.extension} not allowed. Allowed extensions are {ALLOWED_EXTENSIONS}.")

        # Pattern based on extension
        if self.extension:
            self.glob_pattern = f"**/*.{self.extension}"
        else:
            self.glob_pattern = f"**/*.*"

        self.glob_loader = glob_loader
        self.special_loaders = special_loaders or {}
        self.excluded_pattern = list(self.special_loaders.keys()) if special_loaders else []

    def load(self) -> List[DocumentSchema]:
        returned_documents = []
        loader_factory = DocumentLoaderFactory()
        for file_path in self.directory_path.glob(self.glob_pattern):
            # Only process files with allowed extensions if extension is not explicitly provided
            current_file_extension = file_path.suffix.lstrip('.')
            if not self.extension and current_file_extension not in ALLOWED_EXTENSIONS:
                continue

            # Select appropriate loader
            loader = loader_factory.get_loader(file_path)

            logger.info(f"File suffix is '{current_file_extension}'. Using loader: {loader}")
            docs = loader.load()
            doc = docs[0]

            # for loading non
            # if file is empty, pass
            if len(doc.page_content) == 0:
                continue

            file_name = file_path.name
            file_name, file_extension = split_filename(file_name)

            doc.metadata['document_name'] = file_name
            doc.metadata['document_type'] = get_document_type(file_extension)

            # convert Documents to Analitiq DocumentsSchema
            document_schemas = convert_to_document_schema([doc])

            returned_documents.extend(document_schemas)
        return returned_documents
