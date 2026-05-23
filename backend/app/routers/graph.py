from fastapi import APIRouter, HTTPException
from app.database.postgres import get_chunks_by_project, get_project_by_id
from app.database.neo4j import neo4j_client
from app.services.ollama import extract_entities_and_relations
from app.services.graph_builder import (
    store_entities,
    store_relationships,
    get_graph_stats,
    get_entity_neighbors,
    get_chunks_for_entity
)
import asyncio

router = APIRouter()


@router.post("/graph/build-project/{project_id}")
async def build_graph_for_project(project_id: int):
    """
    Build knowledge graph for an entire project.
    """
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chunks = get_chunks_by_project(project_id)
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No chunks found. Upload project first."
        )

    # Create project node
    neo4j_client.run_query(
        """
        MERGE (p:Project {id: $id})
        SET p.name = $name
        """,
        {"id": project_id, "name": project["name"]}
    )

    total_entities = 0
    total_relationships = 0
    failed_chunks = 0
    skipped_chunks = 0

    for i, chunk in enumerate(chunks):
        chunk_id = chunk["id"]
        content = chunk["content"]
        relative_path = chunk["relative_path"]
        extension = chunk["extension"]
        chunk_index = chunk.get("chunk_index", 0)

        print(f"\n--- Chunk {i+1}/{len(chunks)} ---")
        print(f"File: {relative_path}")
        print(f"Chunk index: {chunk_index}")
        print(f"Content: {len(content)} chars")

        # Create file node
        neo4j_client.run_query(
            """
            MERGE (f:File {path: $path, project_id: $project_id})
            SET f.extension = $extension
            """,
            {
                "path": relative_path,
                "project_id": project_id,
                "extension": extension
            }
        )

        # Create chunk node
        neo4j_client.run_query(
            """
            MERGE (c:Chunk {id: $chunk_id})
            SET c.content = $content
            """,
            {"chunk_id": chunk_id, "content": content[:500]}
        )

        # Link project → file
        neo4j_client.run_query(
            """
            MATCH (p:Project {id: $project_id})
            MATCH (f:File {path: $path, project_id: $project_id})
            MERGE (p)-[:HAS_FILE]->(f)
            """,
            {"project_id": project_id, "path": relative_path}
        )

        # Link file → chunk
        neo4j_client.run_query(
            """
            MATCH (f:File {path: $path, project_id: $project_id})
            MATCH (c:Chunk {id: $chunk_id})
            MERGE (f)-[:HAS_CHUNK]->(c)
            """,
            {
                "path": relative_path,
                "project_id": project_id,
                "chunk_id": chunk_id
            }
        )

        # Only extract entities from first 2 chunks per file
        # This prevents Ollama overload on large projects
        if chunk_index > 1:
            print(f"  ⏭ Skipping extraction (chunk index {chunk_index} > 1)")
            skipped_chunks += 1
            continue

        # Extract entities
        try:
            extracted = await extract_entities_and_relations(
                content[:800],
                extension=extension,
                file_path=relative_path
            )

            entities = extracted.get("entities", [])
            relationships = extracted.get("relationships", [])

            print(f"  ✅ Entities: {len(entities)}, Relations: {len(relationships)}")

            # Print what was found
            for e in entities:
                print(f"     Entity: {e['name']} ({e['type']})")
            for r in relationships:
                print(f"     Rel: {r['from']} --{r['relation']}--> {r['to']}")

            if entities:
                store_entities(chunk_id, entities)
            if relationships:
                store_relationships(relationships)

            total_entities += len(entities)
            total_relationships += len(relationships)

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed_chunks += 1

        # Small delay to let Ollama breathe
        await asyncio.sleep(0.5)

    print(f"\n{'='*50}")
    print(f"BUILD COMPLETE")
    print(f"Entities: {total_entities}")
    print(f"Relationships: {total_relationships}")
    print(f"Failed: {failed_chunks}")
    print(f"Skipped: {skipped_chunks}")
    print(f"{'='*50}")

    return {
        "message": "Project graph built successfully",
        "project_id": project_id,
        "project_name": project["name"],
        "chunks_processed": len(chunks),
        "entities_extracted": total_entities,
        "relationships_extracted": total_relationships,
        "failed_chunks": failed_chunks,
        "skipped_chunks": skipped_chunks
    }


@router.get("/graph/stats")
async def graph_stats():
    stats = get_graph_stats()
    return stats


@router.get("/graph/entity/{entity_name}")
async def entity_info(entity_name: str, hops: int = 2):
    neighbors = get_entity_neighbors(entity_name.lower(), hops)
    chunks = get_chunks_for_entity(entity_name.lower())
    return {
        "entity": entity_name,
        "neighbors": neighbors,
        "appears_in_chunks": len(chunks),
        "chunks": chunks
    }


@router.get("/graph/entities")
async def list_entities():
    result = neo4j_client.run_query(
        """
        MATCH (e:Entity)
        RETURN e.name as name, e.type as type
        ORDER BY e.name
        """
    )
    return {"entities": result, "count": len(result)}


@router.get("/graph/visualize/{project_id}")
async def visualize_graph(project_id: int):
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes = []
    edges = []
    seen = set()
    edge_idx = 0

    # 1. Project node
    nodes.append({
        "id": f"project::{project_id}",
        "data": {
            "label": project["name"],
            "nodeType": "Project"
        },
        "position": {"x": 0, "y": 0}
    })
    seen.add(f"project::{project_id}")

    # 2. File nodes
    file_rows = neo4j_client.run_query(
        """
        MATCH (p:Project {id: $pid})-[:HAS_FILE]->(f:File)
        RETURN DISTINCT f.path as path, f.extension as ext
        """,
        {"pid": project_id}
    )

    for f in file_rows:
        fid = f"file::{f['path']}"
        if fid not in seen:
            short = f["path"].split("/")[-1]
            nodes.append({
                "id": fid,
                "data": {
                    "label": short,
                    "nodeType": "File",
                    "fullPath": f["path"],
                    "extension": f["ext"]
                },
                "position": {"x": 0, "y": 0}
            })
            seen.add(fid)

            edges.append({
                "id": f"e_{edge_idx}",
                "source": f"project::{project_id}",
                "target": fid,
                "label": "HAS_FILE",
                "type": "default"
            })
            edge_idx += 1

    # 3. Entity nodes
    entity_rows = neo4j_client.run_query(
        """
        MATCH (p:Project {id: $pid})-[:HAS_FILE]->(f:File)
              -[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
        RETURN DISTINCT e.name as name, e.type as type
        """,
        {"pid": project_id}
    )

    for e in entity_rows:
        eid = f"entity::{e['name']}"
        if eid not in seen:
            nodes.append({
                "id": eid,
                "data": {
                    "label": e["name"],
                    "nodeType": e["type"] or "Entity"
                },
                "position": {"x": 0, "y": 0}
            })
            seen.add(eid)

    # 4. File → Entity edges
    file_entity = neo4j_client.run_query(
        """
        MATCH (p:Project {id: $pid})-[:HAS_FILE]->(f:File)
              -[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
        RETURN DISTINCT f.path as file_path, e.name as entity_name
        """,
        {"pid": project_id}
    )

    for fe in file_entity:
        fid = f"file::{fe['file_path']}"
        eid = f"entity::{fe['entity_name']}"
        if fid in seen and eid in seen:
            edges.append({
                "id": f"e_{edge_idx}",
                "source": fid,
                "target": eid,
                "label": "DEFINES",
                "type": "default"
            })
            edge_idx += 1

    # 5. Entity → Entity edges
    rel_rows = neo4j_client.run_query(
        """
        MATCH (p:Project {id: $pid})-[:HAS_FILE]->(:File)
              -[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(e1:Entity)
        MATCH (e1)-[r:RELATED]->(e2:Entity)
        RETURN DISTINCT e1.name as from_name, r.type as rel, e2.name as to_name
        """,
        {"pid": project_id}
    )

    for r in rel_rows:
        fid = f"entity::{r['from_name']}"
        tid = f"entity::{r['to_name']}"
        if fid in seen and tid in seen:
            edges.append({
                "id": f"e_{edge_idx}",
                "source": fid,
                "target": tid,
                "label": r["rel"] or "related",
                "type": "default"
            })
            edge_idx += 1

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "files": len(file_rows),
            "entities": len(entity_rows)
        }
    }