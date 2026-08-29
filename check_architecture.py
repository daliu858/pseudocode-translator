"""Enforce the compiler's intended module dependency boundaries.

This check is deliberately dependency-free so it can run in every pull request.
It verifies the static import graph; runtime/dynamic imports remain a code-review
concern.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# A module may import standard-library/third-party modules freely.  Imports of
# project modules, however, must follow this allow-list.
ALLOWED_PROJECT_IMPORTS = {
    "errors": set(),
    "tokens": set(),
    "ast_nodes": set(),
    "lexer": {"errors", "tokens"},
    "parser": {"errors", "tokens", "ast_nodes"},
    "codegen": {"errors", "tokens", "ast_nodes"},
    "compiler": {"errors", "tokens", "ast_nodes", "lexer", "parser", "codegen"},
}

PROJECT_MODULES = set(ALLOWED_PROJECT_IMPORTS)


def imported_project_modules(node: ast.Import | ast.ImportFrom) -> set[str]:
    if isinstance(node, ast.ImportFrom):
        if node.level or not node.module:
            return set()
        root_name = node.module.split(".", 1)[0]
        return {root_name} if root_name in PROJECT_MODULES else set()

    return {
        alias.name.split(".", 1)[0]
        for alias in node.names
        if alias.name.split(".", 1)[0] in PROJECT_MODULES
    }


def check_module(module_name: str) -> list[str]:
    path = ROOT / f"{module_name}.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    allowed = ALLOWED_PROJECT_IMPORTS[module_name]
    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        imported_modules = imported_project_modules(node)
        if not imported_modules:
            continue

        for imported in imported_modules:
            if imported not in allowed:
                violations.append(
                    f"{path.name}:{node.lineno}: {module_name} must not import {imported}"
                )

        if isinstance(node, ast.ImportFrom):
            imported = next(iter(imported_modules))
            for alias in node.names:
                if alias.name == "*":
                    violations.append(
                        f"{path.name}:{node.lineno}: wildcard imports hide the public boundary"
                    )
                elif alias.name.startswith("_"):
                    violations.append(
                        f"{path.name}:{node.lineno}: private name {imported}.{alias.name} "
                        "must not cross a module boundary"
                    )

    return violations


def main() -> int:
    violations = [
        violation
        for module_name in ALLOWED_PROJECT_IMPORTS
        for violation in check_module(module_name)
    ]

    if violations:
        print("Architecture boundary check failed:")
        for violation in violations:
            print(f"  - {violation}")
        return 1

    print("Architecture boundary check passed.")
    print("  data modules -> stage modules -> compiler")
    print("  lexer/parser/codegen remain mutually independent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
