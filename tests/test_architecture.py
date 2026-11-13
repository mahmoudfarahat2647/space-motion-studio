"""Architecture verification test.

Following Clean Architecture's Golden Rule (The Dependency Rule):
- Dependencies must point only inward toward higher-level policies.
- Domain cannot import application, adapters, or entrypoints.
- Application cannot import adapters or entrypoints.
- Domain and Application cannot import external framework libraries like Pydantic or external HTTP/SDKs.
- Filesystem operations (os, pathlib, shutil, tempfile) belong strictly to adapters.
"""

import ast
import os
from pathlib import Path
import pytest


def get_imports_from_file(file_path: Path) -> set[str]:
    """Parse python file and extract all top-level imported module names."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
            elif node.level > 0:
                # Relative import
                pass
    return imports


def get_internal_imports_from_file(file_path: Path) -> set[str]:
    """Parse python file and extract all space_motion_studio submodule imports."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    internal_imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("space_motion_studio"):
                    internal_imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("space_motion_studio"):
                internal_imports.add(node.module)
    return internal_imports


def test_domain_layer_dependencies():
    """Domain layer must not depend on any outer circle or external framework."""
    root = Path(__file__).parent.parent / "space_motion_studio" / "domain"
    domain_files = list(root.glob("*.py"))
    assert domain_files, "No domain files found"

    forbidden_packages = {
        "pydantic",
        "requests",
        "aiohttp",
        "edge_tts",
        "remotion",
        "pytest",
    }

    for file_path in domain_files:
        all_imports = get_imports_from_file(file_path)
        internal_imports = get_internal_imports_from_file(file_path)

        # Domain cannot import outer packages
        forbidden_found = all_imports.intersection(forbidden_packages)
        assert not forbidden_found, f"{file_path.name} imports forbidden outer packages: {forbidden_found}"

        # Domain cannot import application, adapters, or entrypoints
        for imp in internal_imports:
            assert not imp.startswith("space_motion_studio.application"), f"{file_path.name} illegally imports application layer: {imp}"
            assert not imp.startswith("space_motion_studio.adapters"), f"{file_path.name} illegally imports adapters layer: {imp}"
            assert not imp.startswith("space_motion_studio.entrypoints"), f"{file_path.name} illegally imports entrypoints layer: {imp}"


def test_application_layer_dependencies():
    """Application layer must not depend on adapters or entrypoints or external framework libraries."""
    root = Path(__file__).parent.parent / "space_motion_studio" / "application"
    app_files = list(root.rglob("*.py"))
    assert app_files, "No application files found"

    forbidden_packages = {
        "pydantic",
        "requests",
        "aiohttp",
        "edge_tts",
        "remotion",
    }

    for file_path in app_files:
        all_imports = get_imports_from_file(file_path)
        internal_imports = get_internal_imports_from_file(file_path)

        forbidden_found = all_imports.intersection(forbidden_packages)
        assert not forbidden_found, f"{file_path.name} imports forbidden framework library: {forbidden_found}"

        for imp in internal_imports:
            assert not imp.startswith("space_motion_studio.adapters"), f"{file_path.name} illegally imports adapters layer: {imp}"
            assert not imp.startswith("space_motion_studio.entrypoints"), f"{file_path.name} illegally imports entrypoints layer: {imp}"


def test_no_filesystem_leakage_in_domain_and_application():
    """Clean Architecture: filesystem operations (os, pathlib, shutil, tempfile) belong strictly to adapters."""
    base_dir = Path(__file__).parent.parent / "space_motion_studio"
    inner_files = list((base_dir / "domain").rglob("*.py")) + list((base_dir / "application").rglob("*.py"))

    filesystem_modules = {"os", "pathlib", "shutil", "tempfile"}

    for file_path in inner_files:
        imports = get_imports_from_file(file_path)
        leaked = imports.intersection(filesystem_modules)
        assert not leaked, (
            f"Clean Architecture violation: {file_path.relative_to(base_dir)} imports filesystem module {leaked}. "
            "All filesystem access must be encapsulated in adapters behind application ports."
        )
