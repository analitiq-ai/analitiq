
from analitiq.analitiq import Analitiq

user_prompt = "Query the database for me and give me a chart of our top 10 customers."

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
print(services_responses)
for service, response in services_responses.items():
    print(response)
    response.print_details()

