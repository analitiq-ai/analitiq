"""This is an example of how to query Analitiq for information."""

from analitiq.main import Analitiq

user_prompt = "Hello"

a = Analitiq()
services_responses = a.run(user_prompt)
#print(services_responses)
for response in services_responses.values():
    if response:
        response.print_details()


