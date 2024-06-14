import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from typing import List
import dspy
from sklearn.model_selection import train_test_split
#from groq import Groq
from dspy.teleprompt import *

# Loading the created dataset
df = pd.read_csv('third_prompt_answers.csv')

# Calculating the previous accuracy
df['Correct_Service'] = [1 if x==y else 0 for x,y in zip(df['Expected Response'],df['actual_response'])]
print('Accuracy: ',format(100*df['Correct_Service'].sum()/len(df), '0.2f')+'%')

# Recreating the Pydantic output parser
class SelectedService(BaseModel):
    Action: str = Field(description="Name of the service.", default='none')
    ActionInput: str = Field(description="Action input required for successful completion of this action, output 'none' as default", default='none')
    Instructions: str = Field(description="Instructions of what needs to be done by this action.", default='none')
    DependsOn: List[str] = Field(description="List of names of actions this action depends on.", default='none')
    Further_Explanation: str = Field(description="Includes the explanation and extra details. Add all extra details here Remove'\_' with _", default='none')

# DSPy signature for the service_selection
class GenerateService(dspy.Signature):
    available_services = dspy.InputField(description='All available services for the agent')
    query = dspy.InputField(description='User specified query')
    selected_service : SelectedService = dspy.OutputField(description='The details of the service selected, only the service selected')

# Basic test train split
train_df, test_df = train_test_split(df, test_size=0.3)

# Defining the LLM
lm = dspy.Mistral(model='open-mistral-7b', api_key="ox7o6sc561oCyCPLjfB3wndsWUD5yF4Q", max_tokens=1200)
dspy.settings.configure(lm=lm)

# Creating the Module for the service selection
class Service(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate_answer = dspy.ChainOfThought(GenerateService)

    def forward(self, query, available_services):
        pred = self.generate_answer(query=query, available_services = available_services)
        return dspy.Prediction(selected_service = pred.selected_service)

# Creating a metric for evaluation
def validate_service(example, pred, trace=None):
    s = ['SearchDocs', 'QueryDatabase', 'GeneralKnowledger', 'DataManager']
    excluded_service = [x for x in s if x!= example.selected_service]
    score = 0
    neg_score = 1
    try:
        w = pred.selected_service.split('Selected Service')[1]
        if example.selected_service in w:
            score += 1
        for e_s in excluded_service:
            if e_s in w:
                neg_score += 1
        return score/neg_score
    except:
        w = pred.selected_service
        if example.selected_service in w:
            score += 1
        for e_s in excluded_service:
            if e_s in w:
                neg_score += 1
        return score/neg_score

# Define the query and available services
q = 'What is the capital of Pakistan?'
available_services = """
name: QueryDatabase description: "Use this service to query data from the company database."
name: SearchDocs description: "The service to search the documentation for information."
name: DataManager description: "This service is to run pre-configured data pipelines like DAGs ETL"
name: GeneralKnowledge description: "This service answers general knowledge queries"
"""

# Adding the training and testing set into the DSPy example object
trainset = [dspy.Example(query=q,available_services=available_services ,selected_service=a).with_inputs("query", "available_services") for q,a in zip(train_df['Question'],train_df['Expected Response'])]
testset = [dspy.Example(query=q,available_services=available_services ,selected_service=a).with_inputs("query", "available_services") for q,a in zip(test_df['Question'],test_df['Expected Response'])]

# Set up the optimizer
config = dict(max_bootstrapped_demos=4, max_labeled_demos=1, num_candidate_programs=2, num_threads=4)
kwargs = dict(num_threads=32, display_progress=True, display_table=0)
optimizer_d = BootstrapFewShotWithRandomSearch(metric=validate_service, **config)
optimizer = COPRO(metric=validate_service, prompt_model=lm, init_temperature=0.2)

d = optimizer_d.compile(Service(),trainset=trainset, valset=testset)
c = optimizer.compile(Service(),trainset=trainset, eval_kwargs=kwargs)


# Create an instance of the Service module
service = Service()

# Use the module to predict the selected service for the query
prediction = service(query=q, available_services=available_services)

# Print the selected service
print(prediction.selected_service)
