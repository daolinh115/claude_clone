from __future__ import annotations
from pathlib import Path
from typing import AsyncGenerator
from agent.events import AgentEvent, AgentStreamEventType
from client.llm_client import LLMClient
from client.response import StreamEventType, ToolCall
from context.manager import ContextManager
from tools.registry import create_default_registry


class Agent:
    def __init__(self):
        self.client = LLMClient()
        self.context_manager = ContextManager()
        self.tool_registry = create_default_registry()

    async def run(self, message: str)->AsyncGenerator[AgentEvent, None]:
        yield AgentEvent.agent_start(message)
        # add a user message to context
        self.context_manager.add_user_message(message)
        final_response: str | None = None
        async for event in self._agentic_loop():
            yield event
            if event.type == AgentStreamEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")

        yield AgentEvent.agent_end(final_response)

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent, None]:
        response_text = ""
        tool_schema = self.tool_registry.get_schemas()
        tool_calls: list[ToolCall] = []
        async for event in self.client.chat_completion(
            self.context_manager.get_messages(),
            tools=tool_schema if tool_schema else None,
            stream=True,
        ):
            print(event)
            if event.type == StreamEventType.TEXT_DELTA:
                content = event.text_delta.content
                response_text += content
                yield AgentEvent.text_delta(content=content)
            elif event.type == StreamEventType.TOOL_CALL_COMPLETE:
                if event.tool_call:
                    tool_calls.append(event.tool_call)
            elif event.type == StreamEventType.ERROR:
                yield AgentEvent.agent_error(event.error or "Unknown error occured")
        self.context_manager.add_assistant_message(response_text or None)
        if response_text:
            yield AgentEvent.text_complete(response_text)

        for tool_call in tool_calls:
            yield AgentEvent.tool_call_start(
                call_id=tool_call.call_id,
                name=tool_call.name,
                arguments=tool_call.arguments
            )
            self.tool_registry.invoke(
                tool_call.name,
                tool_call.arguments,
                Path.cwd
            )
    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.client:
            await self.client.close()
            self.client = None
