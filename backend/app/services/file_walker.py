import os
import zipfile
import shutil
import tempfile

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("gitpython not installed. GitHub import disabled.")

# File types we support
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".cpp", ".c",
    ".html", ".css",
    ".md", ".txt", ".rst",
    ".json", ".yaml", ".yml", ".toml", ".env",
}

# Directories to always skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__",
    ".venv", "venv", "env", "dist", "build",
    ".next", ".nuxt", "coverage", ".pytest_cache",
    "eggs", ".eggs", "wheels", "htmlcov",
    ".mypy_cache", ".ruff_cache",
    "__MACOSX", ".DS_Store_dir"
}

# Files to always skip
SKIP_FILES = {
    ".DS_Store", "package-lock.json",
    "yarn.lock", "poetry.lock",
    "Pipfile.lock", ".gitignore",
    "README.md", "LICENSE", "LICENSE.md",
    "CHANGELOG.md", "CONTRIBUTING.md",
    ".eslintrc.js", ".prettierrc",
    "jest.config.js", "babel.config.js",
    "tsconfig.json",
}

# Max file size (500KB)
MAX_FILE_SIZE = 500 * 1024


def should_skip_file(filename: str, full_path: str) -> bool:
    """Check if a file should be skipped"""
    # Skip hidden files starting with ._
    if filename.startswith("._"):
        return True

    # Skip by name
    if filename in SKIP_FILES:
        return True

    # Skip binary-looking extensions
    binary_ext = {".pyc", ".pyo", ".so", ".dylib", ".exe", ".dll", ".png", ".jpg", ".gif", ".ico", ".woff", ".ttf"}
    ext = os.path.splitext(filename)[1].lower()
    if ext in binary_ext:
        return True

    # Skip if too large
    try:
        if os.path.getsize(full_path) > MAX_FILE_SIZE:
            print(f"  Skipping large file: {filename}")
            return True
    except Exception:
        return True

    return False


def read_file_content(full_path: str) -> str:
    """Read file content safely, removing NUL bytes"""
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        # Remove NUL bytes that break PostgreSQL
        content = content.replace("\x00", "")
        # Remove other problematic characters
        content = content.replace("\r\n", "\n")
        return content
    except Exception as e:
        print(f"  Could not read {full_path}: {e}")
        return ""


def walk_directory(root_path: str) -> list[dict]:
    """
    Recursively walk a directory and return
    all supported files with their content.
    """
    files = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Remove skipped dirs in place
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            full_path = os.path.join(dirpath, filename)

            if should_skip_file(filename, full_path):
                print(f"  Skipping: {filename}")
                continue

            content = read_file_content(full_path)
            if not content.strip():
                continue

            relative_path = os.path.relpath(full_path, root_path)

            files.append({
                "filename": filename,
                "relative_path": relative_path,
                "extension": ext,
                "content": content
            })

    print(f"Found {len(files)} supported files in project")
    return files


def extract_zip(zip_bytes: bytes) -> tuple[str, str]:
    """Extract ZIP file to a temp directory"""
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "project.zip")

    with open(zip_path, "wb") as f:
        f.write(zip_bytes)

    extract_path = os.path.join(temp_dir, "extracted")
    os.makedirs(extract_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_path)

    # If ZIP contains a single root folder, go into it
    contents = [
        c for c in os.listdir(extract_path)
        if not c.startswith(".") and c != "__MACOSX"
    ]

    if len(contents) == 1 and os.path.isdir(
        os.path.join(extract_path, contents[0])
    ):
        project_root = os.path.join(extract_path, contents[0])
    else:
        project_root = extract_path

    return temp_dir, project_root


def clone_github_repo(url: str) -> tuple[str, str]:
    """Clone a GitHub repo to a temp directory"""
    if not GIT_AVAILABLE:
        raise RuntimeError(
            "gitpython not installed. Run: pip install gitpython"
        )
    temp_dir = tempfile.mkdtemp()
    repo_path = os.path.join(temp_dir, "repo")
    print(f"Cloning {url}...")
    git.Repo.clone_from(url, repo_path, depth=1)
    print(f"Cloned successfully")
    return temp_dir, repo_path


def cleanup_temp(temp_dir: str):
    """Remove temp directory after processing"""
    try:
        shutil.rmtree(temp_dir)
        print(f"Cleaned up {temp_dir}")
    except Exception as e:
        print(f"Cleanup warning: {e}")