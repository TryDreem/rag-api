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
    async def get_last_messages(self, document_id: int, db: AsyncSession, limit: int = 6) -> list[dict]:
        logger.info(f"getting last messages: {document_id}...")

        messages = await self._get_messages(db=db, document_id=document_id, limit=limit)

        logger.info(f"Got {len(messages)} messages")

        return [{"role": msg.role, "content": msg.content} for msg in messages]


    async def ask_question(self, document_id: int, question: str, current_user: User, db: AsyncSession) -> str:
        logger.info(f"asking question: {question[:50]}...")
        document = await db.get(Document, document_id)
        if not document:
            raise DocumentNotFound("Document not found")
        if document.user_id != current_user.id:
            raise AccessDenied("User not allowed to use this document")

        try:

            messages = await self.get_last_messages(document_id=document_id, db=db)

            if messages:
                rephrased_question = await self._rephrase_question(question=question, messages=messages)
            else:
                rephrased_question = question

            chunks = await find_similar_chunks(text=rephrased_question, document_id=document_id, db=db, limit=5)
            context = "\n\n".join([chunk.content for chunk in chunks])

            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer questions based only on the provided context. If the answer is not in the context, say so."
                    },
                    *messages,
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


    async def get_history(self, document_id: int, current_user: User, db: AsyncSession, limit: int = 5) -> list[Message]:
        logger.info(f"getting history: {document_id}...")
        document = await db.get(Document, document_id)

        if not document:
            raise DocumentNotFound("Document not found")

        if document.user_id != current_user.id:
            raise AccessDenied("User not allowed to use this document")

        messages = await self._get_messages(document_id=document_id, db=db, limit=limit)

        logger.info(f"Got {len(messages)} messages")

        return messages


    async def _get_messages(self, document_id: int, db: AsyncSession, limit: int = 6) -> list[Message]:
        query = select(Message).where(Message.document_id == document_id).order_by(Message.created_at.desc()).limit(limit)
        result = await db.execute(query)
        messages = result.scalars().all()
        messages = list(reversed(messages))

        return messages


    async def _rephrase_question(self,question: str, messages: list[dict]) -> str:
        logger.info(f"rephrasing question: {question}...")

        try:

            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a question rephraser. Your only job is to rephrase follow-up questions into standalone questions.

                        Example:
                        History: user asked "Who is Lena?" and got answer "Lena is a commander in the Republic army"
                        Follow-up: "Where did she have vacation?"
                        Output: "Where did Lena have her vacation?"
                        
                        Rules:
                        - Return ONLY the rephrased question
                        - Do NOT answer the question
                        - Do NOT explain anything
                        - Do NOT add any extra text
                        - Just one sentence ending with ?"""
                    },
                    *messages,
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )

            answer = response.choices[0].message.content

            logger.info(f"Rephrased question:\n {answer}")

            return answer

        except Exception as e:
            raise SomethingWentWrong(f"Failed to rephrase question using LLM: {e}")











service = ChatService()