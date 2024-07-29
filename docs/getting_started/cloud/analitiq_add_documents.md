
# Adding Documents to Analitiq

In Analitiq, you can add documents to enhance the capabilities of Analitiq by providing it with relevant context and data. This guide will show you how to add documents using the Analitiq Web UI and the Analitiq Python application.

## Adding Documents via Analitiq Web UI

To upload documents one by one using the Analitiq Web UI, follow these steps:

1. **Navigate to the Documents Section**

   Once logged in to the Analitiq dashboard, navigate to the **Documents** section from the menu.

   ![db_connections.png](..%2F..%2Fassets%2Fimages%2Fcloud%2Fdb_connections.png)

2. **Upload a Document**

   Click on the **Upload Document** button and you will see a form similar to the one shown below:

   ![document_add_form.png](..%2F..%2Fassets%2Fimages%2Fcloud%2Fdocument_add_form.png)

3. **Fill in the Document Details**

   - **Content**: Paste the content of your document.
   - **Document name**: Provide a name for your document.

4. **Save the Document**

   Click **Save** to upload and store your document in Analitiq.

## Adding Multiple Documents via Analitiq Python Application

To upload multiple documents at once, you can use the Analitiq Python application. The following code snippet, available in the Analitiq Cookbooks, demonstrates how to scan a whole directory of objects and upload them to the VectorDatabase:

```python
from libs.analitiq.vectordb.weaviate import WeaviateHandler

params = {
    "collection_name": "xxx",
    "host": "xxxxx",
    "api_key": "xxxx"
}

vdb = WeaviateHandler(params)

# To load all SQL files from a directory
DIR_PATH = '/xxx/xxx/xxx/xxx/models'
vdb.load(DIR_PATH, 'sql')
```

### Steps to Use the Python Application:

1. **Install the necessary libraries**: Ensure you have the required libraries installed in your Python environment.
2. **Configure Parameters**: Replace the placeholder values in `params` with your actual collection name, host, and API key. You can obtain these from Analitiq support.
3. **Set Directory Path**: Update `DIR_PATH` with the path to the directory containing your `.sql` files.
4. **Run the Script**: Execute the script to upload all `.sql` files in the specified directory and its subdirectories to the VectorDatabase.

If you encounter any issues or need assistance, please visit our [Support Page](https://analitiq-app.com/support) or contact us at support@analitiq-app.com.

We are here to help you make the most of your data with Analitiq!

---

Thank you for choosing Analitiq!

**The Analitiq Team**
