from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
from analitiq.logger.logger import logger
from analitiq.factories.relational_database_factory import RelationalDatabaseFactory
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from analitiq.factories.llm_factory import LlmFactory


class BaseAgent(ABC):
    """Abstract base class for agents."""

    def __init__(self, key: str):
        self.key = key
        self.db = None
        self.llm = None
        self.vdb = None

    def invoke(self, params: Dict[str, Any]):
        """Initialize dependencies based on provided parameters."""
        db_params = params.get("db_params")
        llm_params = params.get("llm_params")
        vdb_params = params.get("vdb_params")

        if db_params and not self.db:
            self.db = RelationalDatabaseFactory.connect(db_params)
            logger.debug(f"Database initialized for agent {self.key}")
        if llm_params and not self.llm:
            self.llm = LlmFactory.connect(llm_params)
            logger.debug(f"LLM initialized for agent {self.key}")
        if vdb_params and not self.vdb:
            self.vdb = VectorDatabaseFactory.connect(vdb_params)
            logger.debug(f"Vector Database initialized for agent {self.key}")

        # Validate required dependencies
        if not self.llm:
            raise ValueError(f"Agent {self.key} requires access to LLM to function.")

        if not self.vdb:
            logger.warning(f"Vector Database (vdb) is not provided for agent {self.key}. "
                           "Performance may be affected.")

    @abstractmethod
    def run(self, context):
        """Run the agent synchronously."""
        pass

    @abstractmethod
    async def arun(self, context):
        """Run the agent asynchronously."""
        pass