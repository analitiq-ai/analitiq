from sqlalchemy import create_engine
from analitiq.base.base_relational_database import BaseRelationalDatabase
from analitiq.logger.logger import initialize_logging
from sqlalchemy.exc import SQLAlchemyError

logger, chat_logger = initialize_logging()

class PostgresqlConnector(BaseRelationalDatabase):
    """Database wrapper for PostgreSQL databases."""

    def create_engine(self):

        engine_options = {}
        if self.params.get("db_schemas"):
            schemas_str = ",".join(self.params["db_schemas"])
            engine_options["connect_args"] = {"options": f"-csearch_path={schemas_str}"}
        # Create a redacted version of the connection string for logging
        redacted_url = (
            f"postgresql+psycopg2://{self.params['username']}:*****@"
            f"{self.params['host']}:{self.params['port']}/{self.params['db_name']}"
        )

        # Print or log the redacted URL
        logger.info(f"Connecting to database: {redacted_url}")
        try:
            engine = create_engine(
                f"postgresql+psycopg2://{self.params['username']}:{self.params['password']}@"
                f"{self.params['host']}:{self.params['port']}/{self.params['db_name']}",
                **engine_options,
            )

            # Attempt to connect to the database to confirm the connection
            with engine.connect() as connection:
                logger.info(f"Successfully connected to the database: {redacted_url}")

            return engine
        except SQLAlchemyError as e:
            logger.info(f"Failed to create engine for: {redacted_url}")
            logger.info(f"Error details: {e}")
            raise e
        except Exception as e:
            # Handle general exceptions
            logger.info(f"An unexpected error occurred: {e}")
            raise e