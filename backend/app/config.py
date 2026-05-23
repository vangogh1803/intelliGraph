from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "graphrag"
    postgres_password: str = "graphrag123"
    postgres_db: str = "graphrag_db"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "graphrag123"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3:mini"

    # App
    app_env: str = "development"
    app_port: int = 8000

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


settings = Settings()