import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.file_walker import (
    extract_zip,
    clone_github_repo,
    walk_directory,
    cleanup_temp
)
from app.services.chunker import chunk_text
from app.services.embedder import embed_batch
from app.database.postgres import (
    insert_project,
    update_project_status,
    insert_file,
    insert_chunk,
    get_all_projects,
    get_project_by_id,
    get_files_by_project
)

router = APIRouter()


class GithubRequest(BaseModel):
    url: str
    name: str = None


async def process_project_files(
    project_id: int,
    files: list[dict]
):
    """
    Core pipeline:
    For each file:
      1. Store file in PostgreSQL
      2. Chunk the content
      3. Embed all chunks
      4. Store chunks with embeddings
    """
    total_chunks = 0

    for i, file_data in enumerate(files):
        print(
            f"Processing file {i+1}/{len(files)}: "
            f"{file_data['relative_path']}"
        )

        # Store file
        file_id = insert_file(
            project_id=project_id,
            filename=file_data["filename"],
            relative_path=file_data["relative_path"],
            extension=file_data["extension"],
            content=file_data["content"]
        )

        # Chunk
        chunks = chunk_text(
            file_data["content"],
            chunk_size=300,
            overlap=30
        )

        if not chunks:
            continue

        # Embed batch
        chunk_texts = [c["content"] for c in chunks]
        try:
            embeddings = embed_batch(chunk_texts)
        except Exception as e:
            print(f"Embedding failed for {file_data['filename']}: {e}")
            continue

        # Store chunks
        for chunk, embedding in zip(chunks, embeddings):
            insert_chunk(
                chunk_id=chunk["id"],
                file_id=file_id,
                project_id=project_id,
                content=chunk["content"],
                chunk_index=chunk["index"],
                embedding=embedding
            )
            total_chunks += 1

    return total_chunks


@router.post("/projects/upload-zip")
async def upload_zip(file: UploadFile = File(...)):
    """
    Upload a ZIP file of a project.
    Extracts, walks, chunks, embeds all files.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only ZIP files are supported"
        )

    zip_bytes = await file.read()
    if not zip_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Get project name from zip filename
    project_name = file.filename.replace(".zip", "")

    # Create project record
    project_id = insert_project(
        name=project_name,
        source="zip"
    )

    temp_dir = None
    try:
        # Extract ZIP
        temp_dir, project_root = extract_zip(zip_bytes)

        # Walk files
        files = walk_directory(project_root)

        if not files:
            update_project_status(project_id, "failed")
            raise HTTPException(
                status_code=400,
                detail="No supported files found in ZIP"
            )

        # Process files
        total_chunks = await process_project_files(project_id, files)

        # Update project status
        update_project_status(
            project_id,
            status="ready",
            file_count=len(files),
            chunk_count=total_chunks
        )

        return {
            "message": "Project uploaded successfully",
            "project_id": project_id,
            "project_name": project_name,
            "files_processed": len(files),
            "chunks_created": total_chunks
        }

    except HTTPException:
        raise
    except Exception as e:
        update_project_status(project_id, "failed")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        if temp_dir:
            cleanup_temp(temp_dir)


@router.post("/projects/import-github")
async def import_github(request: GithubRequest):
    """
    Clone a GitHub repo and process it.
    """
    url = request.url.strip()

    if not url.startswith("https://github.com"):
        raise HTTPException(
            status_code=400,
            detail="Only public GitHub URLs are supported"
        )

    # Derive project name from URL
    project_name = request.name or url.rstrip("/").split("/")[-1]

    # Create project record
    project_id = insert_project(
        name=project_name,
        source="github",
        source_url=url
    )

    temp_dir = None
    try:
        # Clone repo
        temp_dir, project_root = clone_github_repo(url)

        # Walk files
        files = walk_directory(project_root)

        if not files:
            update_project_status(project_id, "failed")
            raise HTTPException(
                status_code=400,
                detail="No supported files found in repository"
            )

        # Process files
        total_chunks = await process_project_files(project_id, files)

        # Update project status
        update_project_status(
            project_id,
            status="ready",
            file_count=len(files),
            chunk_count=total_chunks
        )

        return {
            "message": "Repository imported successfully",
            "project_id": project_id,
            "project_name": project_name,
            "source_url": url,
            "files_processed": len(files),
            "chunks_created": total_chunks
        }

    except HTTPException:
        raise
    except Exception as e:
        update_project_status(project_id, "failed")
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )
    finally:
        if temp_dir:
            cleanup_temp(temp_dir)


@router.get("/projects")
async def list_projects():
    """List all projects"""
    projects = get_all_projects()
    return {"projects": [dict(p) for p in projects]}


@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """Get a single project with its files"""
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files = get_files_by_project(project_id)
    return {
        "project": dict(project),
        "files": [dict(f) for f in files]
    }


@router.get("/projects/{project_id}/files")
async def get_project_files(project_id: int):
    """Get all files for a project"""
    files = get_files_by_project(project_id)
    return {"files": [dict(f) for f in files]}