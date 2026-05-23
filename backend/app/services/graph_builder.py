from app.database.neo4j import neo4j_client


def store_document_node(doc_id: int, filename: str):
    """Create a Document node in Neo4j"""
    neo4j_client.run_query(
        """
        MERGE (d:Document {id: $id})
        SET d.filename = $filename
        """,
        {"id": doc_id, "filename": filename}
    )


def store_chunk_node(chunk_id: str, doc_id: int, content: str, index: int):
    """Create a Chunk node and link it to its Document"""
    neo4j_client.run_query(
        """
        MERGE (c:Chunk {id: $chunk_id})
        SET c.content = $content,
            c.index = $index
        """,
        {"chunk_id": chunk_id, "content": content, "index": index}
    )

    # Link chunk to document
    neo4j_client.run_query(
        """
        MATCH (d:Document {id: $doc_id})
        MATCH (c:Chunk {id: $chunk_id})
        MERGE (d)-[:CONTAINS]->(c)
        """,
        {"doc_id": doc_id, "chunk_id": chunk_id}
    )


def store_entities(chunk_id: str, entities: list):
    """
    Create Entity nodes and link them to their Chunk.
    Uses MERGE so duplicate entities are not created.
    """
    for entity in entities:
        # Create or update entity node
        neo4j_client.run_query(
            """
            MERGE (e:Entity {name: $name})
            SET e.type = $type
            """,
            {"name": entity["name"], "type": entity["type"]}
        )

        # Link entity to chunk
        neo4j_client.run_query(
            """
            MATCH (c:Chunk {id: $chunk_id})
            MATCH (e:Entity {name: $name})
            MERGE (c)-[:MENTIONS]->(e)
            """,
            {"chunk_id": chunk_id, "name": entity["name"]}
        )


def store_relationships(relationships: list):
    """
    Create edges between Entity nodes.
    Uses MERGE so duplicate relationships are not created.
    """
    for rel in relationships:
        neo4j_client.run_query(
            """
            MATCH (a:Entity {name: $from_name})
            MATCH (b:Entity {name: $to_name})
            MERGE (a)-[r:RELATED {type: $relation}]->(b)
            """,
            {
                "from_name": rel["from"],
                "to_name": rel["to"],
                "relation": rel["relation"]
            }
        )


def get_graph_stats() -> dict:
    """Return basic stats about the graph"""
    docs = neo4j_client.run_query(
        "MATCH (d:Document) RETURN count(d) as count"
    )
    chunks = neo4j_client.run_query(
        "MATCH (c:Chunk) RETURN count(c) as count"
    )
    entities = neo4j_client.run_query(
        "MATCH (e:Entity) RETURN count(e) as count"
    )
    rels = neo4j_client.run_query(
        "MATCH ()-[r:RELATED]->() RETURN count(r) as count"
    )

    return {
        "docs":     docs[0]["count"] if docs else 0,
        "chunks":   chunks[0]["count"] if chunks else 0,
        "entities": entities[0]["count"] if entities else 0,
        "rels":     rels[0]["count"] if rels else 0
    }

def get_entity_neighbors(entity_name: str, hops: int = 2) -> list:
    """
    Get all entities connected to a given entity
    within N hops. Used during retrieval.
    """
    result = neo4j_client.run_query(
        """
        MATCH (e:Entity {name: $name})-[*1..$hops]-(neighbor:Entity)
        RETURN DISTINCT neighbor.name as name, neighbor.type as type
        """,
        {"name": entity_name, "hops": hops}
    )
    return result


def get_chunks_for_entity(entity_name: str) -> list:
    """
    Get all chunks that mention a given entity.
    Used to expand context during retrieval.
    """
    result = neo4j_client.run_query(
        """
        MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {name: $name})
        RETURN c.id as chunk_id, c.content as content
        """,
        {"name": entity_name}
    )
    return result