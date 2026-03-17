
# export_tree.py
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

EXCLUDE_DIRS = {
    ".git", ".github", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".streamlit", ".vscode", "node_modules", "data", "datasets", "out", "dist", "build"
}
EXCLUDE_EXTS = {".parquet", ".csv", ".xlsx", ".zip", ".log"}
EXCLUDE_FILES = {".env"}

def should_skip(p: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in p.parts):
        return True
    if p.name in EXCLUDE_FILES:
        return True
    if p.suffix.lower() in EXCLUDE_EXTS:
        return True
    return False

def build_tree(root: Path) -> list[str]:
    lines: list[str] = []
    for p in sorted(root.rglob("*")):
        if should_skip(p):
            continue
        rel = p.relative_to(root)
        lines.append(str(rel).replace("\\", "/"))
    return lines

if __name__ == "__main__":
    lines = build_tree(ROOT)
    out = ROOT / "project_tree.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
