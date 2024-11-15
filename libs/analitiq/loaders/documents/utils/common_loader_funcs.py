from typing import List, Optional
from langchain_core.documents.base import Document
from analitiq.loaders.documents.schemas import DocumentSchema, DocumentMetadata, DocumentTypeEnum

def convert_to_document_schema(documents: List[Document]) -> List[DocumentSchema]:
    document_schemas = []

    # Get the field names for DocumentMetadata
    metadata_fields = DocumentMetadata.__annotations__.keys()

    for doc in documents:
        # Filter metadata attributes that match DocumentMetadata fields
        metadata_kwargs = {k: v for k, v in doc.metadata.items() if k in metadata_fields}

        # Create DocumentMetadata instance (will raise ValidationError if required fields are missing)
        doc_metadata = DocumentMetadata(**metadata_kwargs)

        # Create DocumentSchema instance
        doc_schema = DocumentSchema(
            document_content=doc.page_content,
            metadata=doc_metadata
        )
        document_schemas.append(doc_schema)

    return document_schemas


def get_document_type(extension: str) -> Optional[str]:
    try:
        return DocumentTypeEnum[extension].value
    except KeyError:
        return None  # or raise an error, or handle as needed


def split_filename(filename: str) -> tuple[str, str]:
    """
    Split the given filename into name and extension.

    Args:
        filename (str): The filename with extension.

    Returns:
        tuple[str, str]: A tuple containing the name and the extension.

    Raises:
        ValueError: If the filename does not contain a valid extension.
    """
    try:
        # Use rsplit with maxsplit=1 to split into name and extension
        name, extension = filename.rsplit('.', 1)
        return name, extension
    except ValueError:
        raise ValueError("The filename does not contain a valid extension.")
