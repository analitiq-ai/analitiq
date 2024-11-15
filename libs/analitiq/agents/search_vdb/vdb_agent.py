from typing import Literal, AsyncGenerator, Union
from analitiq.logger.logger import initialize_logging
from analitiq.agents.base_agent import BaseAgent
from analitiq.base.agent_context import AgentContext

DEFAULT_SEARCH_MODE = "hybrid"
logger, chat_logger = initialize_logging()

class VDBAgent(BaseAgent):
    """VDBAgent.

    This class represents a search agent that queries a Weaviate database based on a user prompt. It provides different search modes: keyword search, vector search, and hybrid search. It
    * also uses a Language Model (LLM) to summarize the documents retrieved from the search.

    Attributes
    ----------
        - llm: An instance of the Language Model used for document summarization.
        - vdb: An instance of the Weaviate database handler.
        - search_mode: The search mode to be used. Valid values are "kw" (keyword search), "vector" (vector search), or "hybrid" (hybrid search). Default value is "hybrid".
        - user_prompt: The user prompt for the search.
        - response: An instance of the BaseResponse class that holds the response content and metadata.

    Methods
    -------
        - __init__(self, llm, vdb: WeaviateConnector, search_mode: Literal["kw", "vector", "hybrid"] = DEFAULT_SEARCH_MODE) -> None:
            Initializes a new instance of SearchVdb.

    Parameters
    ----------
                - llm: An instance of the Language Model used for document summarization.
                - vdb: An instance of the Weaviate database handler.
                - search_mode: The search mode to be used. Default value is "hybrid".

        - run(self, user_prompt):
            Runs the search with the given user prompt.

    Parameters
    ----------
                - user_prompt: The user prompt for the search.

    Returns
    -------
                - response: An instance of the BaseResponse class that holds the response content and metadata.

    """

    def __init__(
        self,
        key: str,
        search_mode: Literal["kw", "vector", "hybrid"] = DEFAULT_SEARCH_MODE,
    ) -> None:
        super().__init__(key)
        logger.info(f"VDB Agent {self.key} started.")
        self.key = key  # Unique key for this agent instance
        self.user_query: str = None
        self.search_mode = search_mode

    @staticmethod
    def format_docs_into_string(docs):
        # Initialize an empty string to hold the formatted content
        document_name_list = []
        formatted_documents_string = ""
        for o in docs:
            # Extract the document name and content from each object
            document_name_list.append(o.properties["document_name"])
            # Append the document name and content to the formatted string with the desired formatting
            formatted_documents_string += f"Document name: {o.properties['document_name']}\nDocument content:\n{o.properties['content']}\n\n"

        return document_name_list, formatted_documents_string

    def run(self, context: AgentContext) -> AgentContext:
        logger.info(f"[Search VDb Agent]. Query: {context.user_query}. Search mode: {self.search_mode}")
        self.user_query = context.user_query

        if self.search_mode == "kw":
            response = self.vdb.kw_search(context.user_query)
        elif self.search_mode == "hybrid":
            response = self.vdb.hybrid_search(context.user_query)
        elif self.search_mode == "vector":
            response = self.vdb.vector_search(context.user_query)

        try:
            docs = response.objects
        except Exception:
            logger.error("[Body: Vector Search] Error: No objects returned")
            context.add_result(self.key, "Search failed")
            return context

        # Initialize an empty string to hold the formatted content
        document_name_list, formatted_documents_string = self.format_docs_into_string(docs)

        if self.llm is not None:
            ai_response = self.llm.llm_summ_docs(context.user_query, formatted_documents_string)
            context.add_result(self.key, ai_response)
            context.add_result(self.key, f"Documents: {', '.join(document_name_list)}")
        else:
            logger.error("ERROR: No llm set")

        return context

    async def arun(self, context) -> AsyncGenerator[Union[str, None], None]:

        logger.info(f"[Search VDb Agent]. Query: {context.user_query}. Search mode: {self.search_mode}")
        if self.search_mode == "kw":
            response = self.vdb.kw_search(context.user_query)
        elif self.search_mode == "hybrid":
            response = self.vdb.hybrid_search(context.user_query)
        elif self.search_mode == "vector":
            response = self.vdb.vector_search(context.user_query)

        try:
            docs = response.objects
        except Exception:
            logger.error("[Body: Vector Search] Error: No objects returned")
            yield context.add_result(self.key, "Search produced no results")

            return

        document_name_list, formatted_documents_string = self.format_docs_into_string(docs)

        if self.llm is not None:
            ai_response = self.llm.llm_summ_docs(context.user_query, formatted_documents_string)
            yield context.add_result(self.key, ai_response)
            yield context.add_result(self.key, f"Documents: {', '.join(document_name_list)}")
        else:
            logger.error("ERROR: No llm set")

        return
