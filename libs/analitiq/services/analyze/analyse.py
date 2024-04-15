from analitiq.base.BaseService import BaseResponse
from analitiq.base.GlobalConfig import GlobalConfig
from langchain.prompts import PromptTemplate


from analitiq.services.analyze.prompt import (
    ANALYZE_DATA_PROMPT
)

class Analyze():
    """Class to determine what kind of char should be generated,"""
    def __init__(self) -> None:
        """Initialize the service.
        """
        self.llm = GlobalConfig().get_llm()

    def run(self, service_input, user_prompt=None,  **kwargs):
        """Initialize the Analyzer.
        Args:
          user_prompt: User prompt optional but can enhance results.
          service_input: Dataframe of the actual data. Required because we have to analyze something.
        """
        if service_input is None:
            return

        data_format = 'pandas data frame'

        prompt = PromptTemplate(
            template=ANALYZE_DATA_PROMPT,
            input_variables=["user_prompt"],
            partial_variables={"data_format": data_format, "data_to_analyze": str(service_input)},
        )

        table_chain = prompt | self.llm
        llm_response = table_chain.invoke({"user_prompt": user_prompt})

        # Package the result and metadata into a Response object
        response = BaseResponse(
            content=llm_response.content,
            metadata={
            }
        )

        return response