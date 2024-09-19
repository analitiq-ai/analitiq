Usage of Relational Database Factory
Loading a Database via the Factory
You can use the create_database function from relational_database_factory.py to instantiate a database wrapper dynamically based on the db_type.

Example: PostgreSQL

```
from relational_databases.relational_database_factory import create_database

# Parameters for PostgreSQL
postgres_params = {
"type": "postgres",
"username": "your_username",
"password": "your_password",
"host": "localhost",
"port": 5432,
"db_name": "your_database",
"db_schemas": ["public"],  # Optional
}

# Create a PostgreSQL database instance using the factory

postgres_db = create_database(db_type="postgres", params=postgres_params)

# Use the database instance
schemas = postgres_db.get_schema_names()
print("PostgreSQL Schemas:", schemas)
```
Example: Amazon Redshift
```
from relational_databases.relational_database_factory import create_database

# Parameters for Redshift
redshift_params = {
"type": "redshift",
"username": "your_username",
"password": "your_password",
"host": "your_redshift_cluster_endpoint",
"port": 5439,
"db_name": "your_database",
}

# Create a Redshift database instance using the factory

redshift_db = create_database(db_type="redshift", params=redshift_params)

# Use the database instance

schemas = redshift_db.get_schema_names()
print("Redshift Schemas:", schemas)
```

Loading a Database Directly
Alternatively, you can instantiate the database wrapper classes directly without using the factory method.

Example: PostgreSQL
```
from relational_databases.postgres.postgres_rdb import PostgresDatabaseWrapper

# Parameters for PostgreSQL
postgres_params = {
"username": "your_username",
"password": "your_password",
"host": "localhost",
"port": 5432,
"db_name": "your_database",
"db_schemas": ["public"],  # Optional
}

# Create a PostgreSQL database instance directly
postgres_db = PostgresDatabaseWrapper(params=postgres_params)

# Use the database instance
schemas = postgres_db.get_schema_names()
print("PostgreSQL Schemas:", schemas)
```

Example: Amazon Redshift
```
from relational_databases.redshift.redshift_rdb import RedshiftDatabaseWrapper

# Parameters for Redshift
redshift_params = {
"username": "your_username",
"password": "your_password",
"host": "your_redshift_cluster_endpoint",
"port": 5439,
"db_name": "your_database",
}

# Create a Redshift database instance directly
redshift_db = RedshiftDatabaseWrapper(params=redshift_params)

# Use the database instance
schemas = redshift_db.get_schema_names()
print("Redshift Schemas:", schemas)
```
Extending to Other Databases
To add support for another database (e.g., MySQL), follow these steps:

Create a New Directory

```
relational_databases/
└── mysql/
├── __init__.py
└── mysql_rdb.py
```
Implement the Wrapper Class

```
# relational_databases/mysql/mysql_rdb.py

from typing import Dict
from sqlalchemy import create_engine
from relational_databases.base_database import BaseRelationalDatabase

class MysqlDatabaseWrapper(BaseRelationalDatabase):
"""Database wrapper for MySQL databases."""

    def create_engine(self):
        engine = create_engine(
            f"mysql+pymysql://{self.params['username']}:{self.params['password']}@"
            f"{self.params['host']}:{self.params['port']}/{self.params['db_name']}"
        )
        return engine
```

Update Dependencies

Install the necessary driver for MySQL:

```
pip install pymysql
```

Use the Factory to Instantiate

```

from relational_databases.relational_database_factory import create_database

# Parameters for MySQL
mysql_params = {
"type": "mysql",
"username": "your_username",
"password": "your_password",
"host": "localhost",
"port": 3306,
"db_name": "your_database",
}

# Create a MySQL database instance using the factory
mysql_db = create_database(db_type="mysql", params=mysql_params)

# Use the database instance
schemas = mysql_db.get_schema_names()
print("MySQL Schemas:", schemas)
```

Common Methods
The database wrapper classes provide several common methods inherited from `BaseRelationalDatabase`:

`get_schema_names()`: Retrieves a list of schema names in the database.

```
schemas = db_instance.get_schema_names()
```
`get_tables_in_schema(schema_name)`: Retrieves a list of table names within a specific schema.

```
tables = db_instance.get_tables_in_schema('public')
```

`get_table_columns(table_name, schema_name)`: Retrieves column metadata for a given table.

```
columns = db_instance.get_table_columns('employees', 'public')
```

`execute_sql(sql)`: Executes a SQL query and returns the result as a Pandas DataFrame.

```
success, result = db_instance.execute_sql('SELECT * FROM public.employees')
if success:
print(result)
```
`run(sql, include_columns=True)`: Executes a query using the SQLDatabase utility.

```
output = db_instance.run('SELECT COUNT(*) FROM public.employees')
print(output)
```