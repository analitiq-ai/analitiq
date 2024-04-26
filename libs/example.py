
from analitiq.analitiq import Analitiq

user_prompt = "Who are our top 10 customers?."

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
print(services_responses)
for service_name, response in services_responses.items():
    print(service_name)
    print(response.content)

