import httpx
import json
import re
from app.config import settings

def is_code_extension(ext: str) -> bool:
    return ext in {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cpp", ".c"}

async def generate(prompt: str, temperature: float = 0.1) -> str:
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "num_ctx": 4096,
                    "num_predict": 500,
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]
def regex_extract_code_entities(
    code: str,
    file_path: str,
    extension: str
) -> dict:
    """
    Fallback entity extractor using regex.
    Works for Python and JavaScript/TypeScript.
    No LLM needed.
    """
    entities = []
    seen = set()

    def add(name, etype):
        if name and name not in seen and len(name) < 50:
            entities.append({"name": name, "type": etype})
            seen.add(name)

    ext = extension.lower()

    if ext == ".py":
        # Python functions
        for m in re.finditer(r'def\s+([a-zA-Z_]\w*)\s*\(', code):
            add(m.group(1), "Function")
        # Python classes
        for m in re.finditer(r'class\s+([a-zA-Z_]\w*)', code):
            add(m.group(1), "Class")
        # Python imports
        for m in re.finditer(r'import\s+([a-zA-Z_][\w.]*)', code):
            add(m.group(1).split(".")[0], "Module")
        for m in re.finditer(r'from\s+([a-zA-Z_][\w.]*)\s+import', code):
            add(m.group(1).split(".")[0], "Module")

    elif ext in {".js", ".ts", ".jsx", ".tsx"}:
        # JS/TS functions
        for m in re.finditer(
            r'(?:function\s+([a-zA-Z_]\w*)|const\s+([a-zA-Z_]\w*)\s*=\s*(?:async\s*)?\()',
            code
        ):
            name = m.group(1) or m.group(2)
            add(name, "Function")
        # React components (PascalCase)
        for m in re.finditer(r'const\s+([A-Z][a-zA-Z]*)\s*=', code):
            add(m.group(1), "Class")
        # imports
        for m in re.finditer(r"from\s+['\"]([^'\"]+)['\"]", code):
            mod = m.group(1).split("/")[-1].replace(".js","").replace(".ts","")
            if mod and not mod.startswith("."):
                add(mod, "Module")

    elif ext in {".md", ".txt"}:
        # Just skip regex for docs
        pass

    return {"entities": entities[:8], "relationships": []}
def extract_json_from_response(text: str) -> dict:
    """
    Extract JSON from LLM response.
    Handles prose before/after JSON, markdown blocks.
    """
    text = text.strip()

    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    # Find the LAST { ... } in the text
    # LLM sometimes writes prose then JSON at the end
    last_start = text.rfind('{')
    last_end = text.rfind('}')

    # Also try first occurrence
    first_start = text.find('{')
    first_end = text.find('}', first_start) if first_start != -1 else -1

    # Try last JSON first (more likely to be the output)
    candidates = []
    if last_start != -1 and last_end > last_start:
        candidates.append(text[last_start:last_end+1])
    if first_start != -1 and first_end > first_start:
        candidates.append(text[first_start:first_end+1])

    for candidate in candidates:
        # Fix common issues
        fixed = candidate
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)

        try:
            parsed = json.loads(fixed)
            if isinstance(parsed, dict):
                return parsed
        except:
            continue

    print(f"Could not extract JSON from: {text[:200]}")
    return {"entities": [], "relationships": []}


async def extract_entities_and_relations(
    chunk_text: str,
    extension: str = ".txt",
    file_path: str = ""
) -> dict:
    """
    Extract entities and relationships from code/text.
    Uses a very direct prompt that small LLMs can follow.
    """
    # Trim content
    chunk_text = chunk_text[:600].strip()
    ext = (extension or ".txt").lower()

    # Ultra direct prompt that works with small LLMs
    prompt = f"""TASK: Extract code entities from this file.
FILE: {file_path}

CODE:
{chunk_text}

OUTPUT RULES:
- Output ONLY a JSON object
- No explanation, no markdown, no code blocks
- Find: functions (def/function/const/=>/class), imports, variables
- Max 6 entities

OUTPUT THIS EXACT FORMAT:
{{"entities":[{{"name":"name_here","type":"Function"}},{{"name":"name_here","type":"Module"}}],"relationships":[]}}

JSON:"""

    try:
        raw = await generate(prompt, temperature=0.0)

        print("----- LLM RAW (first 300 chars) -----")
        print(raw[:300])
        print("-------------------------------------")

        result = extract_json_from_response(raw)

        if "entities" not in result:
            result["entities"] = []
        if "relationships" not in result:
            result["relationships"] = []

        # Clean entities
        cleaned = []
        for e in result["entities"]:
            if isinstance(e, dict) and "name" in e and "type" in e:
                name = str(e["name"]).strip()
                etype = str(e["type"]).strip()
                if name and len(name) < 60:
                    cleaned.append({"name": name, "type": etype})

        result["entities"] = cleaned
        result["relationships"] = []

    # If LLM returned nothing, use regex fallback
        if not cleaned and is_code_extension(ext):
            print("  → LLM returned 0 entities, using regex fallback")
            fallback = regex_extract_code_entities(
            chunk_text, file_path, ext
        )
            return fallback
        return result
    except Exception as e:
        print(f"Entity extraction failed: {e}")  
        return {"entities": [], "relationships": []}