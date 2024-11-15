"""
Filename: analitiq.loaders.documents.file_loader.file_loader.py
"""

from pathlib import Path
from typing import List
from analitiq.loaders.documents.schemas import DocumentSchema, ALLOWED_EXTENSIONS
from analitiq.loaders.documents.utils.common_loader_funcs import convert_to_document_schema, split_filename, get_document_type
from analitiq.logger.logger import initialize_logging
logger, chat_logger = initialize_logging()

class FileLoader:
    """
        A class used to load files with specific extensions and provide their content.

        Attributes
        ----------
        file_path : Path
            The path to the file to be loaded.
        loader : Any
            The specific loader instance to handle the file based on its extension.

        Methods
        -------
        _get_loader():
            Returns the appropriate loader instance based on the file extension.

        load() -> List[Document]:
            Loads the content of the file using the appropriate loader instance.
    """
    def __init__(self, file_path: str):
        logger.info("File loader initialized")
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        suffix = self.file_path.suffix
        self.extension = suffix[1:] if suffix.startswith('.') else suffix
        if not self.file_path.exists():
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")
        if self.extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension {self.extension} not allowed. Allowed extensions are {ALLOWED_EXTENSIONS}.")
        self.loader = self._get_loader()

    def _get_loader(self):
        if self.extension in ("yml", "yaml"):
            from analitiq.loaders.documents.utils.yaml_loader import YamlLoader
            return YamlLoader(self.file_path)
        else:
            from langchain_community.document_loaders import TextLoader
            return TextLoader(self.file_path)

    def load(self) -> List[DocumentSchema]:
        """
        This will load Langchain Document objects from the file.
        [Document(page_content='Test content')]
        It needs to be converted to more extensive DocumentSchema object.
        :return:
        """
        docs = self.loader.load()
        file_name, file_extension = split_filename(self.file_name)
        doc = docs[0]

        # if file is empty, pass
        if len(doc.page_content) == 0:
            return None

        doc.metadata['document_name'] = file_name
        doc.metadata['document_type'] = get_document_type(file_extension)

        # convert Documents to Analitiq DocumentsSchema
        returned_documents = convert_to_document_schema([doc])
        return returned_documents
