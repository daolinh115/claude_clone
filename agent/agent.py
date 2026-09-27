from typing import AsyncGenerator

from agent.events import AgentEventType


class Agent:
    def __init__(self):
        pass

    async def _agentic_loop(self) -> AsyncGenerator[AgentEventType, None]:
        pass
