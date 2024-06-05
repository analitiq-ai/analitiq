
from analitiq.main import Analitiq

user_prompt = "Give me our top 10 customers by revenue."

a = Analitiq()
services_responses = a.run(user_prompt)
print(services_responses)
for service, response in services_responses.items():
    if response:
        response.print_details()
