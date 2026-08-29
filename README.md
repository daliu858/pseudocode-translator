# Pseudocode Studio — CAIE-style Pseudocode Compiler & Local IDE

A **local** compiler + browser IDE for CAIE-style (Cambridge Assessment
International Education, e.g. 9618/0478) pseudocode:

- **Compiler**: lexer → parser/AST → Python code generation, with
  multi-error recovery and line/column diagnostics;
- **IDE**: Monaco editor, live diagnostics, generated-Python preview,
  built-in console (stdin/stdout), and a server-side file workspace backing
  `OPENFILE` / `READFILE` / `WRITEFILE`;
- Pure standard library — **zero third-party Python dependencies**; one
  command to start: `python -m ide.server`.

> **Contact**: for any questions, concerns, or rights complaints, email
> **<pseudocode-translator@protonmail.com>**. See the
> [Disclaimer](#disclaimer) below.

> **Note**: ghost-text auto-completion is an **experimental research
> feature and is not distributed with this repository** (see Disclaimer,
> item 5). The IDE in this repository runs in compiler-only mode: editing,
> diagnostics, compile, and run are all available — only AI completion is
> absent.

---

## Quick Start: Opening the IDE Locally

### 0. Requirements

| Requirement | Details |
|---|---|
| Python | 3.10 / 3.12 / 3.13 (versions covered by CI; any 3.10+ works) |
| OS | Windows / macOS / Linux |
| Third-party packages | **None** — no `pip install` needed |
| Network | Monaco Editor loads from the jsDelivr CDN on first page load; offline, the page falls back to a plain textarea and compile/run keep working |

### 1. Get the code

```bash
git clone https://github.com/daliu858/pesudocode-translator.git
cd pesudocode-translator
```

(Or Download ZIP, extract, and enter the directory.)

### 2. Start the IDE server

Run **from the repository root**:

```bash
python -m ide.server
```

You should see:

```text
Pseudocode IDE ready at http://127.0.0.1:8765/
File workspace: <your path>/ide/workspace
Completion: disabled (experimental engine not distributed in this build;
compile/run fully available). Press Ctrl+C to stop.
```

A browser window opens automatically at `http://127.0.0.1:8765/`. If it
does not, open that address manually.

Useful flags:

```bash
python -m ide.server --no-browser          # print the URL only
python -m ide.server --port 9000           # change port (default 8765)
python -m ide.server --workspace D:\mywork # folder used by OPENFILE/READFILE/WRITEFILE
```

### 3. Write your first program

Type into the editor:

```text
DECLARE total : INTEGER
DECLARE value : INTEGER
total <- 0

INPUT value
WHILE value <> -1
    total <- total + value
    INPUT value
ENDWHILE

OUTPUT total
```

- **Ctrl+Enter** — compile: the generated Python and the token stream
  appear on the right; errors show as squiggles plus a diagnostics panel
  with exact line/column positions;
- **Ctrl+Shift+Enter** (or the Run button) — run: the built-in console
  supports interactive `INPUT` (for the program above, enter numbers, then
  `-1` to finish);
- **Ctrl+S** — save; the editor also autosaves locally in the browser;
- Built-in examples (running total, count vowels, maximum function, copy
  text file) load with one click;
- Themes: `Studio Dark` and a warm `Ivory Gold` light theme.

### 4. Where do file operations go?

Pseudocode statements such as `OPENFILE "FileA.txt" FOR WRITE` read and
write real files inside the **workspace folder** chosen at server start
(default `ide/workspace/`). The IDE top bar shows the workspace, lets you
switch it, and can reveal the folder in your file explorer.

### 5. Command line (without the IDE)

```bash
python compiler.py        # interactive: paste pseudocode, then END on its own line
python -m unittest test_ide_runner test_file_handling   # IDE & file-handling tests
python check_architecture.py                            # module boundary check
```

### 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `Address already in use` | Use another port: `python -m ide.server --port 9000` |
| Garbled console output / encoding errors on Windows | Run with `PYTHONIOENCODING=utf-8`, or use Windows Terminal |
| Editor is a plain textbox | Monaco CDN unreachable (offline); features still work — refresh once online |
| No code completion | Expected: the completion engine is not distributed (Disclaimer, item 5) |
| `ModuleNotFoundError: ide` | You must run `python -m ide.server` from the **repository root** |

### 7. Security boundaries (local use only)

- The server binds to `127.0.0.1` (loopback) only — **do not expose it to
  a LAN or the public internet**;
- "Run" executes the generated Python in a separate `python -I -u` child
  process with a 3-second deadline, stdin/stdout quotas, and restricted
  builtins — but it is **not** an OS-level sandbox for hostile code. Run
  only pseudocode you trust.

---

## Disclaimer

**Please read in full. Using, copying, or distributing this repository
constitutes acknowledgement of all terms below.**

1. **Contact & rights concerns.**
   For any questions, concerns, or complaints — including any claim that
   content in this repository infringes your rights — email
   **<pseudocode-translator@protonmail.com>** (or open a GitHub issue).
   Matters will be reviewed and addressed promptly, and material will be
   corrected or removed as appropriate.

2. **Unofficial; no affiliation.**
   This is an independent, **student-built educational open project**. It
   is not affiliated with, sponsored by, authorised by, or endorsed by
   Cambridge University Press & Assessment, Cambridge Assessment
   International Education (CAIE), Cambridge International Education, the
   University of Cambridge Local Examinations Syndicate (UCLES), Microsoft
   Corporation, Anysphere, Inc., jsDelivr, or any other organisation named
   in this repository. Names and trademarks such as "CAIE", "Cambridge",
   "IGCSE", and subject codes (e.g. 9618, 0478) are used **nominatively**,
   solely to indicate compatibility and academic context; all rights remain
   with their respective owners.

3. **Not an official language definition.**
   This compiler's treatment of "CAIE-style pseudocode" is an
   **independent engineering implementation**, intended for learning about
   programming languages and compilers. It is **not** a substitute for,
   interpretation of, or authority on any syllabus, mark scheme, or
   official pseudocode guide. Official publications prevail; the author
   accepts no responsibility for academic consequences of relying on this
   tool.

4. **No third-party copyrighted material.**
   This repository **does not contain or distribute** any Cambridge past
   papers, mark schemes, syllabuses, official pseudocode guides,
   textbooks, or any other third-party copyrighted material. Every
   pseudocode example in this repository was written originally for this
   project. Please do not upload, link to, or request any copyrighted
   examination material in issues, pull requests, or discussions; such
   content will be removed.

5. **Experimental completion engine not distributed.**
   An **experimental** next-token completion engine (token-category
   trigram fused with parser legality signals) was researched during
   development. Because its training corpus involved third-party
   copyrighted material that cannot lawfully be redistributed, the engine
   and all of its corpora and evaluation data have been **physically
   removed** from the public repository and are **not available on
   request**. The public IDE runs in compiler-only mode and returns an
   explicit disabled response from `/api/completions`. The internal
   regression test harness used during development is likewise not
   distributed, for the same reason; the tests retained here (IDE service
   and file handling) are built entirely on original example programs.

6. **Provided "AS IS".**
   THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTY
   OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
   IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
   PURPOSE, AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
   COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY
   ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR ITS USE.

7. **Local tool; use at your own risk.**
   The IDE is designed for localhost use on your own machine (see
   "Security boundaries" above). Deploying it as a public-facing service,
   using it in production, or running untrusted code is outside its design
   intent and entirely at the user's own risk.

Supplementary statements: [`NOTICE.md`](NOTICE.md) (purpose, design
references, and attribution) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) (third-party software
licences).

---

## Project Structure

| Path | Role |
|---|---|
| `lexer.py` / `parser.py` / `codegen.py` / `compiler.py` | Compiler core (lexing → parsing/AST → Python generation) |
| `errors.py` / `tokens.py` / `ast_nodes.py` / `symbols.py` | Diagnostics, token, and AST data definitions |
| `ide/` | Local IDE: Monaco front end + zero-dependency HTTP server + restricted runner |
| `test_ide_runner.py` / `test_file_handling.py` | IDE service and file-statement tests |
| `check_architecture.py` | Static module-dependency boundary check (enforced in CI) |
| `lexgen.py` / `regex_lexer.py` | Lexer-design comparison experiments (research code) |
| `docs/` | Technical documents (lexer comparison, non-regularity argument) |

## License

**All rights reserved** for now — no open-source license has been chosen
yet. Reading and learning are welcome; for copying, modification, or
redistribution, please contact the maintainer first
(<pseudocode-translator@protonmail.com> or a GitHub issue). Third-party
component licences (Monaco Editor, MIT) are listed in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
