SAVE_ELEMENT_PROMPT = """
The user has sent you the following request {user_prompt}.
This is likely in reference to your chat history with the user.
Bellow is the chat history provided as list of JSON objects.
Here is a description of each object:

timestamp: time when the message was sent
entity: who sent the message. It can be you (Analitiq) or the user (Human).
content: the actual message that was sent
metadata: the contextual information about the message.

Looking at the chat history, use your best judgement to determine what chat message the user is referring to and provide it in your response.

response format instructions:
{format_instructions}

chat history:
{chat_history}
"""
