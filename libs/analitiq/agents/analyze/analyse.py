from analitiq.logger.logger import logger
from analitiq.base.BaseResponse import BaseResponse
from analitiq.base.GlobalConfig import GlobalConfig
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from analitiq.agents.analyze.prompt import ANALYZE_DATA_PROMPT


class AnalysisResponse(BaseModel):
    """Class for the Analysis Response."""

    Summary: str = Field(description="Summary of your findings and observations")
    Observations: str = Field(description="Interesting observations about the data")
    Anomalies: str = Field(description="Anomalies you may have discovered in the data")


class Analyze:
    """Class to determine what kind of charyt should be generated."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.llm = GlobalConfig().get_llm()
        self.response = BaseResponse(self.__class__.__name__)

    def run(self, service_input: list, user_prompt=None, **kwargs):
        """
        :param service_input: A list of items representing the input for the service.
        :param user_prompt: An optional user prompt.
        :param kwargs: Additional keyword arguments.
        :return: The response object.

        This method runs the service with the given input and user prompt (if provided), and returns the response object.

        If the service_input is None or an empty list, the method will return the existing response object without further processing.

        The method combines the responses from all higher level nodes and stores them in the variable combined_responses.

        A PydanticOutputParser object is created with the AnalysisResponse pydantic_object.

        A PromptTemplate object is created with the ANALYZE_DATA_PROMPT template, "user_prompt" as an input variable, and additional partial variables including "data_to_analyze" and "format
        *_instructions" derived from the combined_responses and parser respectively.

        A table_chain is created using the prompt, llm (lower-level module), and parser objects.

        The table_chain is invoked with the user_prompt as a parameter and the response is stored in llm_response.

        The method logs the llm_response using the logger.

        The result and metadata of the llm_response are packaged into the response object by setting the content of the response.

        Finally, the response object is returned.

        Example usage:
        response = run([item1, item2, item3], "Please provide additional instructions", extra_param1="value1", extra_param2="value2")
        """
        if service_input is None or service_input == []:
            return self.response

        # we combine the responses from all higher level nodes
        combined_responses = ""
        for item in service_input:
            combined_responses = combined_responses + f"{item.content_format}:\n{item.content}"

        parser = PydanticOutputParser(pydantic_object=AnalysisResponse)

        prompt = PromptTemplate(
            template=ANALYZE_DATA_PROMPT,
            input_variables=["user_prompt"],
            partial_variables={
                "data_to_analyze": combined_responses,
                "format_instructions": parser.get_format_instructions(),
            },
        )

        table_chain = prompt | self.llm | parser
        llm_response = table_chain.invoke({"user_prompt": user_prompt})
        logger.info(f"Response {llm_response}")

        # Package the result and metadata into a Response object
        self.response.set_content(
            f"Summary: {llm_response.Summary}\nObservations: "
            f"{llm_response.Observations}\nAnomalies: {llm_response.Anomalies}\n"
        )

        return self.response
