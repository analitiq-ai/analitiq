from typing import List, Optional
from analitiq.base.GlobalConfig import GlobalConfig
from analitiq.base.BaseMemory import BaseMemory
from analitiq.base.BaseService import BaseResponse
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field, validator

from analitiq.llm.prompt import (
    PROMPT_CLARIFICATION,
    SERVICE_DEPENDENCY,
    SERVICE_SELECTION,
    TASK_LIST,
    REFINE_TASK_LIST,
    SUMMARISE_REQUEST
)


class PromptClarification(BaseModel):
    """
        This class is used to capture primary product details of each task
    """
    Clear: bool = Field(description="True if query is clear. False if more input or clarification is needed.")
    Feedback: Optional[str] = Field(description="Optional feedback if this task is not clear")


class Task(BaseModel):
    """
        This class is used to capture primary product details of each task
    """
    Name: str = Field(description="Short name for the task to be done")
    Using: str = Field(description="What kind of tool do you need to complete this task")
    Description: str = Field(description="Additional description of the task")


class Tasks(BaseModel):
    """
        This class is used to store the collection/list of tasks
    """
    TaskList: list[Task] = Field("List of tasks to be done to complete user query.")


class SelectedService(BaseModel):
    Name: str = Field(description="Names of service")
    TaskName: str = Field(description="Name of the task to be done by this service")
    Description: str = Field(description="Description of what needs to be done with this service taken from the list of required services that matched to this service.")


class SelectedServices(BaseModel):
    ServiceList: List[SelectedService] = Field(description="A list of selected services from available services matched against required services to fulfill the users query")


class ServiceDependencies(BaseModel):
    Name: str = Field(description="Name of the service")
    Dependencies: list[str] = Field("List of tasks that this service depends on for completion ")


class Service(BaseModel):
    ServicesList: List[ServiceDependencies] = Field(description="A list of selected services")


class AnalitiqLLM():

    def __init__(self, user_prompt):
        self.llm = GlobalConfig().get_llm()
        self.memory = BaseMemory()
        self.user_prompt = user_prompt

    def save_response(self, response: str):

        # Package the result and metadata into a Response object
        log_response = BaseResponse(
            content=str(response),
            metadata={
            }
        )

        self.memory.log_service_message(log_response, 'Core')
        self.memory.save_to_file()

    def llm_summ_user_prompts(self, user_prompt_hist: str):
        """
        This method asks LLM to summarise multiple disjoined user prompts. For example, if user asks "Give me top 10 customers"
        and the model asks to clarify "based on what criteria?", the user can follow up with "based on sales volume".
        This method will take "Give me top 10 customers" and "based on sales volume" and try to make sense of joined requests.

        :param user_prompt_hist: History of user prompts
        :return: str
        """
        prompt = PromptTemplate(
            template=SUMMARISE_REQUEST,
            input_variables=["user_prompt"],
            partial_variables={"user_prompt_hist": user_prompt_hist}
        )
        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_prompt": self.user_prompt})

        self.save_response(response.content)

        return response.content

    def llm_is_prompt_clear(self, user_prompt: str):
        """
        This method asks LLM to check if the prompt is clear and it understands what needs to be done without any further user input

        :param user_prompt: User prompt
        :return: str
        """

        parser = PydanticOutputParser(pydantic_object=PromptClarification)
        prompt = PromptTemplate(
            template=PROMPT_CLARIFICATION,
            input_variables=["user_prompt"]
        )
        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": user_prompt, "format_instructions": parser.get_format_instructions()})

        #self.save_response(response.content)

        return response

    def llm_select_services(self, user_prompt, required_services, available_services):
        """Decide which tool(s) to use based on the user prompt.
            This is a placeholder function. Integration with an LLM for decision-making goes here.

        Accessing results:
                print(response.service_names)
                print(response.reason)
        """
        # Example: Return a tool based on a keyword in the prompt.
        # In a real scenario, this function would interact with an LLM to make an informed decision.

        parser = PydanticOutputParser(pydantic_object=SelectedServices)
        prompt = PromptTemplate(
            template=SERVICE_SELECTION,
            input_variables=["user_prompt"],
            partial_variables={"required_services": required_services,
                               "available_services": available_services,
                               "format_instructions": parser.get_format_instructions()
                               },
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": self.user_prompt})

        self.save_response(response.ServiceList)
        return response.ServiceList

    def llm_create_task_list(self, user_prompt):

        parser = PydanticOutputParser(pydantic_object=Tasks)
        prompt = PromptTemplate(
            template=TASK_LIST,
            input_variables=["user_prompt"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": self.user_prompt})

        self.save_response(str(response.TaskList))
        return response.TaskList

    def llm_refine_task_list(self, user_prompt: str, tasks_list: str):

        parser = PydanticOutputParser(pydantic_object=Tasks)
        prompt = PromptTemplate(
            template=REFINE_TASK_LIST,
            input_variables=["user_prompt"],
            partial_variables={"format_instructions": parser.get_format_instructions(), "tasks": tasks_list}
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": self.user_prompt})

        self.save_response(response)

        return response

    def llm_build_service_dependency(self, user_prompt, available_services, selected_services):
        """Decide which tool(s) to use based on the user prompt in which order.
            This is a placeholder function. Integration with an LLM for decision-making goes here."""
        # Example: Return a tool based on a keyword in the prompt.
        # In a real scenario, this function would interact with an LLM to make an informed decision.

        # Convert each service's details into a formatted string


        parser = PydanticOutputParser(pydantic_object=Service)
        prompt = PromptTemplate(
            template=SERVICE_DEPENDENCY,
            input_variables=["user_prompt"],
            partial_variables={"available_services": available_services,
                               "selected_services": selected_services,
                               "format_instructions": parser.get_format_instructions()
                               },
        )

        table_chain = prompt | self.llm | parser
        response = table_chain.invoke({"user_prompt": self.user_prompt})

        self.save_response(response.ServicesList)
        return response.ServicesList