
# Creating Custom Services for Analitiq

This guide provides instructions on how to create custom services for the Analitiq platform. Custom services allow for enhanced flexibility and functionality, enabling users to execute specific tasks like generating SQL queries or charts based on natural language prompts. Follow the steps below to develop and integrate a new service.

## Working examples

### Basic Service
Basic service would be located in the directory `services/my_dir/myservice.py`

```python
class MyService:
    """
    This class represents a service that does something
    """

    def run(self):
        """Executes the new service

        Args:
            user_prompt (str): The user's prompt

        Returns:
            Response (str): A string containing some response
        """
        return('Hello, I am new service')
```
### Service + LLM + DB access
Let's say you would like to add LLM to service or give service access to your database, which is defined across all services.
To do this, you can extend the GlobalConfig, which loads the LLM and DB objects.

```python
from analitiq.base.GlobalConfig import GlobalConfig
from langchain.prompts import PromptTemplate

class MyService:
    """
    This class represents a service that does something
    """
    def __init__(self) -> None:
        self.llm = GlobalConfig().get_llm()
        self.db = GlobalConfig().get_db()
        
    def run(self, user_prompt):
        """Executes the new service

        Args:
            user_prompt (str): The user's prompt

        Returns:
            Response: An object containing some response
        """
        prompt = PromptTemplate(
            template="You are a very funny joker.",
            input_variables=["user_prompt"]
        )

        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_prompt": "Tell me a joke"})
        
        return response
```

### Service + Response
If you would like your service to provide response that can be used by other services, you need to wrap it inside `BaseResponse` object.
Onside the object, `metadata={}` dictionary can be used to store and pass any information that you deem important for other services to use and know.

```python
from analitiq.base.GlobalConfig import GlobalConfig
from langchain.prompts import PromptTemplate
from analitiq.base.BaseService import BaseResponse

class MyService:
    """
    This class represents a service that does something
    """
    def __init__(self) -> None:
        self.llm = GlobalConfig().get_llm()
        self.db = GlobalConfig().get_db()
        
    def run(self, user_prompt) -> BaseResponse:
        """Executes the new service

        Args:
            user_prompt (str): The user's prompt

        Returns:
            Response: An object containing some response
        """
        prompt = PromptTemplate(
            template="You are a very funny joker.",
            input_variables=["user_prompt"]
        )

        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_prompt": "Tell me a joke"})

        # Package the result and metadata into a Response object
        return BaseResponse(
            content=response.content,
            metadata={
                "note": 'This is some metadata important to this response',
            }
        )
```

### Service + Chat History Access (Memory)
Saving response to a chat history file can be done using `memory.log_service_message({RESPONSE},{SERVICE_NAME})` from the `BaseMemory` class.
Any future services will now be able to reference this information and retrieve it from the memory.
```python
from analitiq.base.GlobalConfig import GlobalConfig
from analitiq.base.BaseMemory import BaseMemory
from langchain.prompts import PromptTemplate

class MyService:
    """
    This class represents a service that does something
    """
    def __init__(self) -> None:
        self.llm = GlobalConfig().get_llm()
        self.db = GlobalConfig().get_db()
        
    def run(self, user_prompt):
        """Executes the new service

        Args:
            user_prompt (str): The user's prompt

        Returns:
            Response: An object containing some response
        """
        prompt = PromptTemplate(
            template="You are a very funny joker.",
            input_variables=["user_prompt"]
        )

        table_chain = prompt | self.llm
        response = table_chain.invoke({"user_prompt": "Tell me a joke"})

        # Save the response to memory
        memory = BaseMemory()
        memory.log_service_message(response,'Chart')
        memory.save_to_file()
        
        return response
```

## Service Structure

Each custom service should adhere to the following structure:

- **Service Directory**: `/services/{service_name}` - This is where your service's code will reside.
- **Executable File**: `{service_name}.py` - Contains the primary logic for your service.
- **Class Name**: The class inside `{service_name}.py` should have the same name as the service for consistency and clarity.
- **Description Comments**: Immediately below the class definition, include comments describing what your service does. This description is utilized by the AI to understand the service's purpose.
- **Function Comments**: Detailed comments below the `run` (for batch processing) and `arun` (for streaming) functions should define the expected inputs and outputs, including types. This information helps the AI understand what inputs are required for the service and what outputs to expect.

## BaseResponse Class

To standardize responses from your services, use the `BaseResponse` class for encapsulating operation results. Import this class from `service.py`. Here's an outline:

```python
class BaseResponse:
    """Encapsulates the response of service operations.
    
    Attributes:
        content (Any): The main content of the response, often a DataFrame.
        metadata (Dict): Operation metadata, like relevant tables and executed SQL.
    """
    
    def __init__(self, content: Any, metadata: Dict):
        self.content = content
        self.metadata = metadata
```

Your service's main response should be returned in the `content` attribute, with supplementary information in the `metadata` attribute of the dictionary.

## BaseService Class

If your custom service needs access to a database or LLM, extend the `BaseService` from `service.py`. The `BaseService` class provides a shared context and initializes essential resources:

```python
from analitiq.utils import db_utils
from langchain_community.utilities import SQLDatabase
import os

class BaseService:
    """Initializes the service with shared context and parameters.
    
    Args:
        context (Context): Shared resources like the database engine.
    """
    
    def __init__(self, context: Context):
        db_engine = db_utils.create_db_engine('postgresql', 'psycopg2', os.getenv("POSTGRES_HOST"), os.getenv("POSTGRES_PORT"), os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"), os.getenv("POSTGRES_DB"), 'sample_data')
        self.db = SQLDatabase(db_engine)
        self.llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
```

## Example: Adding a New Service

To add a new service, for example, `DataAnalysis`, follow these steps:

1. **Create Service Directory**: `/services/data_analysis`.
2. **Add `base.py`**: Implement your service logic within this file.

```python
# /services/data_analysis/base.py
from analitiq.base.BaseService import BaseService, BaseResponse

class DataAnalysis(BaseService):
    """Performs data analysis based on user prompts and returns insights.
    
    This service analyzes data to provide insights, trends, and patterns.
    """
    
    def run(self, data, prompt: str) -> BaseResponse:
        """Analyzes data based on a prompt.
        
        Args:
            data: The data to analyze.
            prompt (str): A natural language prompt describing the analysis.
        
        Returns:
            BaseResponse: Contains analysis results and metadata.
        """
        # Your analysis logic here
        content = ...
        metadata = ...
        return BaseResponse(content, metadata)
```

3. **Implement Your Service**: Define your analysis logic within the `run` method.

Remember to import necessary utilities and classes as shown in the examples. Follow these guidelines to ensure your services are consistently structured and integrated seamlessly with the Analitiq platform.
