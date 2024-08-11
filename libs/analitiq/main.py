import sys
from typing import Dict, Optional, Any

from analitiq.vectordb.weaviate import WeaviateHandler

from analitiq.logger.logger import logger
from analitiq.base.BaseMemory import BaseMemory
from analitiq.base.Database import DatabaseWrapper
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.base.BaseResponse import BaseResponse
from analitiq.utils.general import extract_hints
from analitiq.base.GlobalConfig import GlobalConfig
from analitiq.base.Graph import Graph
from analitiq.base.BaseSession import BaseSession

HELP_RESPONSE = """
Analitiq [v{version}] is an AI assistant that can examine your SQL files and database structure and answer common questions about your data.

Database: {db}
Collection: {vdb_collection_name}

_help_ - get help menu.
_fail_ - mark responses from Analitiq that are not accurate.
_params_ - get parameters and connections used by Analitiq.

Services that are currently connected:
"""

# import langchain
# langchain.debug = True

sys.path.append("/analitiq")


#  db_params: Dict = None, llm_params: Dict = None, vdb_params: Dict = None
class Analitiq:
    """Analitiq core Class."""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize the Analitiq module."""
        self.response = BaseResponse(self.__class__.__name__)

        self.db: DatabaseWrapper() = None
        self.llm: BaseLlm() = None
        self.vdb = None

        if not params or not params.get("db_params"):
            GlobalConfig().load_profiles()
            self.db_params = GlobalConfig().profile_configs["databases"].model_dump()
        else:
            self.db_params = params["db_params"]

        if not params or not params.get("llm_params"):
            GlobalConfig().load_profiles()
            self.llm_params = GlobalConfig().profile_configs["llms"].model_dump()
        else:
            self.llm_params = params["llm_params"]

        if not params or not params.get("vdb_params"):
            GlobalConfig().load_profiles()
            self.vdb_params = GlobalConfig().profile_configs["vector_dbs"].model_dump()
        else:
            self.vdb_params = params["vdb_params"]

        self.memory = BaseMemory()
        self.services = GlobalConfig().services
        self.avail_services_str = self.get_available_services_str(self.services)

        self.prompts = {"original": "", "refined": "", "feedback": ""}

    def load_connections(self):
        """Load the connection."""
        failures = 0
        tasks = [
            ("db", DatabaseWrapper, self.db_params, "Unable to connect to the Database"),
            ("llm", BaseLlm, self.llm_params, "Unable to set LLM"),
            ("vdb", self._get_vdb_handler, self.vdb_params, "Unable to connect to the Vector Database"),
        ]
        for attr, task, params, error_msg in tasks:
            try:
                setattr(self, attr, task(params))
            except Exception as e:
                self.response.set_content("Error...")
                self.response.add_text_to_metadata(f"{error_msg}: {e}")
                failures += 1
        return failures

    @staticmethod
    def _get_vdb_handler(vdb_params):
        db_type = vdb_params["type"]

        if db_type == "weaviate":
            try:
                handler = WeaviateHandler(vdb_params)
            except Exception as e:
                msg = f"Failed to connect to the vector database: {e}{handler}"
                raise Exception(msg)
        elif db_type == "chromadb":
            from .vectordb.chromadb import ChromaHandler

            handler = ChromaHandler(vdb_params)
        else:
            msg = f"Unsupported database type: {db_type}"
            raise ValueError(msg)

        if handler.connected:
            return handler
        else:
            errmsg = "Failed to establish a connection to the vector database."
            logger.error("%s", errmsg)
            raise Exception(errmsg)

    def get_available_services_str(self, avail_services):
        """Get available Services.

        :param avail_services: A dictionary containing the available services.
        Each service should be represented by a key-value pair, with the key being the name of
        the service and the value
        * being a dictionary containing the service details.
        :return: A string containing the formatted representation of the available services.
        """
        available_services_list = []

        # Iterate over each item in the Services dictionary
        for name, details in avail_services.items():
            # Determine the appropriate description to use
            description = details["description"]
            # Format and add the string to the list
            service_msg = f"{name}: {description}. The input for this tools is {details['inputs']}."
            service_msg = service_msg + f"The output of this tools is {details['outputs']}."
            available_services_list.append(service_msg)
            # Join the list into a single string variable, separated by new lines
        available_services_str = "\n".join(available_services_list)

        return available_services_str

    def is_prompt_clear(self, user_prompt, msg_lookback: int = 2):
        """Return if the prompt is clear.

        :param user_prompt:
        :param msg_lookback: Because the current prompt is already written to chat log,
          we need to go back 2 steps to get the previous prompt.
        :param feedback: Feedback to the LLM model after failed runs to help the model fix an issue.
        :return:
        """
        response = None
        try:
            response = self.llm.llm_is_prompt_clear(user_prompt, self.avail_services_str)
        except Exception as e:
            logger.error(f"[Analitiq] Exception: '{e}'. Needs explanation:\n{response!s}")

        # is LLM is clear with prompt, we return results
        if response.Clear:
            return response

        # Log that the model needs clarification
        logger.info(f"[Analitiq] Prompt not clear: '{user_prompt}'. Needs explanation:\n{response!s}")

        # we try to get Chat history for more context to the LLM
        try:
            chat_hist = self.get_chat_hist(user_prompt, msg_lookback)
        except Exception as e:
            logger.error(f"[Analitiq] Error retrieving chat history: {e}")
            return response

        # if response is not clear and there is no chat history, we exit with False
        if not chat_hist:
            logger.info("[Analitiq] No chat history found.")
            return response

        # if there is chat history, we add it to the prompt to give LLM more context.
        logger.info(f"[Analitiq] Chat history: '{chat_hist}'")
        user_prompt = chat_hist + "\n" + user_prompt
        response = self.llm.llm_is_prompt_clear(user_prompt, self.avail_services_str)

        return response

    def get_chat_hist(self, user_prompt, msg_lookback: int = 5):
        """Get the chat history for a user prompt.

        This function retrieves recent user prompts from the conversation history,
        specifically those marked with an 'entity' value of 'Human', and within
        the last 5 minutes. It then combines these prompts with the current user
        prompt, if the current prompt is not already present in the history.
        The combined prompt is constructed by concatenating these unique prompts
        into a single string, separated by periods. If the user prompt is the only
        prompt, or if it's the first unique prompt in the specified time frame,
        it is returned as is.

        Note:
        ----
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
        user_prompt_hist = self.memory.get_last_messages_within_minutes(msg_lookback, 5, 1, "Human")

        response = None

        if not user_prompt_hist:
            return response

        user_prompt_list = list({message["content"] for message in user_prompt_hist})

        if len(user_prompt_list) > 0:
            user_prompt_w_hist = "\n".join(user_prompt_list)

            response = self.llm.llm_summ_user_prompts(user_prompt, user_prompt_w_hist)

            logger.info(f"[Prompt][Change From]: {user_prompt_w_hist}\n[Prompt][Change To]: {response}")

        return response

    def return_response(self):
        r"""Return a response.

        Example returned response:
        {
           "Analitiq": "{\"content\": \"Some Text\", \"metadata\": {}}"
        }
        :return: a dictionary containing the "Analitiq" key with the value of `self.response`
        converted to JSON format
        """
        return {"Analitiq": self.response.to_json()}

    def run(self, user_prompt):
        """Run the Service.

        :param user_prompt:
        :return:
        """
        session = BaseSession()
        session.get_or_create_session_uuid()
        # First, we check if user typed Help. If so, we can skiop the rest of the logic, for now
        if user_prompt.lower() == "help":
            text = HELP_RESPONSE.format(
                version=GlobalConfig().project_config["version"],
                db=f"{self.db_params['host']}/{self.db_params['db_name']}",
                vdb_collection_name=self.vdb_params["collection_name"],
            ) + "\n\n".join(
                [f"{details['name']}: {details['description']}" for details in self.services.values()]
            )
            self.response.set_content(text)

            return self.return_response()
        elif user_prompt.lower() == "fail":
            logger.error("[[TAG]]:RESPONSE_FAIL")
            text = "I apologise for poor response. It has been logged for review by developers."
            self.response.set_content(text)
            return self.return_response()

        logger.info(f"[Main] User query: {user_prompt}")

        # Here we load DB, LLM amd VDB. If there are errors, we exit.
        load_errors = self.load_connections()
        if load_errors > 0:
            return self.return_response()

        # check if there are user hints in the prompt
        self.prompts["original"], self.prompts["hints"] = extract_hints(user_prompt)

        self.memory.log_human_message(user_prompt)
        self.memory.save_to_file()

        # we now trigger the main forward logic: goal -> tasks -> services/tools -> outcome

        # Step 1 - Is the task clear? IF not and there is no history to fall back on, exit with feedback.
        # because it is the first try of using LLM, we need to wrap it in TRY
        """
        try:
            prompt_clear_response = self.is_prompt_clear(self.prompts['original'])
        except Exception as e:
            self.response.set_content("Error")
            self.response.add_text_to_metadata(f"{e}")
            return self.return_response()

        if not prompt_clear_response.Clear:
            self.response.set_content(prompt_clear_response.Feedback)
            return self.return_response()

        # add the refined prompts by the model.
        self.prompts['refined'] = prompt_clear_response.Query
        self.prompts['feedback'] = prompt_clear_response.Feedback
        user_prompt = self.prompts['refined']

        logger.info(f"Refined prompt context: {self.prompts}")
        """

        self.prompts["refined"] = self.prompts["original"]

        # TODO we still need to fix the selectin process, so for now we overide and default
        # it to DocSearch service
        """
        #selected_services = self.llm.llm_select_services(self.prompts, self.avail_services_str)

        # Convert list of objects into a dictionary where name is the key and description is the value
        #selected_services = {service.Action: {'Action': service.Action, 'ActionInput':
        # service.ActionInput, 'Instructions': service.Instructions, 'DependsOn': service.DependsOn}
        # for service in selected_services}

        #logger.info(f"[Services][Selected]: {selected_services}")
        """

        selected_services = {
            "SearchDocs": {
                "Action": "Search Documents",
                "ActionInput": "text",
                "Instructions": user_prompt,
                "DependsOn": "",
            }
        }

        # Building node dependency
        # Check if the list contains exactly one item
        if len(selected_services) == 0:
            self.response.set_content("No services selected.")
            return self.return_response()

        # Initialize the execution graph with the context
        graph = Graph(self.services, self.db, self.llm, self.vdb)

        for service, details in selected_services.items():
            graph.add_node(service, details)

        # if there is only one node, there is no dependency, and we exit
        if len(selected_services) > 1:
            graph.build_service_dependency(selected_services)

        # Now, the graph is ready, and you can execute it
        graph.get_dependency_tree()

        node_outputs = graph.run(self.services)

        return node_outputs
