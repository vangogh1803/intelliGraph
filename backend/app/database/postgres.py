import psycopg2
from psycopg2.extras import RealDictCursor
import json
from app.config import settings


def get_connection():
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        dbname=settings.postgres_db,
        cursor_factory=RealDictCursor
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Projects table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            source      TEXT NOT NULL,
            source_url  TEXT,
            file_count  INT DEFAULT 0,
            chunk_count INT DEFAULT 0,
            status      TEXT DEFAULT 'uploaded',
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    # Files table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id            SERIAL PRIMARY KEY,
            project_id    INT REFERENCES projects(id) ON DELETE CASCADE,
            filename      TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            extension     TEXT NOT NULL,
            content       TEXT,
            created_at    TIMESTAMP DEFAULT NOW()
        );
    """)

    # Chunks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id          TEXT PRIMARY KEY,
            file_id     INT REFERENCES files(id) ON DELETE CASCADE,
            project_id  INT REFERENCES projects(id) ON DELETE CASCADE,
            content     TEXT NOT NULL,
            chunk_index INT NOT NULL,
            embedding   JSONB,
            created_at  TIMESTAMP DEFAULT NOW()
        );
    """)

    # Query traces table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS query_traces (
            id               SERIAL PRIMARY KEY,
            project_id       INT REFERENCES projects(id) ON DELETE CASCADE,
            question         TEXT NOT NULL,
            answer           TEXT,
            latency_ms       FLOAT,
            chunks_retrieved INT,
            graph_hops       INT,
            entities_matched INT,
            retrieval_type   TEXT,
            created_at       TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("PostgreSQL tables initialized")


# ─── Projects ────────────────────────────────────────────

def insert_project(
    name: str,
    source: str,
    source_url: str = None
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (name, source, source_url, status)
        VALUES (%s, %s, %s, 'processing')
        RETURNING id
        """,
        (name, source, source_url)
    )
    project_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return project_id


def update_project_status(
    project_id: int,
    status: str,
    file_count: int = None,
    chunk_count: int = None
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE projects
        SET status = %s,
            file_count = COALESCE(%s, file_count),
            chunk_count = COALESCE(%s, chunk_count)
        WHERE id = %s
        """,
        (status, file_count, chunk_count, project_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_all_projects():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, source, source_url,
               file_count, chunk_count, status, created_at
        FROM projects
        ORDER BY created_at DESC
        """
    )
    projects = cur.fetchall()
    cur.close()
    conn.close()
    return projects


def get_project_by_id(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM projects WHERE id = %s",
        (project_id,)
    )
    project = cur.fetchone()
    cur.close()
    conn.close()
    return project


# ─── Files ───────────────────────────────────────────────

def insert_file(
    project_id: int,
    filename: str,
    relative_path: str,
    extension: str,
    content: str
) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO files
            (project_id, filename, relative_path, extension, content)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (project_id, filename, relative_path, extension, content)
    )
    file_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return file_id


def get_files_by_project(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, filename, relative_path, extension
        FROM files
        WHERE project_id = %s
        ORDER BY relative_path
        """,
        (project_id,)
    )
    files = cur.fetchall()
    cur.close()
    conn.close()
    return files


# ─── Chunks ──────────────────────────────────────────────

def insert_chunk(
    chunk_id: str,
    file_id: int,
    project_id: int,
    content: str,
    chunk_index: int,
    embedding: list
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO chunks
            (id, file_id, project_id, content, chunk_index, embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (
            chunk_id, file_id, project_id,
            content, chunk_index, json.dumps(embedding)
        )
    )
    conn.commit()
    cur.close()
    conn.close()


def get_chunks_by_project(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.id, c.file_id, c.project_id,
               c.content, c.embedding, c.chunk_index,
               f.relative_path, f.extension
        FROM chunks c
        JOIN files f ON c.file_id = f.id
        WHERE c.project_id = %s
        ORDER BY f.relative_path, c.chunk_index
        """,
        (project_id,)
    )
    chunks = cur.fetchall()
    cur.close()
    conn.close()
    return chunks


# ─── Traces ──────────────────────────────────────────────

def insert_trace(
    project_id: int,
    question: str,
    answer: str,
    latency_ms: float,
    chunks_retrieved: int,
    graph_hops: int,
    entities_matched: int,
    retrieval_type: str
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO query_traces (
            project_id, question, answer, latency_ms,
            chunks_retrieved, graph_hops,
            entities_matched, retrieval_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            project_id, question, answer, latency_ms,
            chunks_retrieved, graph_hops,
            entities_matched, retrieval_type
        )
    )
    conn.commit()
    cur.close()
    conn.close()


def get_traces_by_project(project_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM query_traces
        WHERE project_id = %s
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (project_id,)
    )
    traces = cur.fetchall()
    cur.close()
    conn.close()
    return traces

def find_files_by_name(project_id: int, filename: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, filename, relative_path, extension
        FROM files
        WHERE project_id = %s
          AND (
              filename ILIKE %s
              OR relative_path ILIKE %s
          )
        ORDER BY relative_path
        """,
        (project_id, f"%{filename}%", f"%{filename}%")
    )
    files = cur.fetchall()
    cur.close()
    conn.close()
    return files


def get_chunks_by_file_id(file_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, file_id, project_id, content, chunk_index, embedding
        FROM chunks
        WHERE file_id = %s
        ORDER BY chunk_index
        """,
        (file_id,)
    )
    chunks = cur.fetchall()
    cur.close()
    conn.close()
    return chunks