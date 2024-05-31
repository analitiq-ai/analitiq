
from analitiq.analitiq import Analitiq

user_prompt = "Where in SQL code do we apply transformations to the Ireland policies?"

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
print(services_responses)
for service, response in services_responses.items():
    if response:
        response.print_details()
