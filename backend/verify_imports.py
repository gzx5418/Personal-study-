"""Verify internal imports for all target files."""
import ast
import os

TARGET_FILES = [
    "main.py",
    "core/stream_bus.py",
    "core/orchestrator.py",
    "services/rag_service.py",
    "services/session_service.py",
    "services/profile_service.py",
    "api/chat.py",
    "api/resources.py",
    "api/schemas.py",
    "api/evaluation.py",
    "api/profile.py",
    "api/path.py",
    "api/knowledge.py",
]

THIRD_PARTY = {
    "fastapi", "pydantic", "uvicorn", "openai", "httpx", "aiosqlite",
    "llama_index", "chromadb", "sse_starlette", "networkx", "numpy",
    "PyPDF2", "mammoth", "markdownify", "pptx", "PIL", "svglib",
    "reportlab", "dotenv", "starlette",
}

STDLIB = {
    "__future__", "asyncio", "json", "logging", "typing", "collections",
    "datetime", "uuid", "pathlib", "os", "sys", "time", "contextlib",
    "abc", "enum", "functools", "hashlib", "io", "math", "re",
    "shutil", "tempfile", "traceback", "copy", "dataclasses",
    "importlib", "inspect", "itertools", "operator", "string",
    "textwrap", "threading", "warnings", "base64", "struct",
}

errors = []

for fpath in TARGET_FILES:
    if not os.path.exists(fpath):
        errors.append(f"FILE NOT FOUND: {fpath}")
        continue
    
    with open(fpath, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            if top in STDLIB or top in THIRD_PARTY:
                continue
            # Check if it's a local module
            module_path = node.module.replace(".", "/")
            if os.path.exists(module_path + ".py") or os.path.isdir(module_path):
                continue
            # Could be a submodule file
            parts = node.module.split(".")
            if len(parts) >= 2:
                pkg_path = parts[0] + "/" + "/".join(parts[1:]) + ".py"
                if os.path.exists(pkg_path):
                    continue
            errors.append(f"  {fpath}:{node.lineno} - cannot resolve 'from {node.module} import ...'")
        
        elif isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in STDLIB or top in THIRD_PARTY:
                    continue
                module_path = alias.name.replace(".", "/")
                if os.path.exists(module_path + ".py") or os.path.isdir(module_path):
                    continue
                errors.append(f"  {fpath}:{node.lineno} - cannot resolve 'import {alias.name}'")

if errors:
    print("IMPORT ISSUES FOUND:")
    for e in errors:
        print(e)
else:
    print("ALL INTERNAL IMPORTS OK")
