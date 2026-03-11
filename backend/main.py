from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import models, schemas, crud, parsers
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Saliency Summariser API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Summarise plain text ──────────────────────────────────────────────────────

@app.post("/summarise", response_model=schemas.SummariseResponse)
def summarise_text(req: schemas.SummariseRequest, db: Session = Depends(get_db)):
    if len(req.text.strip()) < 50:
        raise HTTPException(400, "Text too short — provide at least 50 characters.")
    return crud.create_summary(db, req.text, req.title, req.source_type, req.source_url)


# ── Summarise uploaded file (PDF or DOCX) ────────────────────────────────────

@app.post("/summarise/file", response_model=schemas.SummariseResponse)
async def summarise_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    filename = file.filename or ""

    if filename.lower().endswith(".pdf"):
        text = parsers.parse_pdf(content)
        source_type = "pdf"
    elif filename.lower().endswith(".docx"):
        text = parsers.parse_docx(content)
        source_type = "docx"
    else:
        raise HTTPException(400, "Only PDF and DOCX files are supported.")

    if len(text.strip()) < 50:
        raise HTTPException(400, "Could not extract enough text from the file.")

    return crud.create_summary(db, text, filename, source_type)


# ── Summarise URL ─────────────────────────────────────────────────────────────

@app.post("/summarise/url", response_model=schemas.SummariseResponse)
def summarise_url(payload: dict, db: Session = Depends(get_db)):
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(400, "URL is required.")
    try:
        title, text = parsers.parse_url(url)
    except Exception as e:
        raise HTTPException(400, f"Could not fetch URL: {e}")
    if len(text.strip()) < 50:
        raise HTTPException(400, "Not enough text found at that URL.")
    return crud.create_summary(db, text, title, "url", url)


# ── History ───────────────────────────────────────────────────────────────────

@app.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.list_documents(db, skip, limit)


@app.get("/documents/{doc_id}", response_model=schemas.SummariseResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = crud.get_document(db, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    return doc


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    if not crud.delete_document(db, doc_id):
        raise HTTPException(404, "Document not found.")
    return {"ok": True}


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)
