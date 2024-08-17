from typing import List, Union
from transformers import AutoTokenizer, AutoModel
import numpy as np


class AnalitiqVectorizer:
    """A class to handle vectorization of text using Hugging Face models.

    Attributes
    ----------
    model_name_or_path : str
        The name or path of the Hugging Face model.
    tokenizer : AutoTokenizer
        The tokenizer for the model.
    model : AutoModel
        The model for generating vectors.

    Methods
    -------
    __init__(model_name_or_path: str):
        Initializes the Vectorizer with the specified model.
    load_model():
        Loads the tokenizer and model.
    vectorize(text: Union[str, List[str]]) -> torch.Tensor:
        Generates vectors for the given input text.

    """

    def __init__(self, model_name_or_path: str):
        """Initialize the Vectorizer with the specified model.

        Parameters
        ----------
        model_name_or_path : str
            The name or path of the Hugging Face model to be used.

        """
        self.model_name_or_path = model_name_or_path
        self.tokenizer = None
        self.model = None
        self.load_model()

    def load_model(self):
        """Load the tokenizer and model from Hugging Face.

        If the model is not present locally, it will be downloaded.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
        self.model = AutoModel.from_pretrained(self.model_name_or_path)

    def vectorize(self, text: Union[str, List[str]], flatten: bool = True) -> np.ndarray:
        """Generate vectors for the given input text.

        Parameters
        ----------
        text : Union[str, List[str]]
            The input text or list of texts to be vectorized.
        flatten : bool
            To avoid potential issues with the FAISS index

        Returns
        -------
        torch.Tensor
            The vectors generated from the input text.

        """
        if self.tokenizer is None:
            errmsg = "ERROR: Tokenizer is not set."
            raise TypeError(errmsg)
        if self.model is None:
            errmsg = "ERROR: No Model is set."
            raise TypeError(errmsg)
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        outputs = self.model(**inputs)
        vectors = outputs.last_hidden_state.mean(dim=1)

        if flatten:
            return vectors.detach().cpu().numpy().flatten().tolist()
        else:
            return vectors.detach().cpu().numpy()

    def normalize(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize some vectors."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / norms

    def create_embeddings(self, texts: List[str]):
        """Create Embeddings after normalization."""
        self.texts = texts
        embeddings = self.vectorize(texts, False)
        self.embeddings = self.normalize(embeddings)

    def search(self, query: str, k: int = 3):
        """Search for embeddings."""
        if self.embeddings is None or self.texts is None:
            errmsg = "Embeddings have not been created. Call create_embeddings() first."
            raise ValueError(errmsg)

        query_vector = self.vectorize([query], False)
        query_vector = self.normalize(query_vector)

        similarities = np.dot(self.embeddings, query_vector.T).flatten()
        top_k_indices = similarities.argsort()[-k:][::-1]
        results = [(self.texts[idx], similarities[idx]) for idx in top_k_indices]
        return results
