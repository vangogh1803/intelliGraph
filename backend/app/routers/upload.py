from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.chunker import extract_text, chunk_text
from app.services.embedder import embed_batch
from app.database.postgres import (
    insert_document,
    insert_chunk,
    update_document_chunk_count,
    get_all_documents
)
import time

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF or TXT document.
    Pipeline:
    1. Read file bytes
    2. Extract text
    3. Chunk text
    4. Embed all chunks in batch
    5. Store document + chunks in PostgreSQL
    """
    start_time = time.time()

    # Validate file type
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported"
        )

    # Read file
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Extract text
    try:
        text = extract_text(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Text extraction failed: {str(e)}"
        )

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from file"
        )

    # Store document
    doc_id = insert_document(file.filename, text)

    # Chunk text
    chunks = chunk_text(text, chunk_size=400, overlap=50)

    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks created")

    # Embed all chunks in one batch (faster)
    chunk_texts = [c["content"] for c in chunks]
    embeddings = embed_batch(chunk_texts)

    # Store each chunk with its embedding
    for chunk, embedding in zip(chunks, embeddings):
        insert_chunk(
            chunk_id=chunk["id"],
            document_id=doc_id,
            content=chunk["content"],
            chunk_index=chunk["index"],
            embedding=embedding
        )

    # Update document with chunk count
    update_document_chunk_count(doc_id, len(chunks))

    elapsed = round((time.time() - start_time) * 1000, 2)

    return {
        "message": "Document uploaded successfully",
        "document_id": doc_id,
        "filename": file.filename,
        "chunks_created": len(chunks),
        "processing_time_ms": elapsed
    }


@router.get("/documents")
async def list_documents():
    """Return all uploaded documents"""
    docs = get_all_documents()
    return {"documents": [dict(d) for d in docs]}