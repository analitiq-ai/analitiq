from typing import List, Optional, Any
from langchain_core.pydantic_v1 import BaseModel, Field


class PromptClarification(BaseModel):
    """This class is used to capture primary product details of each task."""

    Clear: bool = Field(
        description="True if query is clear. False if more input or clarification is needed. Make sure True or False is with initial caps."
    )
    Query: str = Field(description="Properly worded query.")
    Hints: str = Field(
        description="Extract here the hints from the user provided inside the double square brackets, if available."
    )
    Feedback: Optional[str] = Field(
        description="If user query is clear, rephrase the user query here, while keeping all the details. If query is not clear, put your questions here."
    )


class Task(BaseModel):
    """This class is used to capture primary product details of each task."""

    Name: str = Field(description="Short name for the task to be done")
    Using: str = Field(
        description="Name of a tool needed to complete this task. It can be only one tool per task."
    )
    Description: str = Field(description="Additional description of the task")


class Tasks(BaseModel):
    """This class is used to store the collection/list of tasks."""

    TaskList: list[Task] = Field("List of tasks to be done to complete user query.")


class SelectedService(BaseModel):
    Action: str = Field(description="Name of a service.")
    ActionInput: str = Field(
        description="Action input require for successful completion of this action."
    )
    Instructions: str = Field(
        description="Instructions of what needs to be done by this action."
    )
    DependsOn: List[str] = Field(
        description="List of names of actions this action depends on."
    )


class SelectedServices(BaseModel):
    ServiceList: List[SelectedService] = Field(
        description="A list of selected services from available services matched against required services to fulfill the users query"
    )


class ServiceDependencies(BaseModel):
    Name: str = Field(description="Name of the service")
    Dependencies: list[str] = Field(
        "List of tasks that this service depends on for completion "
    )


class Service(BaseModel):
    ServicesList: List[ServiceDependencies] = Field(
        description="A list of selected services"
    )
