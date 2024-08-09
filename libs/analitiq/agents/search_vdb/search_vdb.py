from typing import Literal, AsyncGenerator, Union
from analitiq.logger.logger import logger as alogger
from analitiq.base.BaseResponse import BaseResponse
from analitiq.vectordb import weaviate
import time
DEFAULT_SEARCH_MODE = 'hybrid'

class SearchVdb:
    """
    SearchVdb

    This class represents a search agent that queries a Weaviate database based on a user prompt. It provides different search modes: keyword search, vector search, and hybrid search. It
    * also uses a Language Model (LLM) to summarize the documents retrieved from the search.

    Attributes:
        - llm: An instance of the Language Model used for document summarization.
        - vdb: An instance of the Weaviate database handler.
        - search_mode: The search mode to be used. Valid values are "kw" (keyword search), "vector" (vector search), or "hybrid" (hybrid search). Default value is "hybrid".
        - user_prompt: The user prompt for the search.
        - response: An instance of the BaseResponse class that holds the response content and metadata.

    Methods:
        - __init__(self, llm, vdb: weaviate.WeaviateHandler, search_mode: Literal["kw", "vector", "hybrid"] = DEFAULT_SEARCH_MODE) -> None:
            Initializes a new instance of SearchVdb.

            Parameters:
                - llm: An instance of the Language Model used for document summarization.
                - vdb: An instance of the Weaviate database handler.
                - search_mode: The search mode to be used. Default value is "hybrid".

        - run(self, user_prompt):
            Runs the search with the given user prompt.

            Parameters:
                - user_prompt: The user prompt for the search.

            Returns:
                - response: An instance of the BaseResponse class that holds the response content and metadata.

    """

    def __init__(self, llm, vdb: weaviate.WeaviateHandler, search_mode: Literal["kw", "vector", "hybrid"] = DEFAULT_SEARCH_MODE) -> None:
        self.llm = llm
        self.client = vdb
        self.user_prompt: str = None
        self.response = BaseResponse(self.__class__.__name__)
        self.search_mode = search_mode

    @staticmethod
    def format_docs_into_string(docs):
        # Initialize an empty string to hold the formatted content
        document_name_list = []
        formatted_documents_string = ""
        for o in docs:
            # Extract the document name and content from each object
            document_name_list.append(o.properties['document_name'])
            # Append the document name and content to the formatted string with the desired formatting
            formatted_documents_string += f"Document name: {o.properties['document_name']}\nDocument content:\n{o.properties['content']}\n\n"

        return document_name_list, formatted_documents_string


    def run(self, user_prompt):
        self.user_prompt = user_prompt
        alogger.info(f"[Search VDb Agent]. Query: {user_prompt}")

        if self.search_mode == "kw":
            response = self.client.kw_search(user_prompt)
        elif self.search_mode == "hybrid":
            response = self.client.hybrid_search(user_prompt)
        elif self.search_mode == "vector":
            response = self.client.vector_search(user_prompt)

        try:
            docs = response.objects
        except Exception as e:
            alogger.error(f"[Body: Vector Search] Error: No objects returned")
            self.response.set_content('Search failed')
            return self.response

        # Initialize an empty string to hold the formatted content
        document_name_list, formatted_documents_string=self.format_docs_into_string(docs)
        if self.llm is not None:
            ai_response = self.llm.llm_summ_docs(user_prompt, formatted_documents_string)
            self.response.set_content(ai_response)
            self.response.set_metadata({"documents": ', '.join(document_name_list)})
        else:
            logger.error("ERROR: No llm set")

        return self.response

    async def arun(self, user_prompt) -> AsyncGenerator[Union[str, BaseResponse], None]:
        self.user_prompt = user_prompt
        alogger.info(f"[Search VDb Agent]. Query: {user_prompt}")

        if self.search_mode == "kw":
            response = self.client.kw_search(user_prompt)
        elif self.search_mode == "hybrid":
            response = self.client.hybrid_search(user_prompt)
        elif self.search_mode == "vector":
            response = self.client.vector_search(user_prompt)

        try:
            docs = response.objects
        except Exception as e:
            alogger.error(f"[Body: Vector Search] Error: No objects returned")
            self.response.set_content('Search produced no results')
            yield self.response.to_json()

            return

        document_name_list, formatted_documents_string=self.format_docs_into_string(docs)
        if self.llm is not None:
            ai_response = self.llm.llm_summ_docs(user_prompt, formatted_documents_string)
            self.response.set_content(ai_response)
            self.response.set_metadata({"documents": ', '.join(document_name_list)})
        else:
            logger.error("ERROR: No llm set")

        yield self.response.to_json()

        return
