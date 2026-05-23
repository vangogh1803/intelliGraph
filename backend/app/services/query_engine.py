import time
from app.services.retriever import hybrid_retrieve
from app.services.ollama import generate
from app.database.postgres import insert_trace


async def answer_question(
    question: str,
    project_id: int
) -> dict:
    start_time = time.time()

    # Step 1: Retrieve
    retrieval = hybrid_retrieve(
        query=question,
        project_id=project_id,
        vector_top_k=5,
        graph_hops=1
    )

    chunks = retrieval["chunks"]

    if not chunks:
        return {
            "answer": "No relevant information found in the project.",
            "sources": [],
            "trace": {
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "chunks_retrieved": 0,
                "graph_hops": 0,
                "entities_matched": 0,
                "retrieval_type": "none"
            }
        }

    # Step 2: Build context based on retrieval type
    is_overview = retrieval["retrieval_type"] == "overview"

    if is_overview:
        # For overview: short summary per file
        context_parts = []
        sources = []
        for chunk in chunks:
            file_path = chunk.get("file_path", "unknown")
            content = chunk["content"][:300]
            context_parts.append(f"[{file_path}]\n{content}")
            sources.append({
                "file_path": file_path,
                "chunk_id": chunk["chunk_id"],
                "source_type": chunk["source"],
                "score": round(chunk.get("score", 0), 4),
                "via_entity": chunk.get("via_entity", None)
            })
        context = "\n\n".join(context_parts)
    else:
        # For specific questions: fewer chunks, more content
        context_parts = []
        sources = []
        total_len = 0
        budget = 1800

        for chunk in chunks:
            file_path = chunk.get("file_path", "unknown")
            content = chunk["content"]

            if total_len + len(content) <= budget:
                context_parts.append(f"[{file_path}]\n{content}")
                total_len += len(content)
            else:
                remaining = budget - total_len
                if remaining > 150:
                    context_parts.append(
                        f"[{file_path}]\n{content[:remaining]}"
                    )
                    total_len += remaining
                break

            sources.append({
                "file_path": file_path,
                "chunk_id": chunk["chunk_id"],
                "source_type": chunk["source"],
                "score": round(chunk.get("score", 0), 4),
                "via_entity": chunk.get("via_entity", None)
            })

        context = "\n\n---\n\n".join(context_parts)

    print(f"--- RETRIEVAL: {retrieval['retrieval_type']} ---")
    print(f"--- CONTEXT: {len(context)} chars, {len(chunks)} chunks ---")

    # Step 3: Build prompt based on query type
    if is_overview:
        prompt = f"""You are analyzing a codebase. Answer the question by examining the actual source code files shown below.

RULES:
- Describe what each file DOES based on the code, not based on README
- Mention specific function names, component names, and what they do
- Describe the user flow: what happens when someone uses this app
- If there are API endpoints, list them with their paths
- If there are React components, describe what each one renders
- Be specific and practical, not generic

Source code from the project:
{context}

Question: {question}

Detailed answer based on the actual code:"""

    else:
        prompt = f"""You are a code analyst. Answer using ONLY the code below.

RULES:
- State exact function names, variable names, parameters
- Include exact numbers and values from the code
- Reference file names where things are defined
- If you see chunk_size=300, say "300 words"
- If you see model name, state the exact model name
- Quote config values exactly as written

Code:
{context}

Question: {question}

Precise answer:"""

    # Step 4: Generate
    try:
        print(f"--- PROMPT: {len(prompt)} chars ---")
        answer = await generate(prompt, temperature=0.1)
        answer = answer.strip()
        print(f"--- ANSWER: {len(answer)} chars ---")
    except Exception as e:
        import traceback
        traceback.print_exc()
        answer = f"LLM generation failed: {str(e)}"

    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Step 5: Build trace
    trace = {
        "latency_ms": latency_ms,
        "chunks_retrieved": len(chunks),
        "graph_hops": retrieval["graph_hops"],
        "entities_matched": len(retrieval["matched_entities"]),
        "retrieval_type": retrieval["retrieval_type"],
        "matched_entities": retrieval.get("matched_entities", []),
        "traversed_entities": retrieval.get("traversed_entities", []),
        "vector_count": retrieval.get("vector_count", 0),
        "graph_count": retrieval.get("graph_count", 0)
    }

    # Step 6: Log trace
    try:
        insert_trace(
            project_id=project_id,
            question=question,
            answer=answer,
            latency_ms=latency_ms,
            chunks_retrieved=len(chunks),
            graph_hops=retrieval["graph_hops"],
            entities_matched=len(retrieval["matched_entities"]),
            retrieval_type=retrieval["retrieval_type"]
        )
    except Exception as e:
        print(f"Trace logging failed: {e}")

    return {
        "answer": answer,
        "sources": sources,
        "trace": trace
    }