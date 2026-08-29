"""Local folder used by CAIE OPENFILE / READFILE / WRITEFILE.

The IDE is a localhost tool, so generated programs can read and write real
files on the student's machine.  Access is limited to one chosen folder and
to a single basename (no `..`, no subdirectories, no absolute paths).
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys


DEFAULT_WORKSPACE = Path(__file__).resolve().parent / "workspace"
MAX_FILE_BYTES = 256 * 1024
MAX_LISTED_FILES = 200
_SEED_FILE_A = (
    "alpha\n"
    "beta\n"
    "\n"
    "gamma\n"
)


def default_workspace() -> Path:
    return DEFAULT_WORKSPACE


def desktop_workspace() -> Path:
    home = Path.home()
    for name in ("Desktop", "桌面"):
        desktop = home / name
        if desktop.is_dir():
            return desktop / "PseudocodeFiles"
    return home / "PseudocodeFiles"


def ensure_workspace(path: Path | str | None = None) -> Path:
    folder = Path(path) if path is not None else default_workspace()
    folder = folder.expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    seed = folder / "FileA.txt"
    if not seed.exists():
        seed.write_text(_SEED_FILE_A, encoding="utf-8", newline="\n")
    return folder


def resolve_data_file(workspace: Path, name: str) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("file name is required")
    candidate = Path(name.replace("\\", "/"))
    if candidate.is_absolute() or len(candidate.parts) != 1 or candidate.name in {".", ".."}:
        raise ValueError("file names must be a single file in the workspace folder")
    target = (workspace / candidate.name).resolve()
    if workspace not in target.parents and target != workspace:
        raise ValueError("file names must stay inside the workspace folder")
    return target


def list_files(workspace: Path) -> list[dict]:
    entries = []
    for item in sorted(workspace.iterdir(), key=lambda path: path.name.casefold()):
        if not item.is_file() or item.name.startswith("."):
            continue
        stat = item.stat()
        entries.append(
            {
                "name": item.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M"),
            }
        )
        if len(entries) >= MAX_LISTED_FILES:
            break
    return entries


def read_file(workspace: Path, name: str) -> str:
    path = resolve_data_file(workspace, name)
    if not path.is_file():
        raise FileNotFoundError(name)
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"file is larger than {MAX_FILE_BYTES} bytes")
    return data.decode("utf-8", errors="replace")


def write_file(workspace: Path, name: str, content: str) -> dict:
    if not isinstance(content, str):
        raise ValueError("file content must be text")
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_FILE_BYTES:
        raise ValueError(f"file is larger than {MAX_FILE_BYTES} bytes")
    path = resolve_data_file(workspace, name)
    path.write_bytes(encoded)
    return {"name": path.name, "size": len(encoded)}


def delete_file(workspace: Path, name: str) -> None:
    path = resolve_data_file(workspace, name)
    if path.is_file():
        path.unlink()


def reveal_folder(workspace: Path) -> None:
    folder = str(workspace)
    if os.name == "nt":
        os.startfile(folder)  # type: ignore[attr-defined]
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen(
        [opener, folder],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def workspace_payload(workspace: Path) -> dict:
    return {
        "path": str(workspace),
        "desktopPath": str(desktop_workspace()),
        "files": list_files(workspace),
    }
