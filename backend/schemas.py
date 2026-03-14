from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------- AUTH ----------------

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------- OPTIMIZATION ----------------

class EdgeInput(BaseModel):
    from_node: str
    to_node: str
    base_cost: float = Field(..., ge=0)
    capacity: float = Field(..., gt=0)

    @field_validator("from_node", "to_node")
    @classmethod
    def node_names_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Node name cannot be empty")
        return v


class OptimizeRequest(BaseModel):
    nodes: List[str]
    edges: List[EdgeInput]
    source: str
    sink: str
    total_demand: float = Field(..., gt=0)
    hours: int = Field(default=24, ge=1, le=168)

    @field_validator("nodes")
    @classmethod
    def validate_nodes(cls, v: List[str]) -> List[str]:
        cleaned = [node.strip() for node in v if node.strip()]
        if len(cleaned) < 2:
            raise ValueError("At least 2 valid nodes are required")
        return cleaned

    @field_validator("sink")
    @classmethod
    def source_sink_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Source/Sink cannot be empty")
        return v


class FlowRecord(BaseModel):
    from_node: str
    to_node: str
    flow: float
    effective_cost: float
    edge_cost_total: float


class HourSchedule(BaseModel):
    hour: int
    delivered_this_hour: float
    hour_cost: float
    flows: List[FlowRecord]


class OptimizeResponse(BaseModel):
    run_id: Optional[int] = None
    status: str
    total_cost: float
    delivered_volume: float
    total_demand: float
    unmet_demand: float
    hours: int
    schedule: List[HourSchedule]
    note: Optional[str] = None