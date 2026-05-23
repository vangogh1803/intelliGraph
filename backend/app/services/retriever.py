import json
import numpy as np
from app.services.embedder import embed_text, cosine_similarity
from app.database.postgres import get_chunks_by_project
from app.database.neo4j import neo4j_client
import re
from app.database.postgres import (
    get_chunks_by_project,
    find_files_by_name,
    get_chunks_by_file_id
)

def vector_search(
    query: str,
    project_id: int,
    top_k: int = 5
) -> list[dict]:
    """
    Find most similar chunks using cosine similarity.
    Returns top_k chunks sorted by similarity.
    """
    query_embedding = embed_text(query)
    chunks = get_chunks_by_project(project_id)

    scored = []
    for chunk in chunks:
        if not chunk["embedding"]:
            continue

        # Parse stored embedding
        stored = chunk["embedding"]
        if isinstance(stored, str):
            stored = json.loads(stored)

        score = cosine_similarity(query_embedding, stored)
        scored.append({
            "chunk_id": chunk["id"],
            "content": chunk["content"],
            "file_path": chunk["relative_path"],
            "extension": chunk["extension"],
            "score": score,
            "source": "vector"
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def extract_query_entities(query: str) -> list[str]:
    """
    Find which entities from our graph appear in the query.
    Simple but effective string matching approach.
    """
    # Get all entity names from graph
    all_entities = neo4j_client.run_query(
        "MATCH (e:Entity) RETURN e.name as name"
    )

    query_lower = query.lower()
    matched = []

    for e in all_entities:
        name = e["name"]
        # Check if entity name appears in query
        if name.lower() in query_lower:
            matched.append(name)

    return matched


def graph_search(
    entities: list[str],
    project_id: int,
    hops: int = 2
) -> list[dict]:
    """
    For each matched entity:
    1. Find its neighbors in the graph (N hops)
    2. Get all chunks that mention those entities
    Returns unique chunks with graph metadata.
    """
    if not entities:
        return []

    all_chunks = []
    traversed_entities = set()
    seen_chunks = set()

    for entity_name in entities:
        # Get neighbors
        neighbors = neo4j_client.run_query(
            """
            MATCH (e:Entity {name: $name})-[*1..2]-(neighbor:Entity)
            RETURN DISTINCT neighbor.name as name
            """,
            {"name": entity_name}
        )

        # Collect entity names (original + neighbors)
        related = [entity_name]
        for n in neighbors:
            related.append(n["name"])
            traversed_entities.add(n["name"])

        traversed_entities.add(entity_name)

        # Get chunks mentioning any of these entities
        for ename in related:
            chunks = neo4j_client.run_query(
                """
                MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {name: $name})
                MATCH (f:File)-[:HAS_CHUNK]->(c)
                RETURN c.id as chunk_id, c.content as content,
                       f.path as file_path, f.extension as extension
                """,
                {"name": ename}
            )

            for chunk in chunks:
                if chunk["chunk_id"] not in seen_chunks:
                    all_chunks.append({
                        "chunk_id": chunk["chunk_id"],
                        "content": chunk["content"],
                        "file_path": chunk["file_path"],
                        "extension": chunk["extension"] or "",
                        "score": 0.8,
                        "source": "graph",
                        "via_entity": ename
                    })
                    seen_chunks.add(chunk["chunk_id"])

    return all_chunks

def hybrid_retrieve(
    query: str,
    project_id: int,
    vector_top_k: int = 5,
    graph_hops: int = 1
) -> dict:
    """
    Combine overview + file + vector + graph retrieval.
    """

    # Check if broad question
    if is_broad_question(query):
        overview_chunks = project_overview_search(project_id)
        return {
            "chunks": overview_chunks[:8],
            "matched_entities": [],
            "traversed_entities": [],
            "graph_hops": 0,
            "retrieval_type": "overview",
            "vector_count": 0,
            "graph_count": 0,
            "file_count": len(overview_chunks)
        }

    # File-specific search
    file_chunks = file_search(query, project_id)

    # Vector search
    vector_chunks = vector_search(query, project_id, top_k=vector_top_k)

    # Graph search
    matched_entities = extract_query_entities(query)
    graph_chunks = graph_search(matched_entities, project_id, hops=graph_hops)

    # Merge with priority
    seen = set()
    merged = []

    # Priority 1: file chunks
    for c in file_chunks:
        if c["chunk_id"] not in seen:
            merged.append(c)
            seen.add(c["chunk_id"])

    # Priority 2: vector chunks
    for c in vector_chunks:
        if c["chunk_id"] not in seen:
            merged.append(c)
            seen.add(c["chunk_id"])

    # Priority 3: graph chunks
    for c in graph_chunks:
        if c["chunk_id"] not in seen:
            merged.append(c)
            seen.add(c["chunk_id"])

    has_file = len(file_chunks) > 0
    has_vector = len(vector_chunks) > 0
    has_graph = len(graph_chunks) > 0

    if has_file:
        retrieval_type = "file_exact"
    elif has_vector and has_graph:
        retrieval_type = "hybrid"
    elif has_vector:
        retrieval_type = "vector_only"
    elif has_graph:
        retrieval_type = "graph_only"
    else:
        retrieval_type = "none"

    traversed = set()
    for c in graph_chunks:
        if c.get("via_entity"):
            traversed.add(c["via_entity"])

    return {
        "chunks": merged[:8],
        "matched_entities": matched_entities,
        "traversed_entities": list(traversed),
        "graph_hops": graph_hops if has_graph else 0,
        "retrieval_type": retrieval_type,
        "vector_count": len(vector_chunks),
        "graph_count": len(graph_chunks),
        "file_count": len(file_chunks)
    }

def extract_file_mentions(query: str) -> list[str]:
    """
    Extract file-like tokens from query.
    Examples: index.html, main.py, App.jsx
    """
    file_pattern = r'([A-Za-z0-9_\-./]+\.(?:py|js|ts|jsx|tsx|html|css|json|md|txt|yaml|yml|toml))'
    matches = re.findall(file_pattern, query, flags=re.IGNORECASE)
    return list(set(matches))
def file_search(query: str, project_id: int) -> list[dict]:
    """
    If the query mentions a filename, fetch chunks from that file directly.
    """
    file_mentions = extract_file_mentions(query)
    if not file_mentions:
        return []

    results = []
    seen = set()

    for mentioned in file_mentions:
        files = find_files_by_name(project_id, mentioned)

        for f in files:
            chunks = get_chunks_by_file_id(f["id"])

            for chunk in chunks:
                if chunk["id"] in seen:
                    continue

                results.append({
                    "chunk_id": chunk["id"],
                    "content": chunk["content"],
                    "file_path": f["relative_path"],
                    "extension": f["extension"],
                    "score": 1.0,
                    "source": "file",
                    "via_entity": None
                })
                seen.add(chunk["id"])

    return results

def is_broad_question(query: str) -> bool:
    """
    Detect broad questions that need project-wide context.
    """
    broad_patterns = [
          "what functions",
          "what files",
          "what does this project",
          "explain the project",
          "project structure",
          "how does the project",
          "list all",
          "what modules",
          "what components",
          "overview",
          "summarize",
          "what is this project",
          "describe the project",
          "how is the project",
          "what technologies",
          "tech stack",
          "how do i use",
          "how to use",
          "how does the app",
          "what does the app",
          "how does this app",
          "what does this app",
          "walk me through",
          "explain how",
          "tell me about",
          "give me an overview",
          "main features",
          "what can this",
          "how to run",
    ]
    query_lower = query.lower()
    return any(p in query_lower for p in broad_patterns)



def project_overview_search(project_id: int) -> list[dict]:
    """
    Get first chunk from every file.
    Skip config and boilerplate files.
    Prioritize actual code files.
    """
    from app.database.postgres import get_connection

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT ON (f.relative_path)
            c.id, c.content, c.chunk_index,
            f.relative_path, f.extension
        FROM chunks c
        JOIN files f ON c.file_id = f.id
        WHERE c.project_id = %s
          AND f.extension NOT IN ('.json', '.css', '.yml', '.yaml', '.toml')
          AND f.filename NOT IN ('README.md', 'LICENSE', 'package.json',
                                  'tsconfig.json', '.eslintrc.js')
        ORDER BY f.relative_path, c.chunk_index ASC
        """,
        (project_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "chunk_id": row["id"],
            "content": row["content"][:400],
            "file_path": row["relative_path"],
            "extension": row["extension"],
            "score": 0.9,
            "source": "overview",
            "via_entity": None
        })

    return results