"""
This is an example of how to query Analitiq for information.
"""

from analitiq.main import Analitiq

user_prompt = "Search documentation for number of bikes."

a = Analitiq()
services_responses = a.run(user_prompt)
#print(services_responses)
for service, response in services_responses.items():
    if response:
        response.print_details()


