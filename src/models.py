from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, Boolean


class Base(DeclarativeBase):
    pass


class MiniApp(Base):
    __tablename__ = "mini_apps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    category = Column(String)
    tags = Column(String)
    deployment_id = Column(String)
    icon_url = Column(String, nullable=True)
    version = Column(String)
    rating = Column(Float)
    downloads = Column(Integer)
    is_featured = Column(Boolean)
