import logging
from analitiq.base.BaseResponse import BaseResponse
# A dummy service created by replicating a previous service
# TODO you can remove this after testing or implement it exactly how it actually should work

class Get_Knowledge:
    """
    This class represents a service to search internal documentation for information.
    """

    def __init__(self, llm, vdb) -> None:
        self.llm = llm
        self.client = vdb
        self.user_prompt: str = None
        self.response = BaseResponse(self.__class__.__name__)

    def run(self, user_prompt):
        self.user_prompt = user_prompt

        self.response = "Fake response"
        return self.response
