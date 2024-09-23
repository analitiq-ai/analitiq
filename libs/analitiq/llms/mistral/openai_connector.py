from langchain_mistralai.chat_models import ChatMistralAI
from analitiq.base.base_llm import BaseLlm
import logging


class MistralConnector(BaseLlm):
    """Wrapper for Large language models."""

    def create_llm(self):
        return ChatMistralAI(
            mistral_api_key=self.params["llm_api_key"],
            temperature=self.params["temperature"],
            model_name=self.params["llm_model_name"],
        )

        logging.info(f"LLM is set to {params['type']}")
