import os
import stat
import shutil
import subprocess
import ast
from pathlib import Path

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# langchain embedding wrapper around sentence-transformers
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# global faiss store, starts empty
vector_store = None

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}
ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".rb"}


# windows fix — git files are read-only so normal rmtree fails
def force_remove(path):
    def handle_error(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(path, onerror=handle_error)


def clone_repo(repo_url):
    if os.path.exists("./tmp_repo"):
        force_remove("./tmp_repo")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, "./tmp_repo"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f"git clone failed: {result.stderr}")


def get_all_code_files(folder):
    files = []
    for path in Path(folder).rglob("*"):
        if any(s in path.parts for s in SKIP_DIRS):
            continue
        if path.suffix in ALLOWED_EXTENSIONS and path.is_file():
            files.append(path)
    return files


def load_file_as_documents(file_path, repo_root):
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except:
        return []

    rel_path = str(file_path.relative_to(repo_root))
    lang = file_path.suffix.lstrip(".")

    # for python files use AST to get function/class level chunks
    if file_path.suffix == ".py":
        return python_to_documents(source, rel_path)

    # for everything else use langchain splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\nclass ", "\ndef ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_text(source)
    lines = source.splitlines()

    docs = []
    for chunk in chunks:
        # find line number of this chunk in the file
        try:
            start_line = next(i + 1 for i, line in enumerate(lines) if line in chunk)
        except:
            start_line = 1

        docs.append(Document(
            page_content=chunk,
            metadata={
                "file": rel_path,
                "language": lang,
                "start_line": start_line,
                "end_line": min(start_line + chunk.count("\n"), len(lines)),
                "name": ""
            }
        ))
    return docs


def python_to_documents(source, rel_path):
    docs = []
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except:
        # fallback to langchain splitter if ast fails
        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        for chunk in splitter.split_text(source):
            docs.append(Document(
                page_content=chunk,
                metadata={"file": rel_path, "language": "py", "start_line": 1, "end_line": len(lines), "name": ""}
            ))
        return docs

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno
            code = "\n".join(lines[start:end])
            if len(code.strip()) < 30:
                continue
            docs.append(Document(
                page_content=code,
                metadata={
                    "file": rel_path,
                    "language": "py",
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "name": node.name
                }
            ))

    return docs if docs else []


def index_repo(repo_url):
    global vector_store

    clone_repo(repo_url)

    files = get_all_code_files("./tmp_repo")
    all_docs = []

    for file_path in files:
        docs = load_file_as_documents(file_path, "./tmp_repo")
        all_docs.extend(docs)

    if not all_docs:
        raise Exception("no code files found in repo")

    # langchain creates FAISS index from all documents in one shot
    vector_store = FAISS.from_documents(all_docs, embeddings)

    force_remove("./tmp_repo")

    return {
        "files_indexed": len(files),
        "chunks_stored": len(all_docs),
        "repo": repo_url
    }
