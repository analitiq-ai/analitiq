import collections.abc
from analitiq.base.agent_context import AgentContext


class AgentPipeline:
    def __init__(self, agents: list, params: dict):
        self.agents = agents
        self.params = params

    def run(self, context: AgentContext):
        for agent in self.agents:
            agent.invoke(self.params)  # Agents initialize dependencies
            context = agent.run(context)
        return context

    async def arun(self, context: AgentContext) -> collections.abc.AsyncGenerator:
        """Async method to run the pipeline with streaming capability and yield intermediate results."""
        for agent in self.agents:
            agent.invoke(self.params)  # Agents initialize dependencies
            async for result in agent.arun(context):
                # Yield each intermediate result directly to the caller
                yield result

                # Update the context if the yielded result is an updated context
                if isinstance(result, AgentContext):
                    context = result

        # Yield the final context after all agents have processed it
        # yield context
