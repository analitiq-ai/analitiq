"""
This is an example of how to query Analitiq for information.
"""

from analitiq.main import Analitiq

user_prompt = "Hello"

a = Analitiq()
agent_responses = a.run(user_prompt)
#print(agent_responses)
for service, response in agent_responses.items():
    if response:
        response.print_details()

