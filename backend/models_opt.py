from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from db import Base


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    source_node = Column(String(50), nullable=False)
    sink_node = Column(String(50), nullable=False)

    total_demand = Column(Float, nullable=False)
    delivered_volume = Column(Float, nullable=False, default=0.0)
    hours = Column(Integer, nullable=False, default=24)

    total_cost = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="completed")

    nodes_json = Column(Text, nullable=False)
    edges_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HourlyFlow(Base):
    __tablename__ = "hourly_flows"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("optimization_runs.id"), nullable=False, index=True)

    hour = Column(Integer, nullable=False)
    edge_key = Column(String(120), nullable=False)

    from_node = Column(String(50), nullable=False)
    to_node = Column(String(50), nullable=False)

    flow = Column(Float, nullable=False, default=0.0)
    effective_cost = Column(Float, nullable=False, default=0.0)
    edge_cost_total = Column(Float, nullable=False, default=0.0)