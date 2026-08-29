# Pseudocode Studio

A small local IDE around the CAIE-style pseudocode compiler.

## Start

From the repository root:

```powershell
python -m ide.server
```

The server listens on `127.0.0.1:8765` and opens a browser. Use
`python -m ide.server --no-browser` when you only want the URL printed.

No Python or Node packages are required. The primary editor is Monaco Editor
0.55.1 loaded from jsDelivr. If it cannot be downloaded, the page switches to
a plain textarea while keeping compilation, open/save, and the Run workflows
available.

See [`NOTICE.md`](../NOTICE.md) for the student-use, independent-design, and
non-affiliation statement, and
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) for the Monaco copyright
and MIT license notice.
This zero-build version pins Monaco's compatibility AMD loader so that the
user only needs Python. Monaco now recommends ESM for new bundled projects;
if this IDE later adopts a Node/Vite build, migrate the editor import to ESM.

## Completion (experimental, not distributed)

An experimental next-token completion engine (token-category trigram fused
with real parser legality signals) was researched during development. Its
training corpus cannot lawfully be redistributed, so the engine and all of
its data are **not part of this repository**. This build runs in
compiler-only mode: `/api/completions` responds with an explicit
`completion_disabled` payload and the editor simply shows no ghost text.
Editing, diagnostics, compile and run are unaffected.

## Features

- Monaco syntax highlighting and editor behaviour for CAIE-style pseudocode;
- persistent `Studio Dark` and warm `Ivory Gold` themes, including matching
  Monaco syntax colours;
- Monaco ligatures are disabled so ASCII `!=` remains visibly two characters;
  the compiler still requires CAIE not-equals syntax `<>`;
- live compiler diagnostics, generated-Python preview, and a built-in Console
  for stdin/stdout execution;
- token-stream inspection;
- browser-local autosave, local file open, and download save;
- a server-side file workspace backing `OPENFILE` / `READFILE` / `WRITEFILE`;
- `Ctrl+Enter` compile, `Ctrl+Shift+Enter` run, `Ctrl+S` save.

`POST /api/run` compiles first and only executes error-free generated Python.
Execution happens in a fresh `python -I -u` child process, never by `exec` in
the IDE server. The runner provides normal `INPUT`/stdin and `OUTPUT`/stdout;
when the source contains only one FUNCTION or PROCEDURE definition, it also
returns entrypoint metadata and converts one stdin line per declared parameter
before invoking it. A non-`None` FUNCTION result is printed and PROCEDURE
output is captured normally.

The local runner has a three-second deadline, 64 KiB stdin budget, shared
64 KiB stdout/stderr budget, a restricted builtins table, and an import
allowlist for the compiler's `RAND` implementation. It is designed for locally
trusted pseudocode with resource limits; it is not an OS-level hostile-code
sandbox. Do not expose this localhost service to untrusted networks.

## Test

```powershell
python -m unittest -v test_ide_runner test_file_handling
```
