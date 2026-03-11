from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SentenceScore(BaseModel):
    index: int
    text: str
    score: float          # 0.0 – 1.0 normalised attention


class SummariseRequest(BaseModel):
    text: str
    title: Optional[str] = None
    source_type: str = "text"
    source_url: Optional[str] = None


class SummariseResponse(BaseModel):
    id: int
    title: Optional[str]
    summary: str
    sentences: List[SentenceScore]
    word_count: int
    model_used: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    title: Optional[str]
    source_type: str
    summary: Optional[str]
    word_count: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
