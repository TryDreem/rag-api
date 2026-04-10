from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.models.chunk import Chunk
from app.core.embeddings import get_embedding
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def find_similar_chunks(text: str, document_id: int, db: AsyncSession, limit: int=5):
    logger.info(f"Finding similar chunks for {text}")
    question_embedding = get_embedding(text)

    query = (
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.embedding.op("<->")(question_embedding))
        .limit(limit)
    )

    result = await db.execute(query)
    chunks = result.scalars().all()

    logger.info(f"Found {len(chunks)} similar chunks for {text}")
    return chunks

