
from client.llm_client import LLMClient
import asyncio

async def main():
    try:
        client = LLMClient()
        message = [{"role": "user", "content": "I have a question want to ask you"}]
        async for event in client.chat_completion(message,True):
            print(event)
        print('Done')
    finally:
        await client.close()
        

asyncio.run(main())