SUMMARIZE_DOCUMENT_CHUNKS = """
The user has given a query: {query}
You have searched the internal knowledge repository and found some documents that may relate to users query.
Use these documents to answer users query the best you can.
The relevant documents are provided as a python dictionary. 
The key will contain the name and the location of the complete file.
The value will contain the excerpts containing the relevant chunk of text to the users query.

Documents:
{documents}
"""