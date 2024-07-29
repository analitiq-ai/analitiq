# Adding Access to Your Data Warehouse in Analitiq

Follow these steps to add access to your Data Warehouse in Analitiq. This will enable Analitiq to access and analyze your data efficiently.

## Step-by-Step Guide

1. **Navigate to Data Connections**

   Once you are logged in to the Analitiq Web UI, navigate to the **Database Connections** section.

   ![db_connections.png](..%2F..%2Fassets%2Fimages%2Fcloud%2Fdb_connections.png)

2. **Add a New Connection**

   Click on the **Add Database** button to start adding a new connection:

   ![add_db.png](..%2F..%2Fassets%2Fimages%2Fcloud%2Fadd_db.png)

3. **Fill in the Connection Details**

   Provide the necessary details for your Data Warehouse connection:

   - **Connection name**: A name for your connection.
   - **Database**: Select your database type from the dropdown menu.
   - **Host**: The hostname or IP address of your database server.
   - **Port**: The port number on which your database server is running.
   - **Database name**: The name of your database.
   - **Username**: Your database username.
   - **Password**: Your database password.
   - **Schema**: The schema you want to connect to (default is 'public').

4. **Test the Connection**

   After filling in all the required details, click on the **Test** button to ensure that the connection to your Data Warehouse is working correctly.

5. **Save the Connection**

   If the connection test is successful, click **Save** to store your credentials and complete the setup.

## Important Notes

- Ensure that you connect only the schema containing the final fact and dimension tables ready for data analysis. This ensures that Analitiq focuses on using ready-made tables and does not inadvertently scan tables not intended for consumption.

- If you encounter any issues during the connection process, please check your connection details or consult your database administrator.

For further assistance, visit our [Support Page](https://analitiq-app.com/support) or contact us at support@analitiq-app.com.

We are here to help you make the most of your data with Analitiq!

---

Thank you for choosing Analitiq!

**The Analitiq Team**
