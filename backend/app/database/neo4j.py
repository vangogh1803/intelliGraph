from neo4j import GraphDatabase
from app.config import settings


class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def verify_connection(self):
        self.driver.verify_connectivity()
        print("Neo4j connected successfully")

    def close(self):
        self.driver.close()

    def run_query(self, query: str, params: dict = {}):
        with self.driver.session() as session:
            result = session.run(query, params)
            return [record.data() for record in result]

    def init_constraints(self):
        """Set up basic graph constraints"""
        queries = [
            """
            CREATE CONSTRAINT document_id IF NOT EXISTS
            FOR (d:Document) REQUIRE d.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT entity_name IF NOT EXISTS
            FOR (e:Entity) REQUIRE e.name IS UNIQUE
            """,
            """
            CREATE CONSTRAINT chunk_id IF NOT EXISTS
            FOR (c:Chunk) REQUIRE c.id IS UNIQUE
            """
        ]
        for q in queries:
            try:
                self.run_query(q)
            except Exception as e:
                print(f"Constraint note: {e}")

        print("Neo4j constraints initialized")


neo4j_client = Neo4jClient()