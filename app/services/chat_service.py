from sqlalchemy.ext.asyncio import AsyncSession
import logging
from groq import AsyncGroq
from app.core.config import settings
from app.models.document import Document
from app.models.user import User
from app.core.exceptions import  DocumentNotFound, AccessDenied, SomethingWentWrong
from app.services.vector_service import find_similar_chunks
from app.models.message import Message
from sqlalchemy import select

logger = logging.getLogger(__name__)
client = AsyncGroq(api_key=settings.GROQ_API_KEY)

class ChatService:
    async def ask_question(self, document_id: int, question: str, current_user: User, db: AsyncSession):
        logger.info(f"asking question: {question[:50]}...")
        document = await db.get(Document, document_id)
        if not document:
            raise DocumentNotFound("Document not found")
        if document.user_id != current_user.id:
            raise AccessDenied("User not allowed to use this document")

        try:

            chunks = await find_similar_chunks(text=question, document_id=document_id, db=db, limit=5)
            context = "\n\n".join([chunk.content for chunk in chunks])

            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer questions based only on the provided context. If the answer is not in the context, say so."
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {question}"
                    }
                ]
            )

            answer = response.choices[0].message.content
            db.add(Message(document_id=document_id, role="user", content=question))
            db.add(Message(document_id=document_id, role="assistant", content=answer))
            await db.commit()

        except Exception as e:
            logger.error(f"Groq error: {e}",exc_info=True)
            raise SomethingWentWrong("Failed to get answer from LLM")

        return answer

    async def get_history(self, document_id: int, current_user: User, db: AsyncSession, limit: int = 5):
        logger.info(f"getting history: {document_id}...")
        document = await db.get(Document, document_id)

        if not document:
            raise DocumentNotFound("Document not found")

        if document.user_id != current_user.id:
            raise AccessDenied("User not allowed to use this document")

        query = select(Message).where(Message.document_id == document_id).limit(limit)
        result = await db.execute(query)
        messages = result.scalars().all()

        logger.info(f"Got {len(messages)} messages")

        return messages





service = ChatService()