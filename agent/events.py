from enum import Enum
from dataclasses import dataclass


class AgentEventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"


@dataclass
class AgentEvent:
    type: AgentEventType
