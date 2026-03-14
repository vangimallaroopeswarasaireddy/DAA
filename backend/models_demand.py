from sqlalchemy import Column, ForeignKey, Integer, String
from backend.db import Base


class Demand(Base):
    __tablename__ = "demands"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source = Column(Integer, nullable=False)
    destination = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    priority = Column(String(50), nullable=False, default="medium")