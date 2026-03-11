from sqlalchemy.orm import Session
from typing import Optional
import models, schemas, summariser


def create_summary(
    db: Session,
    text: str,
    title: Optional[str] = None,
    source_type: str = "text",
    source_url: Optional[str] = None,
) -> models.Document:
    # Truncate text to 4000 chars for T5 (model has 512 token limit)
    truncated = text[:4000]

    result = summariser.summarise_and_score(truncated)

    doc = models.Document(
        title=title or f"Document ({source_type})",
        source_type=source_type,
        source_url=source_url,
        original_text=text,
        summary=result["summary"],
        sentences=result["sentences"],
        word_count=len(text.split()),
        char_count=len(text),
        model_used="facebook/bart-large-cnn",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def list_documents(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.Document).order_by(
        models.Document.created_at.desc()
    ).offset(skip).limit(limit).all()


def get_document(db: Session, doc_id: int) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == doc_id).first()


def delete_document(db: Session, doc_id: int) -> bool:
    doc = get_document(db, doc_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True


def get_stats(db: Session) -> dict:
    total = db.query(models.Document).count()
    return {"total_documents": total}
