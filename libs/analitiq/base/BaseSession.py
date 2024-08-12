import os
from uuid import uuid4
from analitiq.base.GlobalConfig import GlobalConfig


class BaseSession:
    def __init__(self):
        self.session_uuid = self.get_or_create_session_uuid()
        self.session_uuid_file = "./session_uuid.txt"

    def get_or_create_session_uuid(self):
        # Path to the file where the session UUID is stored
        self.session_uuid_file = GlobalConfig().get_session_uuid_file()

        # Check if the session UUID file exists and read the UUID
        if os.path.exists(self.session_uuid_file):
            with open(self.session_uuid_file, "r") as file:
                session_uuid = file.read().strip()
                return session_uuid
        else:
            # If the file does not exist, create a new UUID and save it
            new_uuid = str(uuid4())
            with open(self.session_uuid_file, "w") as file:
                file.write(new_uuid)
            return new_uuid

    def reset_session(self):
        # Generate a new UUID and overwrite the existing one
        new_uuid = str(uuid4())
        self.session_uuid_file = GlobalConfig().get_session_uuid_file()

        with open(self.session_uuid_file, "w") as file:
            file.write(new_uuid)
        self.session_uuid = new_uuid
        # Optionally, clear session data in other components
