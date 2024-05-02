import os
from analitiq.base.GlobalConfig import GlobalConfig
from analitiq.base.BaseMemory import BaseMemory
from analitiq.base.BaseResponse import BaseResponse
from langchain_core.pydantic_v1 import BaseModel, Field
from analitiq.base.BaseSession import BaseSession
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain.prompts import PromptTemplate

from analitiq.services.save.prompt import (
    SAVE_ELEMENT_PROMPT
)


class ElementToSave(BaseModel):
    """Define the desired data structure for llm response"""
    timestamp: str = Field(description="Timestamp of the element that best matches what the user wants to save")
    content: str = Field(description="The content that the user would like to save")
    descr: str = Field(description="Short description of the content that you will be saving for the user")
    filename: str = Field(description="Filename that you think would suit best to the content")


class Save:
    """
    A class to process chat history and extract information based on user prompts.

    Disable:True
    Attributes:
        base_memory (BaseMemory): An instance of BaseMemory to interact with chat history.
        llm_service (Any): Placeholder attribute for the Large Language Model service integration.
        output_directory (str): Directory where extracted objects are saved.
    """

    def __init__(self, output_directory: str = './extracted'):
        """
        Initializes the ChatHistoryProcessor with a session UUID and output directory.

        Parameters:
            output_directory (str): Directory where extracted objects are saved.
        """
        self.db = GlobalConfig().get_database()
        self.llm = GlobalConfig().get_llm()
        self.base_memory = BaseMemory()
        self.output_directory = output_directory
        self.response = BaseResponse(self.__class__.__name__)

    def extract_chat_entity(self, user_prompt, num_messages: int = 5) -> None:
        """
        Processes the user's prompt, retrieves recent chat messages, and extracts the requested information.

        Parameters:
            user_prompt (str): The prompt provided by the user, indicating what information to extract.
            num_messages (int): The number of recent messages to retrieve from chat history for analysis.
        """

        # Load the recent messages from chat history
        chat_history = self.base_memory.get_last_messages(num_messages)

        # Set up a parser + inject instructions into the prompt template.
        parser = JsonOutputParser(pydantic_object=ElementToSave)

        prompt = PromptTemplate(
            template=SAVE_ELEMENT_PROMPT,
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()
                ,"chat_history": chat_history
                               },
        )

        chain = prompt | self.llm

        response = chain.invoke({"user_prompt": user_prompt})

        try:
            parsed_response = parser.parse(response.content)
        except:
            new_parser = OutputFixingParser.from_llm(parser=parser, llm=self.llm)
            try:
                parsed_response = new_parser.parse(response.content)
            except:
                print(f"Could not parse LLM response: {response.content}")

        return parsed_response

    def save_object(self, filename: str, message: str) -> None:
        """
        Extracts the requested object from the key message and saves it to a file.

        Parameters:
            filename (str): The name of the file under which the information is saved.
            message (str): The message identified by the LLM as containing the requested information.
        """
        # Get the session ID
        session = BaseSession()

        # Ensure output directory exists
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        # Save the extracted object to a file
        filename = os.path.join(self.output_directory, f"{filename}_{session.session_uuid}.txt")
        with open(filename, 'w') as file:
            file.write(message)

        return filename

    def run(self, user_prompt: str, service_input, **kwargs):
        """Executes the search of data in chat history and it's saving .

        This method determines the appropriate element from chat_history based on the user's prompt,
        extracts that element from chat history and saves it in the directory.

        Args:
            user_prompt (str): The user's description of the desired chart.
            service_input: The input data for chart generation, either as a DataFrame or a pickled string.

        Returns:
            Response: BaseResponse object containing filename and description of the data that was saved.
        """

        llm_response = self.extract_chat_entity(user_prompt)

        filename = self.save_object(llm_response['filename'], llm_response['content'])

        self.response.set_content(f"I have found that {llm_response['descr']} from our chat history matches your request. The information was saved under file {filename}")
        self.response.set_metadata({
            "timestamp": llm_response['timestamp'],
            "filename": llm_response['filename'],
            "descr": llm_response['descr']
        })

        return self.response

