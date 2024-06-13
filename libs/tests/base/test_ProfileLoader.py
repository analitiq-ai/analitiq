import unittest
from unittest.mock import MagicMock
from libs.analitiq.base.ProfileLoader import ProfileLoader
from pydantic import BaseModel, validator, ValidationError
import yaml
from pathlib import Path
import os



class TestProfileLoader(unittest.TestCase):
    def setUp(self):
        self.profile_config = {
            "profile1": {
                "connections": {
                    "databases": [
                        {"name": "db1", "type": "postgres", "host":"localhost", "user":"xxxx",  "username":"xxxx", "password":"xxxxx", "port":5432, "dbname":"analitiq", "db_name":"analitiq"},
                        {"name": "db2", "type": "postgres", "host":"localhost", "user":"xxxx", "username":"xxxx", "password":"xxxxx", "port":5432, "dbname":"analitiq", "db_name":"analitiq"},
                    ],
                    "llms": [
                        {"name": "llm1", "type": "openai"}
                    ],
                    "vector_dbs": [{
                        "name": "prod_vdb",
                        "type": "weaviate",
                        "collection_name": "my_collection",
                        "host": "example.com",
                        "api_key": "xxxxx"
                    }]
                },
                "usage": {
                    "databases": "db1",
                    "llms": "llm1",
                    "vector_dbs": "prod_vdb"

                }
            },
            "profile2": {
                "connections": {
                    "databases": [
                        {"name": "db1", "type": "postgres", "host":"localhost", "user":"xxxx",  "username":"xxxx", "password":"xxxxx", "port":5432, "dbname":"analitiq", "db_name":"analitiq"},
                        {"name": "db2", "type": "postgres", "host":"localhost", "user":"xxxx", "username":"xxxx", "password":"xxxxx", "port":5432, "dbname":"analitiq", "db_name":"analitiq"},
                    ],
                    "llms": [
                        {"name": "llm1", "type": "openai"}
                    ],
                    "vector_dbs": [{
                        "name": "vector_db1",
                        "type": "weaviate",
                        "collection_name": "my_collection",
                        "host": "example.com",
                        "api_key": "xxxxx"
                    }]
                },
                "usage": {
                    "databases": "db1",
                    "llms": "llm1",
                    "vector_dbs": "vector_db1"
                }
            }
        }
        cwd =  os.getcwd()
        file_path = cwd + "/libs" + '/profiles.sample.yml'
        with open(file_path, 'r') as file:
            self.profile_config = yaml.safe_load(file)
        self.profile_loader = ProfileLoader(self.profile_config)

    def test_validate_and_load(self):
        # Test successful validation and loading of profile1
        specified_configs = self.profile_loader._validate_config("test")
        print(specified_configs)
        self.assertEqual(specified_configs["databases"].name, "prod_dw")
        self.assertEqual(specified_configs["llms"].name, "aws_llm")

        # Test successful validation and loading of profile2
        # specified_configs = self.profile_loader._validate_config("profile2")
        # self.assertEqual(specified_configs["vector_dbs"].name, "vector_db1")

        # Test validation error for non-existent profile
        # with self.assertRaises(KeyError):
        #     self.profile_loader._validate_config("profile3")

        # Test validation error for invalid configuration
        # self.profile_config["profile1"]["connections"]["databases"][0]["type"] = "invalid_type"
        # with self.assertRaises(ValidationError):
        #     self.profile_loader._validate_config("profile1")

if __name__ == "__main__":
    unittest.main()
