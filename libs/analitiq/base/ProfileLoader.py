import logging
import yaml
from typing import List, Optional
from pydantic import BaseModel, validator, ValidationError
from pathlib import Path


class DatabaseConnection(BaseModel):
    name: str
    type: str
    host: str
    user: str
    password: str
    port: int
    dbname: str
    dbschemas: Optional[List] = None
    threads: Optional[int] = 4
    keepalives_idle: Optional[int] = 240
    connect_timeout: Optional[int] = 10

    @validator('type')
    def validate_type(cls, v):
        assert v in ['postgres', 'redshift'], f"Invalid database type: {v}"
        return v


class LLMConnection(BaseModel):
    type: str
    name: str
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    llm_model_name: Optional[str] = None
    credentials_profile_name: Optional[str] = None
    provider: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: Optional[str] = None

    @validator('type')
    def validate_type(cls, v):
        assert v in ['openai', 'mistral', 'bedrock'], f"Invalid LLM type: {v}"
        return v


class VectorDBConnection(BaseModel):
    type: str
    name: str
    collection_name: str
    host: str
    api_key: str

    @validator('type')
    def validate_type(cls, v):
        assert v in ['weaviate', 'chromadb'], f"Invalid Vector DB type: {v}"
        return v


class Connections(BaseModel):
    databases: Optional[List[DatabaseConnection]]
    llms: Optional[List[LLMConnection]]
    vector_dbs: Optional[List[VectorDBConnection]]


class Usage(BaseModel):
    databases: Optional[str]
    llms: Optional[str]
    vector_dbs: Optional[str]


class Configuration(BaseModel):
    connections: Connections
    usage: Usage

    def validate_and_load(self):
        # Validates usage against connections and loads the specified configs
        usage_dict = self.usage.model_dump(exclude_none=True)  # exclude_none=True to skip optional fields that are not set
        specified_configs = {}
        for category, name in usage_dict.items():
            # Correctly access the connections based on the category
            # First, dynamically access the correct category list from connections
            connection_list = getattr(self.connections, category, [])

            # Find the specified connection by name within the connection list
            connection = next((conn for conn in connection_list if conn.name == name), None)

            if not connection:
                raise ValueError(f"Specified connection '{name}' not found in category '{category}'")

            specified_configs[category] = connection

        return specified_configs


class ProfileLoader:
    """
    Initializes the ProfileLoader with the provided file path.

    :param file_path: The path to the configuration file.
    """

    def __init__(self, profile_config):
        """
        Initializes the ProjectLoader with an empty list of services and a dictionary for profiles.
        """
        self.profile_config = profile_config

    def _validate_config(self, load_profile_name: str) -> Configuration:
        """
        Validate profile configuration

        :param load_profile_name: the name of the profile to load and validate the configuration for
        :return: the specified configurations for the loaded profile
        """

        validated_profiles = {}
        for profile_name, config in self.profile_config.items():
            # skip profiles that user does not want to load
            if load_profile_name == profile_name:
                try:
                    validated_config = Configuration(**self.profile_config[profile_name])
                    specified_configs = validated_config.validate_and_load()
                    logging.info(f"Configuration for profile '{profile_name}' loaded and validated successfully.")
                except ValidationError as e:
                    print(f"Validation error for profile '{profile_name}':", e)

        return specified_configs



