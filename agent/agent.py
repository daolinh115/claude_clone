from typing import AsyncGenerator

from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.response import StreamEventType


class Agent:
    def __init__(self):
        self.client = LLMClient()

    async def run(self, message: str):
        yield AgentEvent.agent_start(message)
        # add a user message to context
        async for event in self._agentic_loop():
            yield event

    async def _agentic_loop(self) -> AsyncGenerator[AgentEventType, None]:
        message = [{"role": "user", "content": "hey, what is going on"}]
        async for event in self.client.chat_completion(message, True):
            if event.type == StreamEventType.TEXT_DELTA:
                content = event.text_delta.content
                yield AgentEvent.text_delta(content=content)
            elif event.type == StreamEventType.ERROR:
                yield AgentEvent.agent_error(event.error or "Unknown error occured")
