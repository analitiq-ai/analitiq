# About Analitiq
Analitiq is a Framework for managin your data using LLMs. Analitiq can be extended with your own services written in python. 
These custom services can address your unique tasks for managing your data, and they can function as part of the overall analytical engine of Analitiq.

![image](assets/images/Analitiq_Diagram.png)

Analitiq currently supports the following LLM models
- ChatGPT
- Mistral
- Bedrock (AWS)

Analitiq currently integrates with the following vectorDBs
- Weaviate
- ChromaDB

## What Analitiq needs to work
Since Analitiq is a framework to help data people manage data using LLMs, it requires at the least:
1. Access to LLM
2. Access to Database

As an extra bonus and to make things even smarter, it could also use:
3. Access to Vector Database with documentation.


## UI
The app interface can be extended with a UI, such as streamlit app.
![image](assets/images/query.png)