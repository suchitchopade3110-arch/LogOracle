import asyncio
from llm.groq_client import groq_complete

async def test():
    result = await groq_complete(
        messages=[{"role": "user", "content": "Say: GROQ is working"}],
        max_tokens=20,
    )
    print(result)

asyncio.run(test())
