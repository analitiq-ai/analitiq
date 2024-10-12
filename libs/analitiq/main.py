import pathlib
import sys
from typing import Dict, Optional, Any
from analitiq.base.agent_context import AgentContext
from analitiq.agents.agent_pipeline import AgentPipeline

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGPATH = ROOT / "logger"

HELP_RESPONSE = """
Analitiq [v{version}] is an AI assistant that can examine your SQL files and database structure and answer common questions about your data.

Database: {db}
Collection: {vdb_collection_name}

_help_ - get help menu.
_fail_ - mark responses from Analitiq that are not accurate.
_params_ - get parameters and connections used by Analitiq.

Services that are currently connected:
"""

# import langchain
# langchain.debug = True

sys.path.append("/analitiq")


class Analitiq:

    def __init__(self, agents: list, params: Optional[Dict[str, Any]] = None):
        self.pipeline = AgentPipeline(agents, params)

    def run(self, user_query: str):
        context = AgentContext(user_query=user_query)
        response = self.pipeline.run(context)
        return response

    async def arun(self, user_query: str):
        context = AgentContext(user_query=user_query)
        async for response in self.pipeline.arun(context):
            yield response
