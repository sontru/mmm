from pathlib import Path

from .config import ROOT_DIR


# ---------------------------------------------------------------------------
# Editable project file rules
# ---------------------------------------------------------------------------

CODE_FILE_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
EXCLUDED_DIRS = {
    ".agents",
    ".codex",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "__pycache__",
}
EXCLUDED_FILES = {"mmm_server.db"}
MAX_CODE_BYTES = 1_000_000


# ---------------------------------------------------------------------------
# Public API used by the local admin HTTP handlers
# ---------------------------------------------------------------------------

def code_files():
    """Return every editable project code file visible to the admin editor."""
    files = []
    for path in sorted(ROOT_DIR.rglob("*")):
        if not _is_listable_code_file(path):
            continue
        files.append(
            {
                "path": _relative_path(path),
                "name": path.name,
                "size": path.stat().st_size,
                "language": _language_for(path),
            }
        )
    return files


def read_code_file(file_path):
    """Read one validated project code file as UTF-8 text."""
    path = _safe_code_path(file_path)
    return {
        "path": _relative_path(path),
        "name": path.name,
        "language": _language_for(path),
        "content": path.read_text(encoding="utf-8"),
    }


def save_code_file(file_path, content):
    """Validate and save a project code file from the local admin editor."""
    path = _safe_code_path(file_path)
    if not isinstance(content, str):
        raise ValueError("File content is required")
    if len(content.encode("utf-8")) > MAX_CODE_BYTES:
        raise ValueError("File is too large")
    if "\x00" in content:
        raise ValueError("Binary content is not supported")
    path.write_text(content, encoding="utf-8")
    return read_code_file(file_path)


# ---------------------------------------------------------------------------
# Path validation helpers
# ---------------------------------------------------------------------------

def _safe_code_path(file_path):
    """Resolve and validate a requested project code file path."""
    path = (ROOT_DIR / str(file_path)).resolve()
    try:
        path.relative_to(ROOT_DIR.resolve())
    except ValueError:
        raise ValueError("File must be inside this project") from None
    if not _is_listable_code_file(path):
        raise ValueError("Unknown editable code file")
    return path


def _is_listable_code_file(path):
    """Return whether a path is an editable project code file."""
    if not path.is_file():
        return False
    if path.name in EXCLUDED_FILES:
        return False
    if path.suffix.lower() not in CODE_FILE_EXTENSIONS:
        return False
    relative_parts = path.resolve().relative_to(ROOT_DIR.resolve()).parts
    return not any(part in EXCLUDED_DIRS for part in relative_parts)


def _relative_path(path):
    """Return a project-relative POSIX path for display or API payloads."""
    return path.resolve().relative_to(ROOT_DIR).as_posix()


def _language_for(path):
    """Return the editor language label for a file extension."""
    return {
        ".css": "css",
        ".html": "html",
        ".js": "javascript",
        ".json": "json",
        ".md": "markdown",
        ".py": "python",
        ".txt": "text",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(path.suffix.lower(), "text")
