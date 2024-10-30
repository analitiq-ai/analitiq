from langchain_aws import BedrockLLM
import boto3
from analitiq.base.base_llm import BaseLlm
import logging


class BedrockConnector(BaseLlm):
    """Wrapper for Large language models."""

    def connect(self):
        client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=self.params["aws_access_key_id"],
            aws_secret_access_key=self.params["aws_secret_access_key"],
            region_name=self.params["region_name"],
        )
        return BedrockLLM(
            client=client,
            region_name=self.params["region_name"],
            provider=self.params["provider"],
            model_id=self.params["llm_model_name"],
            model_kwargs={
                "temperature": self.params["temperature"],
                "max_tokens_to_sample": 10000,
            },
            streaming=False,
        )

        logging.info(f"LLM is set to {params['type']}")
