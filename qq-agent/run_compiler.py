"""Helper: read input_code.txt, call compiler_tool.py, print result."""
import subprocess
import sys
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

code_file = "input_code.txt"
try:
    raw = open(code_file, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "utf-16", "gbk", "latin-1"):
        try:
            code = raw.decode(enc)
            break
        except (UnicodeDecodeError, ValueError):
            continue
    else:
        code = raw.decode("latin-1")
    code = code.replace("\x00", "").strip()
except FileNotFoundError:
    print(json.dumps({"success": False, "error": f"{code_file} not found. Write pseudocode there first."}))
    sys.exit(1)

args = ["python", "compiler_tool.py", code]

if len(sys.argv) > 1:
    args += sys.argv[1:]

env = dict(__import__("os").environ)
env["PYTHONIOENCODING"] = "utf-8"
result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
