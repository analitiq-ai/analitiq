"""
Filename: chunker_factory.py

"""
from pathlib import Path
from analitiq.base.base_loader import BaseLoader
from analitiq.loaders.documents.schemas import DocumentTypeEnum

class DocumentLoaderFactory:
    @staticmethod
    def get_loader(file_path: str) -> BaseLoader:
        file_path = Path(file_path)
        suffix = file_path.suffix
        file_extension = suffix[1:] if suffix.startswith('.') else suffix
        document_type = DocumentTypeEnum[file_extension].value

        if document_type == 'yaml':
            from analitiq.loaders.documents.utils.yaml_loader import YamlLoader
            return YamlLoader(file_path)
        else:
            from langchain_community.document_loaders import TextLoader
            return TextLoader(file_path)
