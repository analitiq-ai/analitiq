import logging
from analitiq.base.BaseMemory import BaseMemory
from analitiq.llm.BaseLlm import AnalitiqLLM
from analitiq.base.TaskManager import TaskManager
from analitiq.base.BaseService import BaseResponse
from analitiq.utils.general import *

logging.basicConfig(
    filename='task_op.log'
    ,encoding='utf-8'
    ,filemode='w'
    ,level=logging.INFO
    ,format='%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])'
    ,datefmt='%d/%m/%Y %I:%M:%S %p'
)

from analitiq.base.Graph import Graph, Node
from analitiq.base.BaseSession import BaseSession
from analitiq.base.GlobalConfig import GlobalConfig

from analitiq.prompt import (
    HELP_RESPONSE
)

# import langchain
# langchain.debug = True

class Analitiq():

    def __init__(self, user_prompt):
        """
        self.prompts is a dictionary that will have 1. original prompt as by user and refined prompt by LLM.
        :param user_prompt:
        """
        self.memory = BaseMemory()
        self.services = GlobalConfig().services
        self.avail_services_str = self.get_available_services_str(self.services)
        self.llm = AnalitiqLLM()
        self.prompts = {'original': user_prompt}

    def get_available_services_str(self, avail_services):
        """
        :param avail_services: A dictionary containing the available services. Each service should be represented by a key-value pair, with the key being the name of the service and the value
        * being a dictionary containing the service details.
        :return: A string containing the formatted representation of the available services.

        """
        available_services_list = []

        # Iterate over each item in the Services dictionary
        for name, details in avail_services.items():
            # Determine the appropriate description to use
            description = details['description']
            # Format and add the string to the list
            available_services_list.append(f"{name}: {description}. The input for this tools is {details['inputs']}. The output of this tools is {details['outputs']}.")
            # Join the list into a single string variable, separated by new lines
        available_services_str = "\n".join(available_services_list)

        return available_services_str

    @retry_response(max_retries=3, check_response=is_response_clear)
    def is_prompt_clear(self, user_prompt, msg_lookback: int = 2, feedback: str = None):
        """

        :param user_prompt:
        :param msg_lookback: Because the current prompt is already written to chat log, we need to go back 2 steps to get the previous prompt.
        :param feedback: Feedback to the LLM model after failed runs to help the model fix an issue.
        :return:
        """

        response = self.llm.llm_is_prompt_clear(user_prompt, self.avail_services_str)

        # is LLM does not need any further explanation, we return the prompt
        if not response.Clear:
            # Log that the model needs clarification
            logging.info(f"[Analitiq] Prompt not clear: '{user_prompt}'. Needs explanation:\n{str(response)}")

            try:
                chat_hist = self.get_chat_hist(user_prompt, msg_lookback)
            except Exception as e:
                logging.error(f"[Analitiq] Error retrieving chat history: {e}")
                return (response, False)

            # if response is not clear and there is no chat history, we exit and send the message ot the user.
            if not chat_hist:
                logging.info(f"[Analitiq] No chat history found.")
                return (response, False)

            logging.info(f"[Analitiq] Chat history: '{chat_hist}'")
            user_prompt = chat_hist + "\n" + user_prompt

        return (response, True)  # to indicate chat_hist existence

    def get_chat_hist(self, user_prompt, msg_lookback: int = 5):
        """
        Gets the chat history for a user prompt.
        This function retrieves recent user prompts from the conversation history,
        specifically those marked with an 'entity' value of 'Human', and within
        the last 5 minutes. It then combines these prompts with the current user
        prompt, if the current prompt is not already present in the history.
        The combined prompt is constructed by concatenating these unique prompts
        into a single string, separated by periods. If the user prompt is the only
        prompt, or if it's the first unique prompt in the specified time frame,
        it is returned as is.
        Note:
        - This function relies on `BaseMemory.get_last_messages_within_minutes` method to fetch
          historical prompts. Ensure `BaseMemory` is properly initialized and configured.
        - This function assumes that the `BaseMemory` method successfully returns a list of
          message dictionaries, each containing at least a 'content' key.
        - The chronological order of prompts in the combined string is determined by the order
          of prompts retrieved from the conversation history, with the current user prompt added last.


        :param user_prompt: The user prompt.
        :param msg_lookback: The number of messages to look back in the chat history. Default is 5.
        :return: The response generated based on the chat history, or None if there is no chat history.
        """

        user_prompt_hist = self.memory.get_last_messages_within_minutes(msg_lookback, 5, 1, 'Human')

        response = None

        if not user_prompt_hist:
            return response

        user_prompt_list = list({message['content'] for message in user_prompt_hist})

        if len(user_prompt_list) > 0:
            user_prompt_w_hist = '\n'.join(user_prompt_list)

            response = self.llm.llm_summ_user_prompts(user_prompt, user_prompt_w_hist)

            logging.info(f"[Prompt][Change From]: {user_prompt_w_hist}\n[Prompt][Change To]: {response}")

        return response

    def convert_task_list_to_dict(self, task_list):

        # Convert list of objects into a dictionary where name is the key and description is the value
        task_dict = {item.Name: {'Name': item.Name, 'Using': item.Using, 'Description': item.Description} for item in task_list}

        return task_dict


    def select_services(self, user_prompt, task_list):
        """
        :param user_prompt: The prompt to be displayed to the user to select services.
        :param task_list: A dictionary containing the task names and descriptions.
        :return: A dictionary containing the selected services with their details.

        This method takes a user prompt and a task list as input parameters. It iterates over each item in the task list and formats the name and description of each task. These formatted strings
        * are then appended to a list. The list is then joined into a single string variable, with each item separated by a new line.

        The method calls the 'llm_select_services' method with the user prompt, the required services string, and the available services string. The 'llm_select_services' method returns a list
        * of selected services.

        The list of selected services is then converted into a dictionary, where the name of the service is used as the key and the name, description, task name, and confidence are used as the
        * values.

        Finally, the dictionary of selected services is returned.
        """
        # Initialize an empty list to hold the formatted strings

        required_services_list = []

        # Iterate over each item in the Services dictionary
        for name, description in task_list.items():
            # Format and add the string to the list
            required_services_list.append(f"{name}: {description}")

        # Join the list into a single string variable, separated by new lines
        required_services_str = "\n".join(required_services_list)

        selected_services = self.llm.llm_select_services(user_prompt, required_services_str, self.avail_services_str)

        # Convert list of objects into a dictionary where name is the key and description is the value
        service_dict = {service.Name: {'Name': service.Name, 'Description': service.Description, 'Task': service.TaskName, 'Conf': service.Confidence} for service in selected_services}

        return service_dict

    def build_service_dependency(self, user_prompt, available_services, selected_services):
        """Decide which tool(s) to use based on the user prompt in which order.
            This is a placeholder function. Integration with an LLM for decision-making goes here."""
        # Example: Return a tool based on a keyword in the prompt.
        # In a real scenario, this function would interact with an LLM to make an informed decision.

        # Convert each service's details into a formatted string

        selected_service_details_list = []

        for service_name, description in selected_services.items():
            selected_service_details_list.append(f"{service_name}: {description}")

        selected_service_details_str = "\n".join(selected_service_details_list)

        service_dependency_list = self.llm.llm_build_service_dependency(user_prompt, self.avail_services_str, selected_service_details_str)

        # Convert list of objects into a dictionary where name is the key and description is the value
        service_dependency_dict = {service.Name: {'Name': service.Name, 'Dependencies': service.Dependencies} for service in service_dependency_list}

        return service_dependency_dict

    def run(self, user_prompt):
        """

        :param user_prompt:
        :return:
        """
        session = BaseSession()
        session_uuid = session.get_or_create_session_uuid()

        # First, we check if user typed Help. If so, we can skiop the rest of the logic, for now
        if user_prompt.lower() == 'help':
            return HELP_RESPONSE + '\n'.join([f"{details['name']}: {details['description']}" for details in self.services.values()])

        logging.info(f"\nUser query: {user_prompt}")

        # check if there are user hints in the prompt
        self.prompts['original'], self.prompts['hints'] = extract_hints(user_prompt)

        self.memory.log_human_message(user_prompt)
        self.memory.save_to_file()

        # we now trigger the main forward logic: goal -> tasks -> services/tools -> outcome

        # Step 1 - Is the task clear? IF not and there is no history to fall back on, exit with feedback.
        prompt_clear_response = self.is_prompt_clear(self.prompts['original'])

        if not prompt_clear_response.Clear:
            return {'Analitiq': BaseResponse(content=prompt_clear_response.Feedback, metadata={})}

        # add the refined prompts by the model.
        self.prompts['refined'] = prompt_clear_response.Query
        self.prompts['feedback'] = prompt_clear_response.Feedback
        user_prompt = self.prompts['refined']

        logging.info(f"\nRefined prompt context: {self.prompts}")

        task_mngr = TaskManager()

        # Step 2 - Generate a list of the tasks needed
        tasks_list = task_mngr.create_task_list(self.llm, self.prompts, self.avail_services_str)

        if tasks_list is False:
            return "Could not formulate tasks."

        # Step 3 - Refine task list to the minimum
        refined_task_list = task_mngr.refine_tasks_until_stable(self.llm, user_prompt, tasks_list)
        #refined_task_list2 = task_mngr.combine_tasks_pairwise(self.llm, user_prompt, refined_task_list) TODO refine pairwise task evaluation

        selected_services = self.select_services(user_prompt, refined_task_list)
        logging.info(f"\n[Services][Selected]:\n{selected_services}")



user_prompt = "How do we calculate revenue?"

a = Analitiq(user_prompt)
services_responses = a.run(user_prompt)
for service_name, response in services_responses.items():
    print(service_name)
    print(response.content)

