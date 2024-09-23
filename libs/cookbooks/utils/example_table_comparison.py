
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
from dotenv import load_dotenv
from analitiq.utils.db.table_comparison import compare_columns_between_tables
from analitiq.factories.relational_database_factory import RelationalDatabaseFactory

# Define the environment
env = 'dev'  # This could be determined in multiple ways, e.g., command-line arguments, another environment variable, etc.

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

def load_env_variables(env: str = 'dev'):
    """
    Loads environment variables from a .env file using python-dotenv.

    This method retrieves the necessary environment variables defined in ENV_VARIABLES.
    This is crucial for securely handling sensitive information like database credentials.

    Returns:
        dict: A dictionary containing the values of the required environment variables.
    """

    # Load the appropriate .env file
    try:
        dotenv_path = f'/Users/kirillandriychuk/Documents/Projects/analitiq/.env.mb.{env}'
    except Exception as e:
        print(e)

    load_dotenv(dotenv_path=dotenv_path)

    return {
        "name": os.getenv("DB_NAME"),
        "type": os.getenv("DB_TYPE"),
        "host": os.getenv("DB_HOST"),
        "username": os.getenv("DB_USERNAME"),
        "password": os.getenv("DB_PASSWORD"),
        "port": os.getenv("DB_PORT"),
        "db_name": os.getenv("DB_DB_NAME"),
        "db_schemas": os.getenv("DB_SCHEMAS"),
        "threads": int(os.getenv("DB_THREADS")),
        "keepalives_idle": int(os.getenv("DB_KEEPALIVES_IDLE")),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT"))
    }



if __name__ == "__main__":
    # Add the custom library path to the system path
    add_to_sys_path()

    # Define database parameters for both production and development databases
    db_params_1 = load_env_variables('prod')
    db_params_2 = load_env_variables('prod')

    # Instantiate RelationalDatabaseFactory objects for both production and development databases
    db_1 = RelationalDatabaseFactory.create_database(db_params_1)
    db_2 = RelationalDatabaseFactory.create_database(db_params_2)

    # Example usage:
    # Prepare the table data dictionary containing details of the tables to be compared
    # The keys are the names of the databases, and the values are tuples containing:
    # - The database wrapper instance
    # - The schema name
    # - The table name to compare
    table_data = {
        "DB1": (db_1, db_params_1['db_schemas'], "model_final_output"),
        "DB2": (db_2, db_params_2['db_schemas'], "model_final_output_v2")
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
