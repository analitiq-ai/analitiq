from typing import List, Union
from transformers import AutoTokenizer, AutoModel
import torch

class HuggingFaceVectorizer:
    """
    A class to handle vectorization of text using Hugging Face models.
    
    Attributes:
    -----------
    model_name_or_path : str
        The name or path of the Hugging Face model.
    tokenizer : AutoTokenizer
        The tokenizer for the model.
    model : AutoModel
        The model for generating vectors.
    
    Methods:
    --------
    __init__(model_name_or_path: str):
        Initializes the Vectorizer with the specified model.
    load_model():
        Loads the tokenizer and model.
    vectorize(text: Union[str, List[str]]) -> torch.Tensor:
        Generates vectors for the given input text.
    """
    
    def __init__(self, model_name_or_path: str):
        """
        Initializes the Vectorizer with the specified model.
        
        Parameters:
        -----------
        model_name_or_path : str
            The name or path of the Hugging Face model to be used.
        """
        self.model_name_or_path = model_name_or_path
        self.tokenizer = None
        self.model = None
        self.load_model()

    def load_model(self):
        """
        Loads the tokenizer and model from Hugging Face.
        If the model is not present locally, it will be downloaded.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path)
        self.model = AutoModel.from_pretrained(self.model_name_or_path)

    def vectorize(self, text: Union[str, List[str]]) -> torch.Tensor:
        """
        Generates vectors for the given input text.
        
        Parameters:
        -----------
        text : Union[str, List[str]]
            The input text or list of texts to be vectorized.
        
        Returns:
        --------
        torch.Tensor
            The vectors generated from the input text.
        """
        inputs = self.tokenizer(text, return_tensors='pt', padding=True, truncation=True)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)


if __name__ == "__main__":
    # Loading a sentence bert transformer for embedding
    # other model
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model_name = 'sentence-transformers/all-mpnet-base-v2'
    vectorizer = HuggingFaceVectorizer(model_name)

    # Example Sentences
    sentences = ["Die Sonne scheint heute", "Es ist ein schöner Tag"]

    # Vectorisation
    embeddings = vectorizer.vectorize(sentences)

    #test print of embeddings
    print(embeddings.shape)
    print(embeddings)