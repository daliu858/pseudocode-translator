"""
NanoBot tool for CAIE pseudocode compilation and execution.

Usage:
  python compiler_tool.py "<pseudocode>"                          - Compile, analyze, auto-run if possible
  python compiler_tool.py "<pseudocode>" --inputs '{"x": "5"}'   - Compile and run with pre-injected inputs
"""
import sys
import json
import os
import io
import contextlib
from unittest.mock import patch as mock_patch

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Compiler location: $PSEUDOCODE_COMPILER_ROOT if set, else the repository
# root (this file lives in <repo>/qq-agent/).
_REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_COMPILER_ROOTS = tuple(
    p for p in (os.environ.get("PSEUDOCODE_COMPILER_ROOT"), _REPO_ROOT) if p
)
for _root in _COMPILER_ROOTS:
    if os.path.isfile(os.path.join(_root, "compiler.py")):
        sys.path.insert(0, _root)
        break
else:
    raise FileNotFoundError("compiler.py not found; update _COMPILER_ROOTS")
from compiler import compile_pseudocode, _detect_single_callable, ErrorSeverity, InputNode, OutputNode


def _find_input_vars(ast):
    found = []
    if ast is None:
        return found

    def _walk(node):
        if isinstance(node, InputNode):
            found.append(node.identifier.name)
            return
        for child in getattr(node, '__dict__', {}).values():
            if isinstance(child, list):
                for item in child:
                    if hasattr(item, '__dict__'):
                        _walk(item)
            elif hasattr(child, '__dict__'):
                _walk(child)

    for stmt in getattr(ast, 'statements', []):
        _walk(stmt)
    return found


def _has_output(ast):
    if ast is None:
        return False

    def _walk(node):
        if isinstance(node, OutputNode):
            return True
        for child in getattr(node, '__dict__', {}).values():
            if isinstance(child, list):
                for item in child:
                    if hasattr(item, '__dict__') and _walk(item):
                        return True
            elif hasattr(child, '__dict__') and _walk(child):
                return True
        return False

    for stmt in getattr(ast, 'statements', []):
        if _walk(stmt):
            return True
    return False


def _get_param_info(p):
    if isinstance(p, dict):
        return p.get("name", ""), p.get("type", "STRING")
    elif isinstance(p, (list, tuple)):
        return p[0], (p[1] if len(p) > 1 else "STRING")
    else:
        return getattr(p, "name", ""), getattr(p, "type_name", "STRING")


def _cast_param(value, type_name):
    t = str(type_name).upper()
    if t == "INTEGER":
        try:
            return str(int(value))
        except (ValueError, TypeError):
            return "0"
    elif t == "REAL":
        try:
            return str(float(value))
        except (ValueError, TypeError):
            return "0.0"
    elif t == "BOOLEAN":
        return "True" if str(value).upper() in ("TRUE", "1", "YES") else "False"
    elif t == "CHAR":
        return repr(str(value)[:1])
    else:
        return repr(str(value))


def _format_callable_params(params):
    result = []
    for p in params:
        if isinstance(p, dict):
            name = p.get("name", "")
            ptype = p.get("type", "STRING")
            mode = p.get("pass_by", "BYVAL")
        elif isinstance(p, (list, tuple)):
            name, ptype = p[0], (p[1] if len(p) > 1 else "STRING")
            mode = p[2] if len(p) > 2 else "BYVAL"
        else:
            name = getattr(p, "name", str(p))
            ptype = getattr(p, "type_name", "STRING")
            mode = getattr(p, "mode", "BYVAL")
        result.append({"name": str(name), "type": str(ptype), "mode": str(mode)})
    return result


def _execute(python_code, callable_info, input_values):
    exec_code = python_code

    if callable_info:
        name = callable_info["name"]
        params = callable_info["params"]
        if callable_info["is_function"]:
            args = ", ".join(
                _cast_param(input_values.get(pname, "0"), ptype)
                for pname, ptype in (_get_param_info(p) for p in params)
            )
            exec_code += f"\n_result_ = {name}({args})\nif _result_ is not None:\n    print(f'Return value: {{_result_}}')"
        else:
            args = ", ".join(
                _cast_param(input_values.get(pname, "0"), ptype)
                for pname, ptype in (_get_param_info(p) for p in params)
            )
            exec_code += f"\n{name}({args})"

    remaining_inputs = list(input_values.values())
    input_iter = iter(remaining_inputs)

    def fake_input(prompt=""):
        try:
            return next(input_iter)
        except StopIteration:
            return ""

    stdout_capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_capture), mock_patch('builtins.input', fake_input):
            exec(exec_code, {"__builtins__": __builtins__})
        output = stdout_capture.getvalue()
        return {
            "run_success": True,
            "output": output.strip() if output.strip() else "(no output)",
            "executed_code": exec_code,
        }
    except Exception as e:
        output = stdout_capture.getvalue()
        return {
            "run_success": False,
            "runtime_error": f"{type(e).__name__}: {e}",
            "partial_output": output.strip() if output.strip() else None,
            "executed_code": exec_code,
        }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No pseudocode provided"}, ensure_ascii=False))
        sys.exit(1)

    source = sys.argv[1]

    input_values = {}
    if "--inputs" in sys.argv:
        idx = sys.argv.index("--inputs")
        if idx + 1 < len(sys.argv):
            try:
                input_values = json.loads(sys.argv[idx + 1])
            except json.JSONDecodeError as e:
                print(json.dumps({"success": False, "error": f"Invalid --inputs JSON: {e}"}, ensure_ascii=False))
                sys.exit(1)

    tokens, ast, python_code, errors = compile_pseudocode(source)

    error_list = [{"line": e.line, "message": e.message}
                  for e in errors if e.severity == ErrorSeverity.ERROR]
    warning_list = [{"line": e.line, "message": e.message}
                    for e in errors if e.severity == ErrorSeverity.WARNING]

    input_vars = _find_input_vars(ast)
    has_out = _has_output(ast)
    callable_info = _detect_single_callable(ast)

    callable_desc = None
    if callable_info:
        callable_desc = {
            "name": callable_info["name"],
            "params": _format_callable_params(callable_info["params"]),
            "is_function": callable_info["is_function"],
            "return_type": callable_info.get("return_type"),
        }

    result = {
        "success": len(error_list) == 0,
        "errors": error_list,
        "warnings": warning_list,
        "python_code": python_code if len(error_list) == 0 else None,
        "has_input": len(input_vars) > 0,
        "input_vars": input_vars,
        "has_output": has_out,
        "is_callable": callable_info is not None,
        "callable_info": callable_desc,
    }

    if len(error_list) > 0:
        err_summary = "; ".join(f"Line {e['line']}: {e['message']}" for e in error_list)
        result["INSTRUCTION"] = (
            f"⚠️ SYNTAX ERRORS FOUND. Report these errors to the user and suggest fixes. "
            f"DO NOT attempt to run the code. Errors: {err_summary}"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    needs_input = len(input_vars) > 0 and not input_values
    needs_params = callable_info is not None and not input_values
    can_auto_run = (not needs_input and not needs_params) or input_values

    if can_auto_run:
        run_result = _execute(python_code, callable_info, input_values)
        result.update(run_result)
        result["action"] = "executed"
    elif needs_params:
        result["action"] = "need_params"
        params = callable_desc["params"]
        param_list = ", ".join(f'{p["name"]}({p["type"]})' for p in params)
        kind = "FUNCTION" if callable_desc["is_function"] else "PROCEDURE"
        result["INSTRUCTION"] = (
            f"⚠️ STOP! DO NOT show Python code or output yet. "
            f"The code defines a {kind} '{callable_desc['name']}' that requires test parameters. "
            f"You MUST immediately ask the user: 'Please provide test values for these parameters: {param_list}'. "
            f"After user replies, re-run with --inputs."
        )
    elif needs_input:
        result["action"] = "need_input"
        var_list = ", ".join(input_vars)
        result["INSTRUCTION"] = (
            f"⚠️ STOP! DO NOT show Python code or output yet. "
            f"The code has INPUT statements for: {var_list}. "
            f"You MUST immediately ask the user: 'Please provide values for these variables: {var_list}'. "
            f"After user replies, re-run with --inputs."
        )
    else:
        result["action"] = "compile_only"
 
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
