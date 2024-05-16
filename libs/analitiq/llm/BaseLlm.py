from typing import List, Optional, Any
from analitiq.base.GlobalConfig import GlobalConfig
from analitiq.base.BaseMemory import BaseMemory
from analitiq.base.BaseResponse import BaseResponse
from analitiq.utils.code_extractor import CodeExtractor
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
import json

from langchain_core.pydantic_v1 import BaseModel, Field, validator
from enum import Enum

from analitiq.llm.prompt import (
    PROMPT_CLARIFICATION,
    SERVICE_SELECTION,
    TASK_LIST,
    REFINE_TASK_LIST,
    SUMMARISE_REQUEST,
    COMBINE_TASK_PAIR,
    FIX_JSON,
    EXTRACT_INFO_FROM_DB_SCHEMA
)


class PromptClarification(BaseModel):
    """
        This class is used to capture primary product details of each task
    """
    Clear: bool = Field(description="True if query is clear. False if more input or clarification is needed. Make sure True or False is with initial caps.")
    Query: str = Field(description="Properly worded query.")
    Hints: str = Field(description="Extract here the hints from the user provided inside the double square brackets, if available.")
    Feedback: Optional[str] = Field(description="If user query is clear, rephrase the user query here, while keeping all the details. If query is not clear, put your questions here.")


def fix_case(llm_output) -> str:
    """Parse the AI message."""
    return llm_output.replace(": true,", ": True,")

class CombineTaskPair(Enum):
    """
        This class is used to determine if tasks can be combined.
    """
    YES = 'Can combine tasks.'
    NO = 'Cannot combine tasks.'


class Task(BaseModel):
    """
        This class is used to capture primary product details of each task
    """
    Name: str = Field(description="Short name for the task to be done")
    Using: str = Field(description="Name of a tool needed to complete this task. It can be only one tool per task.")
    Description: str = Field(description="Additional description of the task")


class Tasks(BaseModel):
    """
        This class is used to store the collection/list of tasks
    """
    TaskList: list[Task] = Field("List of tasks to be done to complete user query.")


class SelectedService(BaseModel):
    Action: str = Field(description="Name of a service.")
    ActionInput: str = Field(description="Action input require for successful completion of this action.")
    Instructions: str = Field(description="Instructions of what needs to be done by this action.")
    DependsOn: List[str] = Field(description="List of names of actions this action depends on.")


class SelectedServices(BaseModel):
    ServiceList: List[SelectedService] = Field(description="A list of selected services from available services matched against required services to fulfill the users query")


class ServiceDependencies(BaseModel):
    Name: str = Field(description="Name of the service")
    Dependencies: list[str] = Field("List of tasks that this service depends on for completion ")


class Service(BaseModel):
    ServicesList: List[ServiceDependencies] = Field(description="A list of selected services")


def get_prompt_extra_info(prompts):
    extra_info = ""

    template = TASK_LIST

    if len(prompts['refined']) > 10:
        user_prompt = prompts['refined']
    else:
        user_prompt = prompts['original']

    if len(prompts['feedback']) > 10:
        extra_info = extra_info + f"Your previous thoughts about this query were '{prompts['feedback']}'.\n"

    if len(prompts['hints']) > 10:
        extra_info = extra_info + f"Your previous thoughts about this query were '{prompts['hints']}'.\n"

    return user_prompt, extra_info


class AnalitiqLLM:

    def __init__(self):
        self.llm = GlobalConfig().get_llm()
        self.memory = BaseMemory()
        self.response = BaseResponse(self.__class__.__name__)

    def llm_invoke(self, user_prompt: str, prompt: Any, parser: Any):
        """
        Invokes a call to LLM with user_prompt, constructed_prompt and parser

        :param user_prompt: A string representing the user's prompt to be passed to the table chain.
        :param prompt: An object representing the prompt to be passed to the table chain.
        :param parser: An object representing the parser to be passed to the table chain.
        :return: The response returned from the table chain after invoking with the provided parameters.
        """
        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt})

        return response

    def extract_info_from_db_schema(self, user_query, formatted_documents_string):
        prompt = PromptTemplate(
            template=EXTRACT_INFO_FROM_DB_SCHEMA,
            input_variables=["user_query"],
            partial_variables={"db_schema": formatted_documents_string}
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_query": user_query})

        return response

    def save_response(self, response: str):

        # Package the result and metadata into a Response object
        self.response.set_content(str(response))

        self.memory.log_service_message(self.response)
        self.memory.save_to_file()


    def llm_summ_user_prompts(self, user_prompt: str, user_prompt_hist: str):
        """
        This method asks LLM to summarise multiple disjoined user prompts. For example, if user asks "Give me top 10 customers"
        and the model asks to clarify "based on what criteria?", the user can follow up with "based on sales volume".
        This method will take "Give me top 10 customers" and "based on sales volume" and try to make sense of joined requests.

        :param user_prompt: Current user prompt
        :param user_prompt_hist: History of user prompts, including current prompt
        :return: str
        """
        prompt = PromptTemplate(
            template=SUMMARISE_REQUEST,
            input_variables=["user_prompt_hist"]
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_prompt_hist": user_prompt_hist +"\n"+ user_prompt})

        self.save_response(response)

        return response

    def llm_is_prompt_clear(self, user_prompt: str, available_services: str):
        """
        This method asks LLM to check if the prompt is clear and it understands what needs to be done without any further user input

        :param user_prompt: User prompt
        :param available_services: services available to the LLM
        :return: str
        """

        parser = PydanticOutputParser(pydantic_object=PromptClarification)
        prompt = PromptTemplate(
            template=PROMPT_CLARIFICATION,
            input_variables=["user_prompt"]
        )
        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt
                                            , "available_services": available_services
                                            , "format_instructions": parser.get_format_instructions()}
                                        )

        #self.save_response(response)

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
            partial_variables={"available_services": available_services,
                               "extra_info": extra_info,
                               "format_instructions": parser.get_format_instructions()
                               },
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": prompts['refined']})

        self.save_response(response.ServiceList)
        return response.ServiceList

    def llm_create_task_list(self, prompts: dict, avail_services_str):
        """
        :param prompts: The the dictionary of prompts.
        :param avail_services_str: A string representing the available services.

        :return: The generated task list as a response.

        """
        parser = PydanticOutputParser(pydantic_object=Tasks)

        template = TASK_LIST

        user_prompt, extra_info = self.get_prompt_extra_info(prompts)

        prompt = PromptTemplate(
            template=template,
            input_variables=["user_prompt"],
            partial_variables={
                "format_instructions": parser.get_format_instructions()
                , "available_services": avail_services_str
                , "extra_info": extra_info
            }
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt})

        self.save_response(str(response.TaskList))
        return response.TaskList

    def llm_refine_task_list(self, user_prompt: str, tasks_list: str):
        """
        :param user_prompt: the user prompt or question to refine the task list
        :param tasks_list: the original list of tasks
        :return: the refined task list based on user input

        This method refines the given task list based on user input. It uses the PydanticOutputParser class to parse the output in Pydantic format.
        It creates a PromptTemplate with the 'REFINE_TASK_LIST' template and sets 'user_prompt' as the input variable. It also sets 'format_instructions' and 'tasks' as partial variables in
        * the template using the PydanticOutputParser's 'get_format_instructions' method and the 'tasks_list' parameter respectively.

        Next, it creates a table_chain using the PromptTemplate, the 'llm' method, and the PydanticOutputParser. It then invokes the table_chain by passing the 'user_prompt' parameter as a dictionary
        *.

        The response returned by the table_chain is saved using the 'save_response' method.

        Finally, the method returns the response.
        """
        parser = PydanticOutputParser(pydantic_object=Tasks)
        prompt = PromptTemplate(
            template=REFINE_TASK_LIST,
            input_variables=["user_prompt"],
            partial_variables={"format_instructions": parser.get_format_instructions(), "tasks": tasks_list}
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt})

        self.save_response(response)

        return response

    def llm_fix_json(self, text, error):
        prompt = PromptTemplate(
            template=FIX_JSON,
            input_variables=["string"],
            partial_variables={
                "error": error
            }
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke({"string": text})

        return response
