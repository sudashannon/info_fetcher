from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.db.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, comment="标题")
    url = Column(String, unique=True, index=True, comment="链接")
    source = Column(String, index=True, comment="来源")
    hot_score = Column(Float, default=0.0, comment="热度指数")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Item(title={self.title}, source={self.source})>"
