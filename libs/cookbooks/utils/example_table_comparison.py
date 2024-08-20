
"""
This script is a comprehensive example of how to use the `compare_columns_between_tables` method from the `analitiq` library
to compare the structure and content of tables between two different databases (production and development).

The script demonstrates:
1. Loading environment variables for secure database connection configuration.
2. Defining and managing connection parameters for both production and development databases.
3. Comparing column structures between the specified tables in both databases.
4. Performing detailed numeric comparisons of common columns, if requested.
5. Retrieving and comparing row counts for additional data consistency verification.

This script is particularly useful for data analysts who need to ensure data consistency and integrity across different environments.
"""


import os
import sys
from analitiq.utils.db.table_comparison import compare_columns_between_tables
from analitiq.base.Database import DatabaseWrapper
from dotenv import load_dotenv

# List of environment variables required for database connections and configurations
ENV_VARIABLES = ["WEAVIATE_COLLECTION", "WEAVIATE_URL", "WEAVIATE_CLIENT_SECRET", "LLM_MODEL_NAME",
                 "CREDENTIALS_PROFILE_NAME", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "REGION_NAME",
                 "DB_NAME", "DB_TYPE", "DB_HOST", "DB_USERNAME", "DB_PASSWORD", "DB_PORT", "DB_DB_NAME",
                 "DB_SCHEMAS", "DB_THREADS", "DB_KEEPALIVES_IDLE", "DB_CONNECT_TIMEOUT"]

def add_to_sys_path():
    """
    Adds the dynamic path of the 'analitiq' library to the system path.
    This allows Python to locate and import modules from this custom library.

    This is particularly useful when working in a development environment
    where your project structure is not yet finalized, or the library is not installed globally.
    """
    home_directory = os.environ.get("HOME")
    dynamic_path = f"{home_directory}/Documents/Projects/analitiq/libs/"
    sys.path.insert(0, dynamic_path)

def load_env_variables():
    """
    Loads environment variables from a .env file using python-dotenv.

    This method retrieves the necessary environment variables defined in ENV_VARIABLES.
    This is crucial for securely handling sensitive information like database credentials.

    Returns:
        dict: A dictionary containing the values of the required environment variables.
    """
    load_dotenv()
    return {variable_name: os.getenv(variable_name) for variable_name in ENV_VARIABLES}

def define_db_params(env_vars):
    """
    Defines and returns the database connection parameters for the production database.

    Args:
        env_vars (dict): Dictionary of environment variables.

    Returns:
        dict: A dictionary with all the necessary parameters for connecting to the production database.
    """
    return {
        "name": 'prod',
        "type": 'postgres',
        "host": 'mb-dwh.cycx0gj6menw.eu-west-1.rds.amazonaws.com',
        "username": 'master',
        "password": 'qs%W$I?}]Zo6J:aJ(|rQ)!o~YfrO',
        "port": 5432,
        "db_name": 'dwh',
        "db_schemas": 'analytic_stage',
        "threads": int(env_vars.get("DB_THREADS")),
        "keepalives_idle": int(env_vars.get("DB_KEEPALIVES_IDLE")),
        "connect_timeout": int(env_vars.get("DB_CONNECT_TIMEOUT"))
    }

def define_db_params2(env_vars):
    """
    Defines and returns the database connection parameters for the development database.

    Args:
        env_vars (dict): Dictionary of environment variables.

    Returns:
        dict: A dictionary with all the necessary parameters for connecting to the development database.
    """
    return {
        "name": 'dev',
        "type": 'postgres',
        "host": 'mb-dwh-dev.cycx0gj6menw.eu-west-1.rds.amazonaws.com',
        "username": 'postgres',
        "password": '{#!goQP6>9>.g-t{bZ$MPGh}dcF7',
        "port": 5432,
        "db_name": 'dwh',
        "db_schemas": 'analytic_stage',
        "threads": int(env_vars.get("DB_THREADS")),
        "keepalives_idle": int(env_vars.get("DB_KEEPALIVES_IDLE")),
        "connect_timeout": int(env_vars.get("DB_CONNECT_TIMEOUT"))
    }

if __name__ == "__main__":
    # Add the custom library path to the system path
    add_to_sys_path()

    # Load environment variables necessary for the script
    env_vars = load_env_variables()

    # Define database parameters for both production and development databases
    db_params = define_db_params(env_vars)
    db_params2 = define_db_params2(env_vars)

    # Instantiate DatabaseWrapper objects for both production and development databases
    db = DatabaseWrapper(db_params)
    db2 = DatabaseWrapper(db_params2)

    # Example usage:
    # Prepare the table data dictionary containing details of the tables to be compared
    # The keys are the names of the databases, and the values are tuples containing:
    # - The database wrapper instance
    # - The schema name
    # - The table name to compare
    table_data = {
        "Prod DB": (DatabaseWrapper(db_params), db_params['db_schemas'], "journeys"),
        "Dev DB": (DatabaseWrapper(db_params2), db_params2['db_schemas'], "journeys")
    }

    # Compare the columns between the production and development databases
    # This will print out a summary of column differences and, if `detailed=True`, numeric discrepancies
    compare_columns_between_tables(table_data, detailed=True)

    # Additional analysis: Getting the row count for the same table in both databases
    for db_name, (DbWrapper, params, table_name) in table_data.items():
        # Fetch and print the row count for each database's "journeys" table
        row_count = DbWrapper.get_row_count(params, table_name)
        print(f"Row count for {db_name}: {row_count}")

    # The above row count analysis is useful for data analysts to verify data consistency
    # beyond just column structures and numeric discrepancies.
