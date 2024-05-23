
from analitiq.analitiq import Analitiq

user_prompt = "Count for me number of policies by month for the last 12 months"

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
print(services_responses)
for service, response in services_responses.items():
    if response:
        response.print_details()
