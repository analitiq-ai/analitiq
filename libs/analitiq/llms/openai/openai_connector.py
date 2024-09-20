from langchain_openai import ChatOpenAI
from analitiq.base.base_llm import BaseLlm
import logging


class OpenaiConnector(BaseLlm):
    """Wrapper for Large language models."""

    def create_llm(self):
        return ChatOpenAI(
            openai_api_key=self.params["api_key"],
            temperature=self.params["temperature"],
            model_name=self.params["llm_model_name"],
        )

        logging.info(f"LLM is set to {self.params['type']}")
