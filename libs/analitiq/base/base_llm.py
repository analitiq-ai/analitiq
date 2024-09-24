from abc import ABC, abstractmethod
from analitiq.logger.logger import logger
from typing import Dict, Optional, Any
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from analitiq.llms.utils import get_prompt_extra_info
from analitiq.llms import schemas

from analitiq.llms.prompts import (
    PROMPT_CLARIFICATION,
    SERVICE_SELECTION,
    SUMMARISE_REQUEST,
    EXTRACT_INFO_FROM_DB_DOCS,
    EXTRACT_INFO_FROM_DB_DDL,
    SUMMARISE_DDL,
    SUMMARIZE_DOCUMENT_CHUNKS,
)


class BaseLlm(ABC):
    """Abstract base class for large language models."""

    def __init__(self, params: Dict):
        self.params = params
        self.llm = self.create_llm()

    @abstractmethod
    def create_llm(self):
        """Create and return a SQLAlchemy engine."""
        pass

    def llm_invoke(self, user_prompt: str, prompt: Any, parser: Any):
        """Invokes a call to LLM with user_prompt, constructed_prompt and parser.

        :param user_prompt: A string representing the user's prompt to be passed to the table chain.
        :param prompt: An object representing the prompt to be passed to the table chain.
        :param parser: An object representing the parser to be passed to the table chain.
        :return: The response returned from the table chain after invoking with the provided parameters.
        """
        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt})

        return response

    def extract_info_from_db_docs(
        self, user_query, schemas_list, docs: Optional[str] = None
    ):
        if docs is None:
            docs = ""

        prompt = PromptTemplate(
            template=EXTRACT_INFO_FROM_DB_DOCS,
            input_variables=["user_query"],
            partial_variables={"schemas_list": schemas_list, "docs": docs},
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_query": user_query})

        return response

    def extract_info_from_db_ddl(
        self, user_query: str, ddl: str, docs: Optional[str] = None
    ):
        if docs is not None:
            docs = f"\nHere is some documentation about tables that you might find useful:\n{docs}"

        prompt = PromptTemplate(
            template=EXTRACT_INFO_FROM_DB_DDL,
            input_variables=["user_query"],
            partial_variables={"db_ddl": ddl, "db_docs": docs},
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_query": user_query})

        return response

    def summ_info_from_db_ddl(self, user_query: str, responses: str):
        prompt = PromptTemplate(
            template=SUMMARISE_DDL,
            input_variables=["user_query"],
            partial_variables={"responses": responses},
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_query": user_query})

        return response

    def llm_summ_user_prompts(self, user_prompt: str, user_prompt_hist: str):
        """This method asks LLM to summarise multiple disjoined user prompts. For example, if user asks "Give me top 10 customers"
        and the model asks to clarify "based on what criteria?", the user can follow up with "based on sales volume".
        This method will take "Give me top 10 customers" and "based on sales volume" and try to make sense of joined requests.

        :param user_prompt: Current user prompt
        :param user_prompt_hist: History of user prompts, including current prompt
        :return: str
        """
        prompt = PromptTemplate(
            template=SUMMARISE_REQUEST, input_variables=["user_prompt_hist"]
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke(
            {"user_prompt_hist": user_prompt_hist + "\n" + user_prompt}
        )

        return response

    def llm_is_prompt_clear(self, user_prompt: str, available_services: str):
        """This method asks LLM to check if the prompt is clear and it understands what needs to be done without any further user input.

        :param user_prompt: User prompt
        :param available_services: services available to the LLM
        :return: str
        """
        parser = PydanticOutputParser(pydantic_object=PromptClarification)
        prompt = PromptTemplate(
            template=PROMPT_CLARIFICATION, input_variables=["user_prompt"]
        )
        table_chain = prompt | self.llm | parser
        response = table_chain.invoke(
            {
                "user_prompt": user_prompt,
                "available_services": available_services,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        return response

    def llm_summ_docs(self, user_prompt: str, formatted_documents_string: str):
        prompt = PromptTemplate(
            template=SUMMARIZE_DOCUMENT_CHUNKS,
            input_variables=["user_query"],
            partial_variables={"documents": formatted_documents_string},
        )

        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_query": user_prompt})

        return response

    def llm_select_services(self, prompts, available_services):
        """Decide which tool(s) to use based on the user prompt.
            This is a placeholder function. Integration with an LLM for decision-making goes here.

        Accessing results:
                print(response.service_names)
                print(response.reason)
        """
        # Example: Return a tool based on a keyword in the prompt.
        # In a real scenario, this function would interact with an LLM to make an informed decision.

        parser = PydanticOutputParser(pydantic_object=SelectedServices)

        user_prompt, extra_info = get_prompt_extra_info(prompts)

        prompt = PromptTemplate(
            template=SERVICE_SELECTION,
            input_variables=["user_prompt"],
            partial_variables={
                "available_services": available_services,
                "extra_info": extra_info,
                "format_instructions": parser.get_format_instructions(),
            },
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": prompts["refined"]})

        return response.ServiceList
