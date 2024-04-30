
from analitiq.analitiq import Analitiq

user_prompt = "Show me a chart of our revenues by month for all time."

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
for service_name, response in services_responses.items():
    response.print_details()

