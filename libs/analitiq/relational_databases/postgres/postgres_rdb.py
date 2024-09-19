from sqlalchemy import create_engine
from analitiq.base.base_relational_database import BaseRelationalDatabase


class PostgresDatabaseWrapper(BaseRelationalDatabase):
    """Database wrapper for PostgreSQL databases."""

    def create_engine(self):
        engine_options = {}
        if self.params.get("db_schemas"):
            schemas_str = ",".join(self.params["db_schemas"])
            engine_options["connect_args"] = {"options": f"-csearch_path={schemas_str}"}
        engine = create_engine(
            f"postgresql+psycopg2://{self.params['username']}:{self.params['password']}@"
            f"{self.params['host']}:{self.params['port']}/{self.params['db_name']}",
            **engine_options,
        )
        return engine
