from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base



class Chunk(Base):
    """
    -id
    -document_id
    -content
    -chunk-index
    -embedding - Vector(384)
    """

    __tablename__ = "chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list] = mapped_column(Vector(384))

    document: Mapped["Document"] = relationship(back_populates="chunks")


