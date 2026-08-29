"""Zero-dependency localhost server for the browser IDE.

Run from the repository root:

    python -m ide.server
"""

from __future__ import annotations

import argparse
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import threading
import webbrowser
from urllib.parse import parse_qs, urlsplit

from .application import DEFAULT_RELEASE_GOLD, IDEApplication
from .workspace import (
    delete_file,
    desktop_workspace,
    read_file,
    reveal_folder,
    workspace_payload,
    write_file,
)


STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"
MAX_REQUEST_BYTES = 1_000_000
_STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app.js": "app.js",
    "/styles.css": "styles.css",
    "/favicon.svg": "favicon.svg",
}


class IDEServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, application: IDEApplication):
        self.application = application
        super().__init__(address, IDERequestHandler)


class IDERequestHandler(BaseHTTPRequestHandler):
    server_version = "PseudocodeIDE/1.0"

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        split = urlsplit(self.path)
        path = split.path
        query = parse_qs(split.query)
        if path == "/api/health":
            self._send_json(HTTPStatus.OK, self.server.application.health())
            return
        if path == "/api/meta":
            self._send_json(HTTPStatus.OK, self.server.application.metadata())
            return
        if path == "/api/workspace":
            self._send_json(
                HTTPStatus.OK,
                workspace_payload(self.server.application.workspace),
            )
            return
        if path == "/api/workspace/file":
            names = query.get("name", [])
            if not names:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "name is required"})
                return
            try:
                content = read_file(self.server.application.workspace, names[0])
            except FileNotFoundError:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "file not found"})
                return
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, {"name": names[0], "content": content})
            return
        asset_name = _STATIC_FILES.get(path)
        if asset_name is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        self._send_static(STATIC_DIRECTORY / asset_name)

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlsplit(self.path).path
        try:
            payload = self._read_json_body()
            if path == "/api/completions":
                source = payload.get("source")
                browser_offset = payload.get("cursorOffset")
                python_offset = (
                    _utf16_offset_to_codepoint(source, browser_offset)
                    if isinstance(source, str) and browser_offset is not None
                    else browser_offset
                )
                result = self.server.application.complete(
                    source,
                    python_offset,
                    payload.get("limit", 8),
                )
                if isinstance(source, str):
                    _completion_offsets_to_utf16(source, result)
            elif path == "/api/compile":
                source = payload.get("source")
                result = self.server.application.compile(source)
                if isinstance(source, str):
                    _compiler_columns_to_utf16(source, result)
            elif path == "/api/run":
                source = payload.get("source")
                result = self.server.application.run(
                    source,
                    payload.get("stdin", ""),
                )
                if isinstance(source, str):
                    _compiler_columns_to_utf16(source, result)
            elif path == "/api/workspace":
                result = self.server.application.set_workspace(
                    payload.get("path"),
                    payload.get("create", True),
                )
            elif path == "/api/workspace/file":
                result = write_file(
                    self.server.application.workspace,
                    payload.get("name"),
                    payload.get("content", ""),
                )
                result.update(workspace_payload(self.server.application.workspace))
            elif path == "/api/workspace/delete":
                delete_file(
                    self.server.application.workspace,
                    payload.get("name"),
                )
                result = workspace_payload(self.server.application.workspace)
            elif path == "/api/workspace/reveal":
                reveal_folder(self.server.application.workspace)
                result = {"ok": True, **workspace_payload(self.server.application.workspace)}
            elif path == "/api/workspace/desktop":
                result = self.server.application.set_workspace(
                    desktop_workspace(),
                    True,
                )
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception as exc:
            # Keep internal details out of the browser response.  The compiler
            # application itself converts user-input failures into diagnostics.
            self.log_error("unhandled API error: %s", exc)
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal server error"},
            )
            return
        self._send_json(HTTPStatus.OK, result)

    def _read_json_body(self) -> dict:
        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise ValueError("Content-Type must be application/json")
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "0")
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length <= 0:
            raise ValueError("request body is empty")
        if length > MAX_REQUEST_BYTES:
            raise ValueError("request body is too large")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body is not valid UTF-8 JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _send_static(self, path: Path) -> None:
        if not path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "asset not found"})
            return
        content = path.read_bytes()
        mime, _ = mimetypes.guess_type(path.name)
        self.send_response(HTTPStatus.OK)
        self._common_headers()
        self.send_header("Content-Type", f"{mime or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        # Escaping non-ASCII also makes the response robust to a lone UTF-16
        # surrogate received through otherwise valid escaped JSON. Browsers
        # decode the JSON back to the same Unicode value.
        content = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self._common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _common_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self' https://cdn.jsdelivr.net; "
            "worker-src 'self' blob: data: https://cdn.jsdelivr.net",
        )

    def log_message(self, format, *args):
        # Keep the console useful without changing BaseHTTPRequestHandler's
        # proven formatting and timestamp behaviour.
        super().log_message(format, *args)


def create_server(
    application: IDEApplication,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> IDEServer:
    return IDEServer((host, port), application)


def _utf16_offset_to_codepoint(text: str, offset) -> int:
    """Translate a browser/Monaco UTF-16 offset to a Python string index."""
    if isinstance(offset, bool) or not isinstance(offset, int):
        raise ValueError("cursorOffset must be an integer")
    if offset < 0:
        raise ValueError("cursorOffset is outside the source")
    units = 0
    if offset == 0:
        return 0
    for index, char in enumerate(text):
        units += 2 if ord(char) > 0xFFFF else 1
        if units == offset:
            return index + 1
        if units > offset:
            raise ValueError("cursorOffset splits a UTF-16 surrogate pair")
    if units != offset:
        raise ValueError("cursorOffset is outside the source")
    return len(text)


def _codepoint_offset_to_utf16(text: str, offset: int) -> int:
    return len(text[:offset].encode("utf-16-le")) // 2


def _completion_offsets_to_utf16(source: str, result: dict) -> None:
    for item in result.get("items", []):
        item["replaceStart"] = _codepoint_offset_to_utf16(
            source, item["replaceStart"])
        item["replaceEnd"] = _codepoint_offset_to_utf16(
            source, item["replaceEnd"])
    result["offsetEncoding"] = "utf-16"


def _compiler_columns_to_utf16(source: str, result: dict) -> None:
    lines = source.split("\n")
    for diagnostic in result.get("diagnostics", []):
        line_index = max(0, diagnostic["line"] - 1)
        line = lines[line_index] if line_index < len(lines) else ""
        start = max(0, diagnostic["column"] - 1)
        end = max(start, diagnostic["endColumn"] - 1)
        diagnostic["column"] = _codepoint_offset_to_utf16(line, start) + 1
        diagnostic["endColumn"] = _codepoint_offset_to_utf16(line, end) + 1
    for token in result.get("tokens", []):
        line_index = max(0, token["line"] - 1)
        line = lines[line_index] if line_index < len(lines) else ""
        start = max(0, token["column"] - 1)
        token["column"] = _codepoint_offset_to_utf16(line, start) + 1
    result["columnEncoding"] = "utf-16"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_RELEASE_GOLD,
        help="optional local training corpus for the experimental completion "
             "engine (not distributed with this repository; the IDE runs in "
             "compiler-only mode when it is absent)",
    )
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="folder used by OPENFILE / READFILE / WRITEFILE (default: ide/workspace)",
    )
    return parser


def main(argv=None) -> int:
    # Windows consoles pick legacy code pages (e.g. cp932); the workspace path
    # may contain non-ASCII characters, so degrade to '?' instead of crashing.
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass
    args = _parser().parse_args(argv)
    if not 0 <= args.port <= 65535:
        raise SystemExit("--port must be between 0 and 65535")

    application = IDEApplication.from_release(args.corpus, workspace=args.workspace)
    server = create_server(application, args.host, args.port)
    actual_host, actual_port = server.server_address[:2]
    display_host = "127.0.0.1" if actual_host in {"0.0.0.0", "::"} else actual_host
    url = f"http://{display_host}:{actual_port}/"
    stats = application.stats
    if stats is not None:
        engine_line = (
            f"Hybrid trigram: {stats.unique_streams} unique streams, "
            f"{stats.training_tokens} tokens."
        )
    else:
        engine_line = (
            "Completion: disabled (experimental engine not distributed "
            "in this build; compile/run fully available)."
        )
    print(
        f"Pseudocode IDE ready at {url}\n"
        f"File workspace: {application.workspace}\n"
        f"{engine_line} Press Ctrl+C to stop."
    )
    if not args.no_browser:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Pseudocode IDE.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
