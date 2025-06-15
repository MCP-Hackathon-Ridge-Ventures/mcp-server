from sqlalchemy.orm import DeclarativeBase
from enrichmcp.sqlalchemy import EnrichSQLAlchemyMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Boolean


class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass


class MiniApp(Base):
    __tablename__ = "mini_apps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    tags: Mapped[str] = mapped_column(String)
    deployment_id: Mapped[str] = mapped_column(String)
    icon_url: Mapped[str | None] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String)
    rating: Mapped[float] = mapped_column(Float)
    downloads: Mapped[int] = mapped_column(Integer)
    is_featured: Mapped[bool] = mapped_column(Boolean)
