import logging

from analitiq.base.GlobalConfig import GlobalConfig
from langchain.prompts import PromptTemplate
from analitiq.services.search_vc.prompt import (
    SUMMARIZE_DOCUMENT_CHUNKS
)


class Search_docs:
    """
    This class represents a service to search internal documentation for information.
    """

    def __init__(self) -> None:
        self.llm = GlobalConfig().get_llm()
        self.vdb = GlobalConfig().get_vdb()

    def run(self, user_prompt):
        project_name = GlobalConfig().get_project_name()
        response = self.vdb.kw_search(project_name, user_prompt)

        if response.objects:

            # Initialize an empty string to hold the formatted content
            formatted_documents_string = ""
            for o in response.objects:
                # Extract the document name and content from each object
                document_name = o.properties['document_name']
                content = o.properties['content']
                # Append the document name and content to the formatted string with the desired formatting
                formatted_documents_string += f"Document name: {document_name}\nDocument content: {content}\n\n"

            prompt = PromptTemplate(
                template=SUMMARIZE_DOCUMENT_CHUNKS,
                input_variables=["user_prompt"],
                partial_variables={"query": user_prompt, "documents": formatted_documents_string},
            )

            table_chain = prompt | self.llm
            ai_response = table_chain.invoke({"user_prompt": user_prompt})

            return ai_response
        else:
            return
