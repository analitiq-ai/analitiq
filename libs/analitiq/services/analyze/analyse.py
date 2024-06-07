from analitiq.logger import logger
from analitiq.base.BaseResponse import BaseResponse
from analitiq.base.GlobalConfig import GlobalConfig
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from analitiq.services.analyze.prompt import (
    ANALYZE_DATA_PROMPT
)


class AnalysisResponse(BaseModel):
    Summary: str = Field(description="Summary of your findings and observations")
    Observations: str = Field(description="Interesting observations about the data")
    Anomalies: str = Field(description="Anomalies you may have discovered in the data")


class Analyze():
    """Class to determine what kind of char should be generated,"""
    def __init__(self) -> None:
        """Initialize the service.
        """
        self.llm = GlobalConfig().get_llm()
        self.response = BaseResponse(self.__class__.__name__)

    def run(self, service_input: list, user_prompt=None,  **kwargs):
        """Initialize the Analyzer.
        Args:
          user_prompt: User prompt optional but can enhance results.
          service_input: List of BaseResponse objects from previous nodes
        """

        if service_input is None or service_input is []:
            return self.response

        # we combine the responses from all higher level nodes
        combined_responses = ''
        for item in service_input:
            combined_responses = combined_responses + f"{item.content_format}:\n{item.content}"

        parser = PydanticOutputParser(pydantic_object=AnalysisResponse)

        prompt = PromptTemplate(
            template=ANALYZE_DATA_PROMPT,
            input_variables=["user_prompt"],
            partial_variables={"data_to_analyze": combined_responses, "format_instructions": parser.get_format_instructions()},
        )

        table_chain = prompt | self.llm | parser
        llm_response = table_chain.invoke({"user_prompt": user_prompt})
        logger.info(f"Response {llm_response}")

        # Package the result and metadata into a Response object
        self.response.set_content(f"Summary: {llm_response.Summary}\nObservations: {llm_response.Observations}\nAnomalies: {llm_response.Anomalies}\n ")

        return self.response
