from typing import Literal

from analitiq.logger import logger
from analitiq.base.BaseResponse import BaseResponse


class SearchVdb:
    """
    This class represents a service to search internal documentation for information.
    """

    def __init__(self, llm, vdb, search_mode: Literal["kw","hybrid"] = "kw") -> None:
        self.llm = llm
        self.client = vdb
        self.user_prompt: str = None
        self.response = BaseResponse(self.__class__.__name__)
        self.search_mode = search_mode

    def run(self, user_prompt):
        self.user_prompt = user_prompt
        if self.search_mode == "kw":
            response = self.client.kw_search(user_prompt)
        elif self.search_mode == "hybrid":
            response = self.client.hybrid_search(user_prompt)

        try:
            docs = response.objects
        except Exception as e:
            logger.error(f"[Bode: Vector Search] Error: No objects returned")
            self.response.set_content('Search failed')
            return self.response

        # Initialize an empty string to hold the formatted content
        document_name_list = []
        formatted_documents_string = ""
        for o in docs:
            # Extract the document name and content from each object
            document_name_list.append(o.properties['document_name'])
            # Append the document name and content to the formatted string with the desired formatting
            formatted_documents_string += f"Document name: {o.properties['document_name']}\nDocument content:\n{o.properties['content']}\n\n"

        ai_response = self.llm.llm_summ_docs(user_prompt, formatted_documents_string)

        self.response.set_content(ai_response)
        self.response.set_metadata({"documents": ', '.join(document_name_list)})

        return self.response
