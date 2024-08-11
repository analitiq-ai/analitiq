from analitiq.logger.logger import logger
import os
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from analitiq.base.BaseResponse import BaseResponse
from analitiq.base.BaseSession import BaseSession
from analitiq.base.GlobalConfig import GlobalConfig
from enum import Enum


class EntityType(Enum):
    HUMAN = "Human"
    ANALITIQ = "Analitiq"


class BaseMemory:
    def __init__(self):
        self.conversations = []
        self.start_time = datetime.now()
        self.log_directory = GlobalConfig().get_chat_log_dir()
        session = BaseSession()
        self.session_uuid = session.get_or_create_session_uuid()
        # filename = f"{self.start_time.strftime('%Y%m%d%H%M%S')}.log"
        self.filename = f"{self.session_uuid}.log"

    def log_service_message(self, service_response: BaseResponse) -> None:
        content = service_response.get_content_str()

        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "entity": EntityType.ANALITIQ.value,
            "content": content,
            "metadata": service_response.metadata,
            "source_class_name": service_response.service_name,
        }
        self.conversations.append(conversation_entry)

    def log_human_message(self, message: str) -> None:
        """Logs a single entity message along with the service response."""
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "entity": EntityType.HUMAN.value,
            "content": message,
        }
        self.conversations.append(conversation_entry)

    def save_to_file(self):
        """Saves the current conversation history to a flat file."""
        # Ensure log directory exists
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

        file_path = os.path.join(self.log_directory, self.filename)

        with open(file_path, "a") as file:
            for conversation in self.conversations:
                file.write(json.dumps(conversation) + "\n")

        self.clear_memory()

    def clear_memory(self):
        """Clears the in-memory conversation history."""
        self.conversations = []

    def get_last_messages(self, num_messages: int) -> List[Dict[str, Any]]:
        """A function to retrieve the last number messages from Chat history. Number of messages is specified by the input param.
        :param num_messages:
        :return:
        """
        if not self.session_uuid:
            raise ValueError("Session UUID is not set.")

        file_path = os.path.join(self.log_directory, self.filename)

        if not os.path.exists(file_path):
            logger.info(f"No chat history file found for session UUID {self.session_uuid}.")
            return

        with open(file_path, "r") as file:
            all_messages = [json.loads(line.strip()) for line in file]

        # Return the last `num_messages` entries from the chat history
        return all_messages[-num_messages:]

    def get_last_messages_within_minutes(
        self, num_messages: int, minutes: int, offset: int = 1, entity: str = None
    ) -> List[Dict[str, Any]]:
        """A function to retrieve the last `num_messages` from Chat history within `minutes` minutes from now,
        optionally filtering by an entity type if specified.

        :param offset: How much to offset the search. usualy it is 1 because the last prompt was recorded and in most scenarios we want history before.
        :param num_messages: The maximum number of messages to return
        :param minutes: The time frame in minutes to look for messages
        :param entity: The entity type to filter messages by (e.g., "Human", "Analitiq"). If None, no entity filter is applied.
        :return: A list of chat messages that meet the criteria
        """
        if not self.session_uuid:
            raise ValueError("Session UUID is not set.")

        file_path = os.path.join(self.log_directory, self.filename)

        if not os.path.exists(file_path):
            logger.info(f"No chat history file found for session UUID {self.session_uuid}.")
            return

        now = datetime.now()
        min_time = now - timedelta(minutes=minutes)

        filtered_messages = []

        with open(file_path, "r") as file:
            for line in file:
                message = json.loads(line.strip())
                message_time = datetime.fromisoformat(message["timestamp"])
                if message_time > min_time:
                    # If entity is specified, check if the message's entity matches the given entity
                    if entity is None or message.get("entity") == entity:
                        filtered_messages.append(message)

        # Adjust the slice to include the offset
        start_index = -num_messages - offset
        end_index = None if offset == 0 else -offset
        return filtered_messages[start_index:end_index]
