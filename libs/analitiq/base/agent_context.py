from pydantic import BaseModel, ValidationError


class ResultFormat(BaseModel):
    sql: str = "sql"
    data: str = "data"
    text: str = "text"


class AgentContext:
    def __init__(self, user_query: str):
        self.user_query = user_query
        self.results = {}  # Store all results (SQL, data, text, etc.) under one key

    # Function to add result under a single key with result type validation
    def add_result(self, key: str, result, result_type: str = 'text'):
        # Validate that result_type is one of the allowed values in ResultFormat
        allowed_types = ResultFormat().model_dump()
        if result_type not in allowed_types.values():
            raise ValueError(f"Invalid result_type '{result_type}'. Allowed types are: {list(allowed_types.values())}")

        # Ensure the key exists in the results dictionary
        if key not in self.results:
            self.results[key] = {}

        # Add the result to the appropriate field based on the result_type using the mapping from ResultFormat
        if result_type == "text" and result_type in self.results[key]:
            self.results[key][result_type] += "\n" + result
        else:
            self.results[key][result_type] = result

        # Stream the added result to the requestor as soon as it's added
        return {key: {result_type: result}}  # This can be used to stream results incrementally

    # Function to retrieve the full result (SQL, data, text) by key
    def get_result(self, key: str):
        return self.results.get(key, {})

    # Individual getters for SQL, data, text, and visualization
    def get_result_sql(self, key: str):
        return self.results.get(key, {}).get('sql')

    def get_result_data(self, key: str):
        return self.results.get(key, {}).get('data')

    def get_result_data_json(self, key: str):
        return self.results.get(key, {}).get('data').to_json(orient="split")

    def get_result_text(self, key: str):
        return self.results.get(key, {}).get('text')

