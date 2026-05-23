from fastapi import APIRouter
import httpx
from app.database.postgres import get_connection
from app.database.neo4j import neo4j_client
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    status = {
        "app": "ok",
        "postgres": "unknown",
        "neo4j": "unknown",
        "ollama": "unknown"
    }

    # Check PostgreSQL
    try:
        conn = get_connection()
        conn.close()
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {str(e)}"

    # Check Neo4j
    try:
        neo4j_client.verify_connection()
        status["neo4j"] = "ok"
    except Exception as e:
        status["neo4j"] = f"error: {str(e)}"

    # Check Ollama
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=5.0
            )
            if response.status_code == 200:
                status["ollama"] = "ok"
    except Exception as e:
        status["ollama"] = f"error: {str(e)}"

    return status