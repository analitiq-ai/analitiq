"""This is an example of how to query Analitiq for information."""

from analitiq.main import Analitiq

user_prompt = "Bikes"

a = Analitiq()
agent_responses = a.run(user_prompt)
#print(agent_responses)
for response in agent_responses.values():
    if response:
        pass


