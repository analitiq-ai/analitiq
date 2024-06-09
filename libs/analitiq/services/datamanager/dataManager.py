import logging
from analitiq.base.BaseResponse import BaseResponse

# A dummy service created by copying a existing service, you can remove this later
# TODO you can remove this service, or implement it as for now it is just a replica of other services
class ManageData:
    """
    This class represents a service to search internal documentation for information.
    """

    def __init__(self, llm, vdb) -> None:
        self.llm = llm
        self.client = vdb
        self.user_prompt: str = None
        self.response = BaseResponse(self.__class__.__name__)

    def run(self, user_prompt):
        self.user_prompt = user_prompt

        response = self.client.kw_search(user_prompt)

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

        ai_response = self.llm.llm_summ_docs(user_prompt, formatted_documents_string)

        self.response.set_content(ai_response)
        self.response.set_metadata({"documents": ', '.join(document_name_list)})

        return self.response
