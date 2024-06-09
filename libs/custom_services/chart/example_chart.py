"""
This is an example of how to run this service as a standalone in order to test it or play with it.
"""

import os
import sys
# Get the home directory
home_directory = os.environ['HOME']
# Dynamically construct the path
dynamic_path = f'{home_directory}/Documents/Projects/analitiq/libs/'
sys.path.insert(0, dynamic_path)


from analitiq.base.BaseResponse import BaseResponse
from analitiq.base.llm.BaseLlm import BaseLlm
# we assume that this custom service is located in directory /custom_services/chart/chart.py
from custom_services.chart.chart import Chart
import pandas as pd

# llm_params = {'type': 'bedrock'
#     , 'name': 'aws_llm'
#     , 'api_key': None
#     , 'temperature': 0.0
#     , 'llm_model_name': 'anthropic.claude-v2'
#     , 'credentials_profile_name': 'bedrock'
#     , 'provider': 'anthropic'
#     , 'aws_access_key_id': 'xxxx'
#     , 'aws_secret_access_key': 'xxxxx'
#     , 'region_name': 'eu-central-1'}
llm_params = {'name':'dev_llm', 'type':'Mistral','api_key':'UZoQY2BpxuZVkKjYWqagHGLZvvr8uzju'
              ,}
llm = BaseLlm(llm_params)

inst = Chart(llm)

df = pd.DataFrame({
    'category': ['Electronics', 'Clothing', 'Home & Kitchen', 'Books', 'Toys'],
    'total_sales': [25000, 15000, 20000, 5000, 10000]
})

# here we format input in a way the chart service can read it
service_input = BaseResponse(__name__)
service_input.set_content(df, 'dataframe')
service_input.set_metadata({"sql": "SELECT * FROM public.my_electronics"})

resp = inst.run(user_prompt="what are our sales by category?", service_input=[service_input])

print(resp)