from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health
from app.routers import project
from app.routers import graph
from app.routers import query
from app.routers import metrics
from app.database.postgres import init_db
from app.database.neo4j import neo4j_client

app = FastAPI(
    title="Project Intelligence Graph",
    description="GraphRAG Project Explorer with Observability",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()
    neo4j_client.init_constraints()
    print("Project Intelligence Graph started")


@app.on_event("shutdown")
async def shutdown():
    neo4j_client.close()


app.include_router(health.router,   tags=["Health"])
app.include_router(project.router,  tags=["Projects"])
app.include_router(graph.router,    tags=["Graph"])
app.include_router(query.router,    tags=["Query"])
app.include_router(metrics.router,  tags=["Metrics"])