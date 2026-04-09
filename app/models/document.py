import enum
from datetime import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base



class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class Document(Base):
    """
    -id
    -user_id
    -filename
    -status
    -created_at
    """
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(255),default='pending')
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates='documents')
    chunks: Mapped[list["Chunk"]] = relationship(back_populates='document', cascade='all, delete-orphan')


    def __repr__(self) -> str:
        return f"<Document id={self.id} user_id={self.user_id} filename={self.filename}, type={self.status}>"
