
from analitiq.analitiq import Analitiq
import pandas as pd
# Suppresses some warnings, remove while debugging
import warnings
warnings.filterwarnings('ignore')

questions = {
    "Information Retrieval": [
        {"question": "What is the definition of 'machine learning'?", "expected_response": "GeneralKnowledger"},
        {"question": "Who is the CEO of Amazon?", "expected_response": "GeneralKnowledger"},
        {"question": "What is the capital of Australia?", "expected_response": "GeneralKnowledger"},
        {"question": "What is the definition of 'artificial intelligence'?", "expected_response": "GeneralKnowledger"},
        {"question": "Who is the author of the book 'To Kill a Mockingbird'?", "expected_response": "GeneralKnowledger"},
        {"question": "What is the capital of France?", "expected_response": "SearchDocs"},
        {"question": "What is the definition of 'natural language processing'?", "expected_response": "GeneralKnowledger"},
        {"question": "Who is the founder of Google?", "expected_response": "GeneralKnowledger"},
        {"question": "What is the capital of Japan?", "expected_response": "GeneralKnowledger"},
        {"question": "How do we calculate revenue?", "expected_response": "SearchDocs"},
        {"question": "What other tables does table X depend on?", "expected_response": "GeneralKnowledger"},
        {"question": "Where do we apply currency conversion?", "expected_response": "SearchDocs"},
        {"question": "What tables have tax information?", "expected_response": "GeneralKnowledger"},
        {"question": "Where do we store UK customers infomration?", "expected_response": "SearchDocs"}
    ],
    "SQL Generation": [
        {"question": "Write a SQL query to retrieve the top 5 customers with the highest total sales.", "expected_response": "QueryDatabase"},
        {"question": "Create a SQL query to retrieve all orders for a specific customer.", "expected_response": "QueryDatabase"},
        {"question": "Write a SQL query to retrieve the average order value for a specific product category.", "expected_response": "QueryDatabase"},
        {"question": "Write a SQL query to retrieve the total sales for a specific product.", "expected_response": "QueryDatabase"},
        {"question": "Create a SQL query to retrieve the top 3 products with the highest sales.", "expected_response": "QueryDatabase"},
        {"question": "Write a SQL query to retrieve the top 5 customers with the highest total sales.", "expected_response": "QueryDatabase"},
        {"question": "Create a SQL query to retrieve all orders for a specific customer.", "expected_response": "QueryDatabase"},
        {"question": "Write a SQL query to retrieve the average order value for a specific product category.", "expected_response": "QueryDatabase"},
        {"question": "Write a SQL query to retrieve the total sales for a specific product.", "expected_response": "QueryDatabase"},
        {"question": "Create a SQL query to retrieve the top 3 products with the highest sales.", "expected_response": "QueryDatabase"},
        {"question": "Show me revenues by month for the past 12 months.", "expected_response": "QueryDatabase"},
        {"question": "Who are our top 10 customers?", "expected_response": "QueryDatabase"}
    ],
    "General Knowledge": [
        {"question": "What is the definition of artificial intelligence?", "expected_response": "GeneralKnowledger"},
        {"question": "Who is the author of the book '1984'?", "expected_response": "GeneralKnowledger"},
        {"question": "What is the capital of China?", "expected_response": "GeneralKnowledger"},
        {"question": "What is the definition of 'cloud computing'?", "expected_response": "GeneralKnowledger"},
        {"question": "Who is the CEO of Microsoft?", "expected_response": "GeneralKnowledger"}
    ],

    # "Edge Cases": [
    #     {"question": "Can you retrieve information on a fictional topic, such as 'What is the capital of Atlantis'?", "expected_response": "No Service Available"},
    #     {"question": "Can you generate a SQL query to retrieve information on a non-existent table or column?", "expected_response": "No Service Available"},
    #     {"question": "Can you retrieve information on a topic that does not exist in the knowledge store?", "expected_response": "No Service Available"}
    # ],
    "Error Handling": [
        {"question": "Can you retrieve information on a topic that does not exist in the knowledge store?", "expected_response": "topic not found"},
        {"question": "Can you generate a SQL query with an invalid syntax?", "expected_response": "invalid query"},
        {"question": "Can you retrieve information on a topic with a typo?", "expected_response": "topic not found"}
    ],
    "Data Management": [
        {"question": "Referesh table X", "expected_response": "DataManager"},
        {"question": "Refresh table X and all other tables that depend on it", "expected_response": "DataManager"},
        {"question": "Refresh table X and all tables it depend on", "expected_response": "DataManager"},
        {"question": "Re-run the daily ETL", "expected_response": "DataManager"},
        {"question": "Run the hourly DAG now", "expected_response": "DataManager"}
    ]
}

questions_list = []

# Iterate over the categories
for category, questions in questions.items():
    # Iterate over the questions in the category
    for question in questions:
        # Create a dictionary for the question
        question_dict = {
            "Category": category,
            "Question": question["question"],
            "Expected Response": question["expected_response"]
        }
        # Add the question to the list
        questions_list.append(question_dict)

# Create the DataFrame
quest_df = pd.DataFrame(questions_list)
response_list =[]
service_list =[]

# Loop through all of the questions for the anlatiq engine. 
i =0
for q in quest_df['Question']:
    i+=1
    try:
        user_prompt = q

        a = Analitiq(user_prompt)
        services_responses = a.run(user_prompt)
        # print(services_responses)
        if type(services_responses)=='list':
            print('here')
            services_responses = services_responses[0]
        print(services_responses.replace("'",""))
    # Storing only the service selected at the end
        d = {}
        d['service'] = services_responses.replace("'","")

    # for service, response in services_responses.items():
    #     if service:
    #         # d['response'] = response.print_details()
    #         d['service'] = service
            
    #     else:
# suggest no service meaning the query was ambigious and didn't select a service
            # d['service'] = 'no service'
        response_list.append(d)
        # break
# Exception incase the analitiq engine fails.
    except Exception as e:
        print('FAILED')
        print(e)
        d ={}

        d['service'] = 'fail service'+str(e) 
        response_list.append(d)
        # break

                # else:
                #    
    print(i/len(quest_df), 'As examples done')
print(response_list)
     
quest_df['actual_response'] = [x['service'] for x in response_list]

quest_df.to_csv('third_prompt_answers.csv', index=False)
