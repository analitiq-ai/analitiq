
from analitiq.analitiq import Analitiq

user_prompt = "Please give me revenues by month for all lifetime of data."

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
print(services_responses)
for service, response in services_responses.items():
    if response:
        response.print_details()

