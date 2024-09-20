# Document Search Agent

The Document Search agent, as part of the `Analitiq` framework, provides users with the ability to upload all their documents into a search database and utilize it as a context for data analysis. This agent highlights the power of advanced search algorithms, natural language processing (NLP), and indexing to deliver efficient and context-specific search results.
## Purpose


The main purpose of the Document Search agent is to simplify and accelerate context-based data discovery and analysis for the users. With the power of full-text search, users can readily search their textual documents, find meaningful insights, and improve the effectiveness of their decision-making processes.

This agent eliminates the need for manual tracking and search through extensive amounts of documents, making it an ideal tool for knowledge workers, researchers, and anyone who needs to effectively navigate and analyze their document datasets.

## Specifications

Through the Document Search agent, users can load their documents into the search database. Post indexing of these documents, the agent allows searching within the uploaded documents seamlessly. The document search agent yields relevant search results based on context, enabling users to find appropriate content for data analytics and decision-making.

Users can interact with this agent using natural language inputs, making it accessible to users without a deep understanding of search algorithms. This process simplifies data discovery and equips the users with an intuitive interface to interact with their documents.

## How It Works

The Document Search agent operates through several key stages:

1. **User Query Processing**: The user issues a search query in natural language, which is then processed and understood by the agent.
2. **Document Repository Search**: The agent sends the refined query to the document repository where all documents are stored and indexed.
3. **Result Aggregation**: The agent receives the search results, which are then strategically aggregated. The system uses advanced techniques such as Natural Language Processing (NLP) and machine learning to perform this action.
4. **Result Ranking**: After aggregating the results, the agent ranks them based on their relevance to the user's search query. This ranking system ensures that the most relevant documents appear at the top of the results.
5. **Interpretation by the LLM (Language Learning Model)**: The LLM interprets the aggregated and ranked results. Its job is to understand the context of the documents in the search results.
6. **Summarised Information Presentation**: The LLM converts the interpreted results into a summarized form, which is then presented to the user. This summarization makes it easier for the user to get the crux of the search results quickly.

## Inputs and Outputs

### Inputs
- **User Prompt (str)**: A natural language description of the data retrieval or analysis task.

### Outputs
- **Response Object**: Contains the text summary of the documents and the interpretation by the LLM.
- 
1. response.content = pandas dataframe of the result
2. response.metadata = metadata, such as SQL that has been executed.
```python
metadata={
    "chart_type": "Pie"
}
```

## Example direct usage.
We do not recommend using this module outside of the Analitiq framework. However, if you would like to load it directly, here is how you can do it.

```python
from analitiq.vector_databases.weaviate import WeaviateHandler

params = {
    "project_name": "my_project",
    "host": "https://XXXXXXX.weaviate.network",
    "api_key": "XXXXXX"
}

vdb = WeaviateHandler(params)
```
We need 1 thing for Document Search agent to work with:

1. VectorDB (for searching documentation for better SQL results)

Trigger search with user query:
```python
search_results = vdb.kw_search("climate change", limit=5)
```

Returned Data Format:

```json
{
    "document_id_1": {
        "content": "Document content related to climate change...",
        "document_name": "Document 1",
        "source": "Source A"
    },
    "document_id_2": {
        "content": "Another document content about climate change...",
        "document_name": "Document 2",
        "source": "Source B"
    }
}
```