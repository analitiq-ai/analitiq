

# How to run
```python
"""
import asyncio

async def main():
    user_prompt = "What is our commission per venue?"
    # Sample data
    sample_data = {
        'VenueID': [101, 102, 103],
        'VenueName': ['The Grand Theatre', 'The Opera House', 'The Concert Hall'],
        'TotalCommission': [5000.00, 7500.50, 3200.25]
    }

    agent = AnalyzeAgent(model_name="gpt-3.5-turbo")
    result = agent.run(user_prompt, 'pandas data frame', sample_data)
    print(result)

asyncio.run(main())
"""
```