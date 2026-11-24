from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Any


from client.response import TokenUsage
from tools.base import ToolResult


class AgentStreamEventType(str, Enum):
    # Agent lifecycle
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"

    # Text streaming
    TEXT_DELTA = "text_delta"
    TEXT_COMPLETE = "text_complete"

    # Tool
    TOOL_CALL_START = "Tool call start"
    TOOL_CALL_COMPLETE = "Tool call complete"


@dataclass
class AgentEvent:
    type: AgentStreamEventType
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def agent_start(cls, message: str) -> AgentEvent:
        return cls(type=AgentStreamEventType.AGENT_START, data={"message": message})

    @classmethod
    def agent_end(
        cls, response: str | None = None, usage: TokenUsage | None = None
    ) -> AgentEvent:
        return cls(
            type=AgentStreamEventType.AGENT_END,
            data={"response": response, "usage": usage.__dict__ if usage else None},
        )

    @classmethod
    def agent_error(
        cls, error: str, details: dict[str, Any] | None = None
    ) -> AgentEvent:
        return cls(
            type=AgentStreamEventType.AGENT_ERROR,
            data={"error": error, "details": details or {}},
        )

    @classmethod
    def text_delta(cls, content: str) -> AgentEvent:
        return cls(type=AgentStreamEventType.TEXT_DELTA, data={"content": content})

    @classmethod
    def text_complete(cls, content: str) -> AgentEvent:
        return cls(type=AgentStreamEventType.TEXT_COMPLETE, data={"content": content})

    @classmethod
    def tool_call_start(cls, call_id: str, name: str, arguments: dict[str, Any]):
        return cls(type=AgentStreamEventType.TOOL_CALL_START, data={'call_id': call_id, 'name': name, 'arguments': arguments})

    @classmethod
    def tool_call_complete(cls, call_id: str, name: str, result: ToolResult):
        return cls(type=AgentStreamEventType.TOOL_CALL_START, 
                   data={
                       'call_id': call_id,
                        'name': name,
                        'success': result.success,
                        'output': result.output,
                        'error': result.error,
                        'metadata': result.metadata,
                        'truncated': result.truncated
                        })
