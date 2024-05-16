
from analitiq.analitiq import Analitiq

user_prompt = "Please give me revenues by month."

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
print(services_responses)
for service, response in services_responses.items():
    print(response)
    if isinstance(response, list):
        for item in response:
            item.print_details()

    else:
        response.print_details()

