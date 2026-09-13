# qq-agent — the compiler as an AI-agent tool on QQ

This directory contains the agent-side integration that exposes the pseudocode
compiler to students over QQ: a student sends CAIE pseudocode (typed text **or
a photo of it**) to a QQ bot, and gets back compile diagnostics, the generated
Python, and — after supplying test inputs — the execution result.

This is the deployment described as "wrapped the translator as a tool for an
AI agent". It ran as a private beta for classmates; these are the actual files
from that deployment, with credentials and machine-specific paths removed.

## Architecture

```text
QQ (official bot open platform, api.sgroup.qq.com + WebSocket gateway)
  └─ CoPaw / QwenPaw agent runtime  (fork: daliu858/CoPaw)
        └─ agent profile "PseudoCheck"  (AGENTS.md + SOUL.md + SKILL.md, this dir)
              └─ write_file("input_code.txt") → execute_shell_command("python run_compiler.py")
                    └─ compiler_tool.py  →  from compiler import compile_pseudocode ...
                          └─ this repository's compiler (lexer → parser → codegen)
```

- **`compiler_tool.py`** — CLI wrapper around the compiler. Returns one JSON
  object with `success / errors / warnings / python_code / input_vars /
  callable_info / action`, plus an `INSTRUCTION` field that tells the LLM what
  it must do next (e.g. *stop and ask the user for test values* when the code
  declares `INPUT` variables or is a standalone `FUNCTION`/`PROCEDURE`).
  Driving the LLM through a machine-checked `action` state instead of prose is
  what keeps the bot's behaviour predictable.
- **`run_compiler.py`** — file-based entry point (`input_code.txt` →
  `compiler_tool.py`), used instead of passing code on the command line to
  avoid shell-escaping issues; tolerant of several text encodings, since the
  file is written by the agent.
- **`AGENTS.md` / `SOUL.md`** — the "PseudoCheck" persona: absolute rules
  (always call the tool, never inline compiler logic, always answer in
  English), the decision tree over the tool's `action` field, and the 5-step
  image path (OCR by a multimodal model → show extracted code → write file →
  compile → follow decision tree).
- **`skills/pseudocode_compiler/SKILL.md`** — the custom skill definition
  registered in the agent runtime.
- **`config.example.qq.json`** — the QQ channel config shape with placeholder
  credentials.

## Running it yourself

1. Install [CoPaw](https://github.com/agentscope-ai/CoPaw) (the deployment
   used the fork
   [daliu858/CoPaw@feat/qq-ack-message](https://github.com/daliu858/CoPaw/tree/feat/qq-ack-message),
   which adds a configurable instant acknowledgement message for QQ so
   students see "⏳ Processing..." immediately).
2. Register a bot at the QQ open platform and fill `app_id` /
   `client_secret` into your CoPaw config (see `config.example.qq.json`).
   Configure any OpenAI-compatible multimodal model provider for image input.
3. Copy this directory's files into the agent workspace; set
   `PSEUDOCODE_COMPILER_ROOT` to your clone of this repository (or keep the
   default, which resolves to the repository root).

## Honest limitations

- `compiler_tool.py` executes the generated Python with `exec()` in the tool
  process, restricted only by pre-injected fake `input()` and stdout capture —
  it is **not** the resource-bounded sandbox used by the local IDE
  (`ide/runner.py`). It was acceptable for a supervised beta among classmates;
  a public deployment should route execution through the IDE runner instead.
- Conversation logs, media, credentials and the runtime state of the real
  deployment are deliberately not part of this repository.
