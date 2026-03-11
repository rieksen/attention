from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.sql import func
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300))
    source_type = Column(String(20))   # "text" | "pdf" | "docx" | "url"
    source_url = Column(String(500))
    original_text = Column(Text, nullable=False)
    summary = Column(Text)

    # Saliency: list of {sentence, score} dicts
    sentences = Column(JSON)          # [{text, score, index}, ...]

    word_count = Column(Integer)
    char_count = Column(Integer)
    model_used = Column(String(100), default="google/flan-t5-base")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
