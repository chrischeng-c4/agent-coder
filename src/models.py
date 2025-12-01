from enum import Enum
from pydantic import BaseModel, Field

class AgentMode(str, Enum):
    AUTO = 'auto'
    PLAN = 'plan'
    ASK = 'ask'


