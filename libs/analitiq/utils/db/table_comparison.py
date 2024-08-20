def compare_columns_between_tables(table_data, detailed: bool = False):
    """
    Compares the columns of tables from two different databases and provides detailed numeric column comparisons if requested.

    Args:
        table_data (dict): A dictionary where keys are database names, and values are tuples containing 
                           (db_wrapper, schema_name, table_name). The function expects exactly two items in the dictionary.
        detailed (bool): If True, the function will also compare numeric column statistics (min, max, avg) between the tables.

    Raises:
        ValueError: If the number of databases provided in `table_data` is not exactly two.

    Prints:
        - Summary of columns that are only present in one of the databases.
        - List of common columns between the databases.
        - Discrepancies in numeric column statistics if `detailed` is set to True.
    """

    # Ensure the comparison is between exactly two tables
    if len(table_data) != 2:
        raise ValueError("Comparison should be between tables in exactly 2 databases.")

    # Dictionary to store metadata (columns, numeric stats) for each database
    metadata = {}

    # Iterate over the provided database information
    for db_name, (db_wrapper, schema_name, table_name) in table_data.items():
        try:
            # Fetch column data for the table
            column_data = db_wrapper.get_table_columns(table_name, schema_name)
            # Store column names and their types in a dictionary
            column_details = {col['name']: col['type'] for col in column_data}

            # Store the set of column names for later comparison
            metadata[db_name] = {'cols': set(column_details.keys())}
        except Exception as e:
            print(f"Error fetching metadata for {db_name}: {e}")
            metadata[db_name] = None

        # If detailed comparison is requested, fetch numeric column statistics
        if detailed:
            # Fetch numeric columns from the column data
            numeric_columns = db_wrapper.get_numeric_columns(column_data)
            num_col_stats = {}
            for column_name in numeric_columns:
                # Store summary statistics (min, max, avg) for each numeric column
                num_col_stats[column_name] = db_wrapper.get_summary_statistics(schema_name, table_name, column_name)

            # Add numeric column statistics to the metadata for the current database
            metadata[db_name]['num_col_stats'] = num_col_stats

    # Retrieve the names of the two databases for comparison
    db1, db2 = list(metadata.keys())

    # Count the number of columns in each database
    metadata[db1]['count'] = len(metadata[db1]['cols'])
    metadata[db2]['count'] = len(metadata[db2]['cols'])

    # Identify columns that are only present in one of the databases
    metadata[db1]['columns_only'] = metadata[db1]['cols'] - metadata[db2]['cols']
    metadata[db2]['columns_only'] = metadata[db2]['cols'] - metadata[db1]['cols']
    # Identify common columns between the two databases
    common_columns = metadata[db1]['cols'].intersection(metadata[db2]['cols'])

    # Check if the tables have the same number of columns and identical column names
    if (len(metadata[db1]['columns_only']) == 0 and
            len(metadata[db2]['columns_only']) == 0 and
            metadata[db1]['count'] == metadata[db2]['count'] == len(common_columns)):
        print("\n**Tables have identical number of columns.**")
    else:
        # Print a summary of column differences for each database
        for name_, values in metadata.items():
            print(f"\n=== Summary for {name_} ===")
            print(f"- Total Columns: {values['count']}")
            if values['columns_only']:
                print(f"- Unique Columns: {', '.join(values['columns_only'])}")
            else:
                print(f"- No unique columns")

        print(f"\nCommon Columns: {len(common_columns)}\n")

    # If detailed comparison is requested, compare numeric column statistics
    num_col_discrepancies = []

    for column in common_columns:
        if (column in metadata[db1]['num_col_stats'] and
                column in metadata[db2]['num_col_stats']):

            # Extract min, max, avg statistics for the common column from both databases
            min_1, max_1, avg_1 = metadata[db1]['num_col_stats'][column]
            min_2, max_2, avg_2 = metadata[db2]['num_col_stats'][column]

            # Compare the statistics between the two databases
            if min_1 != min_2 or max_1 != max_2 or avg_1 != avg_2:
                num_col_discrepancies.append({
                    'column': column,
                    f'{db1}_stats': (min_1, max_1, avg_1),
                    f'{db2}_stats': (min_2, max_2, avg_2)
                })

    # Print any discrepancies found in numeric column statistics
    if num_col_discrepancies:
        print("\n**Discrepancies Found in Numeric Columns:**\n")
        for discrepancy in num_col_discrepancies:
            column = discrepancy['column']
            db1_stats = discrepancy[f'{db1}_stats']
            db2_stats = discrepancy[f'{db2}_stats']
            print(f"Column: '{column}'")
            print(f"  {db1} - Min: {db1_stats[0]:,.2f}, Max: {db1_stats[1]:,.2f}, Avg: {db1_stats[2]:,.10f}")
            print(f"  {db2} - Min: {db2_stats[0]:,.2f}, Max: {db2_stats[1]:,.2f}, Avg: {db2_stats[2]:,.10f}\n")
    else:
        print("**All numeric columns match between the two tables.**")
