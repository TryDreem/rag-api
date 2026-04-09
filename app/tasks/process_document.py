from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.celery_app import celery_app
from app.core.config import settings
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.database import SyncSession
import logging

logger = logging.getLogger(__name__)

model = SentenceTransformer("all-MiniLM-L6-v2")

def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


@celery_app.task
def process_document(document_id: int, file_path: str):
    with SyncSession() as session:
        try:
            document = session.get(Document, document_id)
            document.status = DocumentStatus.processing
            session.commit()
            logger.info(f"Document {document_id} is currently processing")

            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text()

            chunks = split_into_chunks(text)
            #print will change to logger
            logger.info(f"Document {document_id} has {len(chunks)} chunks")


            for i, chunk in enumerate(chunks):
                embedding = model.encode(chunk).tolist()
                chunk = Chunk(
                    document_id=document_id,
                    content=chunk,
                    chunk_index=i,
                    embedding=embedding,
                )
                session.add(chunk)

            document.status = DocumentStatus.done
            session.commit()
            logger.info(f"Document {document_id} is done")

        except Exception as e:
            document.status = DocumentStatus.failed
            session.commit()
            raise e

        return {"document_id": document_id, "chunks": len(chunks)}
