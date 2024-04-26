import logging
from analitiq.base.BaseMemory import BaseMemory
from analitiq.llm.BaseLlm import AnalitiqLLM
from analitiq.utils.task_mgmt import TaskManager
from analitiq.base.BaseService import BaseResponse
from analitiq.utils.general import *

logging.basicConfig(
    filename='logs/latest_run.log'
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
        Here we convert available services from a dictionary into a string so it can be placed into a prompt.
        :return:
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

        response = self.llm.llm_is_prompt_clear(user_prompt)

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
        This function retrieves recent user prompts from the conversation history,
        specifically those marked with an 'entity' value of 'Human', and within
        the last 5 minutes. It then combines these prompts with the current user
        prompt, if the current prompt is not already present in the history.
        The combined prompt is constructed by concatenating these unique prompts
        into a single string, separated by periods. If the user prompt is the only
        prompt, or if it's the first unique prompt in the specified time frame,
        it is returned as is.

        Parameters:
        - user_prompt (str): The current user prompt to be combined with the historical prompts.

        Returns:
        - str: A single string consisting of the combined prompts. If there's only the current
               user prompt, it is returned without modification. If there are historical prompts
               within the specified timeframe and they are unique, they are concatenated
               with the current prompt, separated by periods.

        Raises:
        - ValueError: If the `user_prompt` is empty or not a string.
        - Any exceptions raised by `memory.get_last_messages_within_minutes` method,
          such as connectivity issues or timeouts when retrieving historical prompts.

        Note:
        - This function relies on `BaseMemory.get_last_messages_within_minutes` method to fetch
          historical prompts. Ensure `BaseMemory` is properly initialized and configured.
        - This function assumes that the `BaseMemory` method successfully returns a list of
          message dictionaries, each containing at least a 'content' key.
        - The chronological order of prompts in the combined string is determined by the order
          of prompts retrieved from the conversation history, with the current user prompt added last.
        """

        user_prompt_hist = self.memory.get_last_messages_within_minutes(msg_lookback, 5, 1, 'Human')
        print(user_prompt_hist)

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
        Selects appropriate service tools based on a user's prompt by utilizing a language model (LLM) for decision-making.

        This function analyzes a given user prompt and a dictionary mapping tools to tasks, and decides which tools are best suited to perform the required tasks. It interacts with a language model to evaluate the appropriateness of each available tool against the tasks extracted from the user prompt.

        Parameters:
            user_prompt (str): The user's input describing the task or requirement.
            task_list (dict): A dictionary where keys are tool names and values are descriptions of the tasks they perform.

        Returns:
            dict: A dictionary where each key is a tool name and the value is its description, representing the tools selected by the LLM to best meet the user's requirements.

        Usage:
            response = instance.select_services("extract top 10 customer data", {"QueryDatabase": "Queries databases"})
            print(response)  # Prints the names and descriptions of the selected tools

        Notes:
            The `services` attribute of the instance should be a dictionary containing details of all available tools.
            This function is a placeholder for integration with an LLM. In its current implementation, it simulates decision-making based on hardcoded logic.
            After selecting the tools, the function formats the service information into a readable string format and sends it to the LLM for final decision-making.
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
        print(selected_services)
        # Convert list of objects into a dictionary where name is the key and description is the value
        service_dict = {service.Name: {'Name': service.Name, 'Description': service.Description, 'Task': service.TaskName} for service in selected_services}

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

            help_resp = HELP_RESPONSE
            for name, details in self.services.items():
                help_resp = help_resp + details['name'] + ": " + details['description'] + "\n"
            return help_resp

        logging.info(f"\nUser query: {user_prompt}")
        # add original prompts by the user.
        self.prompts['original'] = user_prompt
        self.memory.log_human_message(user_prompt)
        self.memory.save_to_file()

        # we now trigger the main forward logic: goal -> tasks -> services/tools -> outcome

        # Step 1 - Is the task clear? IF not and there is no history to fall back on, exit with feedback.
        prompt_clear_response = self.is_prompt_clear(user_prompt)

        if not prompt_clear_response.Clear:
            return {'Analitiq': BaseResponse(content=prompt_clear_response.Feedback, metadata={})}

        # add the refined prompts by the model.
        self.prompts['refined'] = prompt_clear_response.Query
        self.prompts['hints'] = prompt_clear_response.Hints
        user_prompt = self.prompts['refined']

        logging.info(f"\nRefined query: {user_prompt}")

        task_mngr = TaskManager()

        # Step 2 - Generate a list of the tasks needed
        tasks_list = task_mngr.create_task_list(self.llm, user_prompt)

        if tasks_list is False:
            return "Could not formulate tasks."

        # Step 3 - Refine task list to the minimum
        refined_task_list = task_mngr.refine_tasks_until_stable(self.llm, user_prompt, tasks_list)
        #refined_task_list2 = task_mngr.combine_tasks_pairwise(self.llm, user_prompt, refined_task_list) TODO refine pairwise task evaluation

        selected_services = self.select_services(user_prompt, refined_task_list)
        logging.info(f"\n[Services][Selected]:\n{selected_services}")
        exit()

        # Building node dependency
        # Check if the list contains exactly one item
        if len(selected_services) == 0:
            return "No services selected."
        elif len(selected_services) == 1:
            # Create instances of ServiceDependencies with just the name of first item in selected services
            service_dependency = {next(iter(selected_services)): []}
        else:
            service_dependency = self.build_service_dependency(user_prompt, self.services, selected_services)

        # Initialize the execution graph with the context
        graph = Graph(self.services)

        logging.info(f"\n\n[Service][Dependency]:\n{service_dependency}")

        # First, create all nodes without setting dependencies
        nodes = {}  # Temporary storage to easily access nodes by name

        for service, details in selected_services.items():
            if service not in self.services:
                logging.warning(f"Trying to add non existent service: {service}")
                continue

            node = Node(service, self.services[service]['path'], details['Description'])
            graph.add_node(node)
            nodes[service] = node  # Store the node for easy access

        # Then, set up dependencies based on the JSON response
        for service, details in service_dependency.items():
            if service not in self.services:
                logging.warning(f"Trying to add non existent service: {service}")
                continue

            try:
                node = nodes.get(service)  # Retrieve the node from temporary storage
                logging.info(f"Found node:{service}")
                for dep in details['Dependencies']:
                    logging.info(f" - Dependency Name {dep}")
                    dependency_node = graph.nodes.get(dep)
                    if node and dependency_node:
                        logging.info(f" -- Added Dependency Node: {service}")
                        node.add_dependency(dependency_node)
            except:
                logging.warning(f"Node not found:{service}")

        # Now, the graph is ready, and you can execute it
        graph.get_dependency_tree()

        node_outputs = graph.run()

        return node_outputs

