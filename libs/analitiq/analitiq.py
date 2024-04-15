import logging
from analitiq.base.BaseMemory import BaseMemory
from analitiq.llm.BaseLlm import AnalitiqLLM

logging.basicConfig(
    filename='logs/latest_run.log'
    ,encoding='utf-8'
    ,filemode='w'
    ,level=logging.DEBUG
    ,format='%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])'
    ,datefmt='%d/%m/%Y %I:%M:%S %p'
)

from analitiq.base.Graph import Graph, Node
from analitiq.base.BaseSession import BaseSession
from analitiq.base.GlobalConfig import GlobalConfig

from analitiq.prompt import (
    HELP_RESPONSE
)


class Analitiq():

    def __init__(self, user_prompt):
        self.memory = BaseMemory()
        self.services = GlobalConfig().services
        self.llm = AnalitiqLLM(user_prompt)

    def is_prompt_clear(self, user_prompt):

        # Because current prompt is written to chat log, we need to go back 2 steps in chat history to get prior prompt
        msg_lookback = 2
        response = self.llm.llm_is_prompt_clear(user_prompt)

        # is LLM does not need any further explanation, we return the prompt
        if response.Clear is True:
            return user_prompt

        while response.Clear is False:
            # Log that the model needs clarification
            logging.info(f"Checking history for prompt '{user_prompt}'. Needs explanation: {response.Feedback}")

            # Refine the prompt using chat history.
            refined_prompt = self.combine_prompt_with_hist(user_prompt, msg_lookback)

            # Try to get task list again with the refined prompt
            response = self.llm.llm_is_prompt_clear(refined_prompt)
            logging.info(response)

            msg_lookback += 1
            if msg_lookback > 5:
                logging.warning(f"Prompt refinement process exceeded 3 iterations with no resolution. {response.Feedback}")
                return (f"Prompt is not clear: {response.Feedback}")

            user_prompt = refined_prompt
        logging.info(f"\nFinal user prompt '{user_prompt}'.")
        return user_prompt

    def combine_prompt_with_hist(self, user_prompt, num_messages: int = 5, ):
        """
        Combines the given user prompt with historical prompts from conversations
        within the last 5 minutes, ensuring unique and chronological incorporation
        of prompts.

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

        user_prompt_hist = self.memory.get_last_messages_within_minutes(num_messages,5, 'Human')

        # by default, we return current prompt
        response = user_prompt

        if user_prompt_hist is None:
            return response

        user_prompt_list = list({message['content'] for message in user_prompt_hist})

        if len(user_prompt_list) > 0:
            user_prompt_w_hist = '\n'.join(user_prompt_list)

            response = self.llm.llm_summ_user_prompts(user_prompt_w_hist)

            logging.info(f"Summarised user prompts: {user_prompt_w_hist} \n\n Into: {response}")

        return response

    def convert_task_list_to_dict(self, task_list):
        # Convert list of objects into a dictionary where name is the key and description is the value
        dict = {item.Name: {'Name': item.Name, 'Using': item.Using, 'Description': item.Description} for item in task_list}

        return dict

    def get_task_list(self, user_prompt: str):
        tasks_list = self.llm.llm_create_task_list(user_prompt)

        # Ensure the list is not empty to avoid IndexError
        if not tasks_list:
            return False

        logging.info(f"Task list: {tasks_list}")
        # Convert list of objects into a dictionary where name is the key and description is the value
        return tasks_list

    def refine_tasks_until_stable(self, user_prompt: str, tasks_list):
        num_tasks = len(tasks_list)
        i = 0
        refined_tasks_list = "\n".join(f"{task.Name}: {task.Description} using {task.Using}." for task in tasks_list)
        response = self.llm.llm_refine_task_list(user_prompt, refined_tasks_list)

        while num_tasks != len(response.TaskList):
            num_tasks = len(response.TaskList)
            logging.info(f"\nModel input list of tasks [Iteration {i}][Tasks: {len(response.TaskList)}]: \n {refined_tasks_list}")
            response = self.llm.llm_refine_task_list(user_prompt, refined_tasks_list)

            # make task list from list of objects into a string
            refined_tasks_list = "\n".join(f"{task.Name}: {task.Description} using {task.Using}." for task in response.TaskList)
            logging.info(f"\nModel output list of tasks [Iteration: {i}][Tasks: {len(response.TaskList)}]: \n {refined_tasks_list}")
            i = i+1

            if i >= 5:
                logging.warning(f"Too many iterations of task optimisations: {i}")
                dict = {item.Name: {'Name': item.Name, 'Using': item.Using, 'Description': item.Description} for item in response.TaskList}
                return dict

                # Convert list of objects into a dictionary where name is the key and description is the value
        dict = {item.Name: {'Name': item.Name, 'Using': item.Using, 'Description': item.Description} for item in response.TaskList}
        return dict

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

        available_services_list = []

        # Iterate over each item in the Services dictionary
        for name, details in self.services.items():
            # Determine the appropriate description to use
            description = details['description'] if details['description'] else details.get('class_docstring_description', 'No description available')
            # Format and add the string to the list
            available_services_list.append(f"{name}: {description}")
        # Join the list into a single string variable, separated by new lines
        available_services_str = "\n".join(available_services_list)

        required_services_list = []

        # Iterate over each item in the Services dictionary
        for name, description in task_list.items():
            # Format and add the string to the list
            required_services_list.append(f"{name}: {description}")

        # Join the list into a single string variable, separated by new lines
        required_services_str = "\n".join(required_services_list)

        selected_services = self.llm.llm_select_services(user_prompt, required_services_str, available_services_str)

        # Convert list of objects into a dictionary where name is the key and description is the value
        service_dict = {service.Name: {'Name': service.Name, 'Description': service.Description, 'Task': service.TaskName} for service in selected_services}

        return service_dict

    def build_service_dependency(self, user_prompt, available_services, selected_services):
        """Decide which tool(s) to use based on the user prompt in which order.
            This is a placeholder function. Integration with an LLM for decision-making goes here."""
        # Example: Return a tool based on a keyword in the prompt.
        # In a real scenario, this function would interact with an LLM to make an informed decision.

        # Convert each service's details into a formatted string
        available_service_details_list = []

        for service_name, details in available_services.items():
            service_str = f"{service_name}: Inputs: {details['inputs']}. Outputs: {details['outputs']}"
            available_service_details_list.append(service_str)

        available_service_details_str = "\n".join(available_service_details_list)

        selected_service_details_list = []

        for service_name, description in selected_services.items():
            selected_service_details_list.append(f"{service_name}: {description}")

        selected_service_details_str = "\n".join(selected_service_details_list)

        service_dependency_list = self.llm.llm_build_service_dependency(user_prompt, available_service_details_str, selected_service_details_str)

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
        self.memory.log_human_message(user_prompt)
        self.memory.save_to_file()

        # we now trigger the main forward logic: goal -> tasks -> services/tools -> outcome

        # Step 1 - Is the task clear?
        user_prompt = self.is_prompt_clear(user_prompt)

        # Step 2 - Formulate the tasks
        tasks_list = self.get_task_list(user_prompt)

        if tasks_list is False:
            return "Could not formulate tasks."

        # Step 3 - Refine task list to the minimum
        refined_task_list = self.refine_tasks_until_stable(user_prompt, tasks_list)

        selected_services = self.select_services(user_prompt, refined_task_list)
        logging.info(f"\n\nSelected services:\n{selected_services}")

        # Building node dependency
        # Check if the list contains exactly one item
        if len(selected_services) == 1:
            # Create instances of ServiceDependencies with just the name of first item in selected services
            service_dependency = {next(iter(selected_services)): []}
        else:
            service_dependency = self.build_service_dependency(user_prompt, self.services, selected_services)

        # Initialize the execution graph with the context
        graph = Graph(self.services)

        logging.debug(f"\n\nService dependency:\n{service_dependency}")

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

