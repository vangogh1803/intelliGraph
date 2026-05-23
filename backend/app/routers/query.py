from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.query_engine import answer_question
from app.database.postgres import (
    get_project_by_id,
    get_traces_by_project
)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    project_id: int


@router.post("/query")
async def query_project(request: QueryRequest):
    """
    Ask a question about a project.
    Uses hybrid retrieval (vector + graph).
    """
    project = get_project_by_id(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project["status"] != "ready":
        raise HTTPException(
            status_code=400,
            detail="Project is not ready yet"
        )

    result = await answer_question(
        question=request.question,
        project_id=request.project_id
    )

    return result


@router.get("/traces/{project_id}")
async def get_traces(project_id: int):
    """Get query traces for a project"""
    traces = get_traces_by_project(project_id)
    return {"traces": [dict(t) for t in traces]}