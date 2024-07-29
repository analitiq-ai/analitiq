# Getting Started with the Cloud [beta]

### Register for Cloud Version

To begin using Analitiq, you need to register for our beta cloud version. Please follow these steps:

1. Visit [analitiq-app.com](https://analitiq-app.com).
2. Click on the **Sign Up** button.
3. Enter your desired username and password.
4. Click **Register** to create your account.

![reg.png](..%2F..%2Fassets%2Fimages%2Fcloud%2Freg.png)

### Connect Data Warehouse

Once registered, you will need to connect your Data Warehouse to Analitiq. This would let you query your data and get inisghts.

1. **Navigate to the Data Connections** section in the Analitiq dashboard.
2. **Add a Connection** by providing the necessary details of your Data Warehouse.

3. It is advisable to connect only the schema containing the final fact and dimension tables ready for data analysis. This ensures that Analitiq focuses on using ready-made tables and does not inadvertently scan tables not intended for consumption.

### Upload Documentation
Analitiq Cloud includes a vector database where you can upload documents that Large Language Models (LLMs) can reference for better understanding. By default, Analitiq is connected to a secure Weaviate cluster.
This will give Analitiq better understanding of your data. This documentation should ideally describe your tables and columns. An example of such documentation is a `dbt schema.yml` file.

1. Go to the **Documentation Upload** section in the Analitiq dashboard.
2. Click **Upload Document** and select your documentation file.

### Start Querying and Interacting with Analitiq

Once your Data Warehouse is connected and documentation is uploaded, you can start querying and interacting with Analitiq using the web interface. Our pre-defined LLM operates in read-only mode and ensures that none of your data is used for training.


![chat-web-1.png](..%2F..%2Fassets%2Fimages%2Fchat-web-1.png)


## Key Features

- **Beta Cloud Version**: Register easily and start using Analitiq's powerful data analytics capabilities.
- **Secure Data Connection**: Connect only the necessary schemas to ensure focused and efficient data analysis.
- **Vector Database**: Upload documents to enhance the LLM's understanding and reference.
- **Pre-defined LLM**: Operates in read-only mode ensuring your data remains secure and is never used for training.

If you encounter any issues or have questions, please visit our [Support Page](https://analitiq-app.com/support) or contact us at support@analitiq-app.com.

We are excited to have you on board and look forward to helping you make the most of your data with Analitiq!

---

Thank you for choosing Analitiq!

**The Analitiq Team**
