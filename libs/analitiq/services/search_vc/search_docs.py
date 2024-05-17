import logging
from analitiq.base.BaseResponse import BaseResponse
from analitiq.base.GlobalConfig import GlobalConfig
from langchain.prompts import PromptTemplate
from analitiq.services.search_vc.prompt import (
    SUMMARIZE_DOCUMENT_CHUNKS
)


class Search_docs:
    """
    This class represents a service to search internal documentation for information.
    """

    def __init__(self, user_prompt) -> None:
        self.llm = GlobalConfig().get_llm()
        self.client = None
        self.user_prompt = user_prompt
        self.response = BaseResponse(self.__class__.__name__)

    def run(self):
        project_name = GlobalConfig().get_project_config_param("profile")
        profile = GlobalConfig().profile_configs['vector_dbs']
        self.client = GlobalConfig().get_vdb_client(profile) # We do not need to init the VDB, until we need to use it

        response = self.client.kw_search(project_name, self.user_prompt)

        try:
            docs = response.objects
        except Exception as e:
            logging.error(f"[Bode: Vector Search] Error: No objects returned")
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

        prompt = PromptTemplate(
            template=SUMMARIZE_DOCUMENT_CHUNKS,
            input_variables=["user_prompt"],
            partial_variables={"query": self.user_prompt, "documents": formatted_documents_string},
        )

        table_chain = prompt | self.llm
        ai_response = table_chain.invoke({"user_prompt": self.user_prompt})
        self.response.set_content(ai_response)
        self.response.set_metadata({"documents": ', '.join(document_name_list)})

        return self.response
