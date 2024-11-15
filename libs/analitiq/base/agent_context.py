from pydantic import BaseModel, Field
from pandas import DataFrame
from typing import Optional, Dict, Union

# Define Pydantic Schema for AgentResultFormat
class AgentResultFormat(BaseModel):
    sql: Optional[str] = Field(None, description="SQL query string")
    data: Optional[Dict] = Field(None, description="Data in JSON format")
    text: Optional[str] = Field(None, description="Textual response")


# Define Pydantic RootModel for AgentsResults to enforce key-value structure
class AgentsResults(BaseModel):
    agents_results: Dict[str, AgentResultFormat]

# AgentContext class that uses AgentResultFormat to store results
class AgentContext:
    def __init__(self, user_query: str):
        self.user_query = user_query
        self.results = AgentsResults(agents_results={})  # Store all results (SQL, data, text, etc.) under one key

    # Function to add result under a single key with result type validation
    def add_result(self, key: str, result: Union[str, DataFrame], content_type: str = 'text'):
        # Ensure the key exists in the results dictionary
        if key not in self.results.agents_results:
            self.results.agents_results[key] = AgentResultFormat()

        # Add the result to the appropriate field based on the content_type using the mapping from AgentResultFormat
        if content_type == "text":
            # Since one agent can provide multiple text responses, we try to combine them here
            if self.results.agents_results[key].text:
                self.results.agents_results[key].text += "\n" + result
            else:
                self.results.agents_results[key].text = result
        elif content_type == 'data' and isinstance(result, DataFrame):
            self.results.agents_results[key].data = result.to_dict(orient='split')
        elif content_type == 'sql':
            self.results.agents_results[key].sql = result
        else:
            raise ValueError(f"Invalid content_type '{content_type}' or incompatible result type. Allowed types are: 'sql', 'data', 'text'")

        # Stream the added result to the requestor as soon as it's added
        return {key: {content_type: result}}  # This can be used to stream results incrementally

    # Function to retrieve the full result (SQL, data, text) by key
    def get_result(self, key: str) -> Optional[AgentResultFormat]:
        return self.results.agents_results.get(key)

    # Individual getters for SQL, data, text, and visualization
    def get_result_sql(self, key: str) -> Optional[str]:
        return self.results.agents_results.get(key, {}).sql

    def get_result_data(self, key: str) -> Optional[Dict]:
        return self.results.agents_results.get(key, {}).data

    def get_result_data_json(self, key: str) -> Optional[Dict]:
        data = self.results.agents_results.get(key, {}).data
        if data:
            return data
        return None

    def get_result_text(self, key: str) -> Optional[str]:
        return self.results.agents_results.get(key, {}).text

    def get_results(self) -> Dict[str, AgentResultFormat]:
        dump = self.results.model_dump()
        return dump.get('agents_results')
