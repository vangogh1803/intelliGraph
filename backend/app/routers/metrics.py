from fastapi import APIRouter
from app.database.postgres import get_connection

router = APIRouter()


def get_metrics(project_id: int = None) -> dict:
    """
    Compute observability metrics from query_traces.
    If project_id given → filter to that project.
    Otherwise → all projects.
    """
    conn = get_connection()
    cur = conn.cursor()

    where = "WHERE project_id = %s" if project_id else ""
    params = (project_id,) if project_id else ()

    # Total queries
    cur.execute(
        f"SELECT COUNT(*) as count FROM query_traces {where}",
        params
    )
    total_queries = cur.fetchone()["count"]

    # Avg latency
    cur.execute(
        f"""
        SELECT
            ROUND(AVG(latency_ms)::numeric, 2) as avg_latency,
            ROUND(MIN(latency_ms)::numeric, 2) as min_latency,
            ROUND(MAX(latency_ms)::numeric, 2) as max_latency
        FROM query_traces {where}
        """,
        params
    )
    latency = cur.fetchone()

    # Avg chunks retrieved
    cur.execute(
        f"""
        SELECT ROUND(AVG(chunks_retrieved)::numeric, 2) as avg_chunks
        FROM query_traces {where}
        """,
        params
    )
    avg_chunks = cur.fetchone()["avg_chunks"]

    # Avg entities matched
    cur.execute(
        f"""
        SELECT ROUND(AVG(entities_matched)::numeric, 2) as avg_entities
        FROM query_traces {where}
        """,
        params
    )
    avg_entities = cur.fetchone()["avg_entities"]

    # Retrieval type breakdown
    cur.execute(
        f"""
        SELECT retrieval_type, COUNT(*) as count
        FROM query_traces {where}
        GROUP BY retrieval_type
        ORDER BY count DESC
        """,
        params
    )
    retrieval_breakdown = cur.fetchall()

    # Latency over time (last 20 queries)
    cur.execute(
        f"""
        SELECT
            id,
            ROUND(latency_ms::numeric, 2) as latency_ms,
            retrieval_type,
            chunks_retrieved,
            entities_matched,
            created_at
        FROM query_traces {where}
        ORDER BY created_at DESC
        LIMIT 20
        """,
        params
    )
    recent = cur.fetchall()

    # Slowest queries
    cur.execute(
        f"""
        SELECT
            question,
            ROUND(latency_ms::numeric, 2) as latency_ms,
            retrieval_type,
            chunks_retrieved
        FROM query_traces {where}
        ORDER BY latency_ms DESC
        LIMIT 5
        """,
        params
    )
    slowest = cur.fetchall()

    # Success rate (answered vs failed)
    cur.execute(
        f"""
        SELECT
            COUNT(*) FILTER (
                WHERE answer NOT LIKE 'LLM generation failed%%'
                AND answer NOT LIKE 'I couldn%%'
            ) as success_count,
            COUNT(*) as total
        FROM query_traces {where}
        """,
        params
    )
    success = cur.fetchone()

    cur.close()
    conn.close()

    success_rate = 0
    if success["total"] > 0:
        success_rate = round(
            (success["success_count"] / success["total"]) * 100, 1
        )

    return {
        "total_queries": total_queries,
        "avg_latency_ms": float(latency["avg_latency"] or 0),
        "min_latency_ms": float(latency["min_latency"] or 0),
        "max_latency_ms": float(latency["max_latency"] or 0),
        "avg_chunks_retrieved": float(avg_chunks or 0),
        "avg_entities_matched": float(avg_entities or 0),
        "success_rate": success_rate,
        "retrieval_breakdown": [dict(r) for r in retrieval_breakdown],
        "latency_over_time": [dict(r) for r in reversed(recent)],
        "slowest_queries": [dict(r) for r in slowest],
        "recent_traces": [dict(r) for r in recent]
    }


@router.get("/metrics")
async def global_metrics():
    """Global metrics across all projects"""
    return get_metrics()


@router.get("/metrics/{project_id}")
async def project_metrics(project_id: int):
    """Metrics for a specific project"""
    return get_metrics(project_id)