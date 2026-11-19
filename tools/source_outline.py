#!/usr/bin/env python3
"""Read Python source structure without importing it or exposing string values.

Use on relevant experiment files; never import hardware clients to inspect them.
Output contains only paths, hashes, import module names and definition names.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def outline(path):
    data = path.read_bytes()
    tree = ast.parse(data, filename=str(path))
    imports = []
    definitions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.append({"name": node.name, "line": node.lineno,
                                "kind": type(node).__name__})
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
            "imports": sorted(set(imports)), "definitions": definitions}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    result = []
    for path in args.paths:
        try:
            result.append(outline(path))
        except (OSError, SyntaxError) as exc:
            result.append({"path": str(path), "error": type(exc).__name__})
    print(json.dumps(result, indent=2, ensure_ascii=False))
