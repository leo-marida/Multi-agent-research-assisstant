from pydantic import BaseModel, ConfigDict


class Subtask(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    query: str


class ResearchPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    subtasks: list[Subtask]


class ResearchRequest(BaseModel):
    topic: str


class AgentEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_type: str
    data: dict
