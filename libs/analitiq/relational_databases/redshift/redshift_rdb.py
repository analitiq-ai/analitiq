from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from analitiq.base.base_relational_database import BaseRelationalDatabase


class RedshiftDatabaseWrapper(BaseRelationalDatabase):
    """Database wrapper for Amazon Redshift databases."""

    def create_engine(self):
        url = URL.create(
            drivername="redshift+redshift_connector",
            host=self.params["host"],
            port=self.params.get("port", 5439),
            database=self.params["db_name"],
            username=self.params["username"],
            password=self.params["password"],
        )
        engine = create_engine(url, connect_args={"sslmode": "allow"})
        return engine
