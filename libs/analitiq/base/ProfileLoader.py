import logging
import os
import yaml
import importlib.util
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, validator, ValidationError, model_validator
from pathlib import Path


class DatabaseConnection(BaseModel):
    name: str
    type: str
    host: str
    user: str
    password: str
    port: int
    dbname: str
    dbschema: Optional[str] = None
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


    @validator('type')
    def validate_type(cls, v):
        assert v in ['openai', 'mistral', 'bedrock'], f"Invalid LLM type: {v}"
        return v


class VectorDBConnection(BaseModel):
    type: str
    name: str
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
        usage_dict = self.usage.dict(exclude_none=True)  # exclude_none=True to skip optional fields that are not set
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
    ConfigLoader is responsible for loading project configuration from a YAML file
    and dynamically importing the specified services.
    """

    def __init__(self, file_path: str):
        """
        Initializes the ProjectLoader with an empty list of services and a dictionary for profiles.
        """
        #home_directory = Path.home()
        #self.file_path = home_directory / file_path
        self.file_path = Path(file_path)

    def load_and_validate_config(self, profile_name) -> Configuration:
        with open(self.file_path, 'r') as file:
            profiles = yaml.safe_load(file)

        validated_profiles = {}
        for profile_name, config in profiles.items():
            try:
                validated_config = Configuration(**profiles[profile_name])
                specified_configs = validated_config.validate_and_load()
                logging.info(f"Configuration for profile '{profile_name}' loaded and validated successfully.")
            except ValidationError as e:
                print(f"Validation error for profile '{profile_name}':", e)

        return specified_configs



