"""Python code generation stage.

`PythonCodeGenerator` consumes an AST and emits Python source while collecting
code-generation diagnostics.
"""
from errors import ErrorSeverity, CompileError
from tokens import TokenType
from symbols import SymbolInfo
from ast_nodes import (
    ASTNode, ProgramNode, DeclarationNode, ConstantNode, AssignmentNode,
    InputNode, OutputNode, OpenFileNode, ReadFileNode, WriteFileNode,
    CloseFileNode, SeekNode, GetRecordNode, PutRecordNode, IfNode, CaseBranch,
    CaseNode, ForNode, WhileNode, RepeatNode, ProcedureNode, FunctionDefNode,
    CallNode, ReturnNode, RecordTypeNode, EnumTypeNode, PointerTypeNode,
    SetTypeNode, DefineNode, ClassNode, ExpressionStatementNode, ExpressionNode,
    IdentifierNode, ArrayAccessNode, DotAccessNode, FunctionCallNode,
    NewExpressionNode, IntegerLiteralNode, RealLiteralNode, StringLiteralNode,
    CharLiteralNode, BooleanLiteralNode, BinaryOpNode, UnaryOpNode,
)


# ─── Python Code Generator ──────────────────────────────────────────────
# ─── Python Code Generator ──────────────────────────────────────────────
_CAIE_FILE_RUNTIME = '''
import json as _json

class _CaieFiles:
    _MODES = {"READ", "WRITE", "APPEND", "RANDOM"}

    def __init__(self):
        self._handles = {}
        self._random = {}
        self._seek = {}
        self._modes = {}
        self._canon = {}

    def _key(self, ident):
        text = str(ident).replace("\\\\", "/")
        parts = [part for part in text.split("/") if part not in ("", ".")]
        if (not parts or ".." in parts or ":" in text[:3]
                or text.startswith("/") or len(parts) != 1):
            raise OSError(
                "CAIE filenames must be a single file in the workspace folder"
            )
        name = parts[0]
        folded = name.casefold()
        return self._canon.setdefault(folded, name)

    def openfile(self, ident, mode):
        name = self._key(ident)
        mode = str(mode).upper()
        if mode not in self._MODES:
            raise ValueError("file mode must be READ, WRITE, APPEND, or RANDOM")
        if name in self._modes:
            self.closefile(ident)
        self._modes[name] = mode
        if mode == "RANDOM":
            records = []
            try:
                with open(name, "r", encoding="utf-8", newline="") as fh:
                    raw = fh.read()
                if raw.strip():
                    loaded = _json.loads(raw)
                    if isinstance(loaded, list):
                        records = loaded
            except FileNotFoundError:
                records = []
            self._random[name] = records
            self._seek[name] = 1
            return
        py_mode = {"READ": "r", "WRITE": "w", "APPEND": "a"}[mode]
        self._handles[name] = open(name, py_mode, encoding="utf-8", newline="")

    def closefile(self, ident):
        name = self._key(ident)
        if name not in self._modes:
            raise OSError("file is not open")
        handle = self._handles.pop(name, None)
        if handle is not None:
            handle.close()
        records = self._random.pop(name, None)
        if records is not None:
            with open(name, "w", encoding="utf-8", newline="") as fh:
                _json.dump(records, fh, ensure_ascii=False)
        self._seek.pop(name, None)
        self._modes.pop(name, None)

    def readfile(self, ident):
        handle = self._require_seq(ident, {"READ"})
        line = handle.readline()
        if line.endswith("\\n"):
            line = line[:-1]
        if line.endswith("\\r"):
            line = line[:-1]
        return line

    def writefile(self, ident, data):
        handle = self._require_seq(ident, {"WRITE", "APPEND"})
        handle.write(str(data) + "\\n")
        handle.flush()

    def eof(self, ident):
        handle = self._require_seq(ident, {"READ"})
        position = handle.tell()
        chunk = handle.read(1)
        handle.seek(position)
        return chunk == ""

    def seek(self, ident, address):
        name = self._key(ident)
        if self._modes.get(name) != "RANDOM":
            raise OSError("SEEK requires a file opened FOR RANDOM")
        address = int(address)
        if address < 1:
            raise OSError("CAIE SEEK address is 1-based")
        self._seek[name] = address

    def getrecord(self, ident, target=None):
        name = self._key(ident)
        records = self._require_random(name)
        index = self._seek[name] - 1
        record = records[index] if 0 <= index < len(records) else None
        if target is not None and hasattr(target, "__dict__") and isinstance(record, dict):
            for field, value in record.items():
                setattr(target, field, value)
            return target
        return record if record is not None else target

    def putrecord(self, ident, value):
        name = self._key(ident)
        records = self._require_random(name)
        index = self._seek[name] - 1
        if index < 0:
            raise OSError("CAIE SEEK address is 1-based")
        payload = dict(value.__dict__) if hasattr(value, "__dict__") else value
        while len(records) <= index:
            records.append(None)
        records[index] = payload

    def _require_seq(self, ident, modes):
        name = self._key(ident)
        if self._modes.get(name) not in modes:
            raise OSError("file is not open for this operation")
        return self._handles[name]

    def _require_random(self, name):
        if self._modes.get(name) != "RANDOM":
            raise OSError("random file operation requires OPENFILE FOR RANDOM")
        return self._random[name]

_caie_files = _CaieFiles()
'''.lstrip()


class PythonCodeGenerator:
    _BUILTINS = {
        "LENGTH": lambda a: f"len({a[0]})",
        "RIGHT":  lambda a: f"({a[0]})[len({a[0]})-({a[1]}):]",
        "MID":    lambda a: f"({a[0]})[({a[1]})-1:({a[1]})-1+({a[2]})]",
        "LCASE":  lambda a: f"({a[0]}).lower()",
        "UCASE":  lambda a: f"({a[0]}).upper()",
        "INT":    lambda a: f"int({a[0]})",
        "RAND":   lambda a: f"__import__('random').random()*({a[0]})",
    }

    _TYPE_DEFAULTS = {
        "INTEGER": "0", "REAL": "0.0", "STRING": '""',
        "BOOLEAN": "False", "CHAR": "''", "DATE": '""',
    }

    def __init__(self, symbol_table=None):
        self.indent_level = 0
        self.python_code = []
        # Shallow-copy the handed-over table: the generator reads the parser's
        # global symbols but must not alias (and thus never mutates) the
        # parser's own dict.
        self.scope_stack = [dict(symbol_table) if symbol_table is not None else {}]
        self.array_metadata = {}
        self._class_fields = set()
        self._class_types = set()
        self._class_registry = {}
        self._proc_registry = {}
        self.errors = []
        self._uses_files = False

    def _push_scope(self):
        self.scope_stack.append({})

    def _pop_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def _lookup(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def _declare(self, name, info):
        self.scope_stack[-1][name] = info

    def _indent(self):
        return "    " * self.indent_level

    def _add_line(self, line):
        self.python_code.append(self._indent() + line)

    def _default(self, type_name):
        return self._TYPE_DEFAULTS.get(type_name, "None")

    def _check_declared(self, var_name, token=None):
        if self._lookup(var_name) is None and var_name not in self._class_fields:
            line = token.line if token is not None else 0
            column = token.column if token is not None else 0
            self.errors.append(CompileError(
                ErrorSeverity.ERROR, line, column,
                f"Variable '{var_name}' is used but has not been declared.",
                suggestion=f"Add 'DECLARE {var_name} : <type>' before using it."))
            return False
        return True

    def generate(self, program_node):
        if not program_node:
            return "# Error during parsing. No Python code generated."
        self.visit(program_node)
        body = "\n".join(self.python_code)
        if self._uses_files:
            return _CAIE_FILE_RUNTIME + "\n" + body
        return body

    def visit(self, node):
        method = 'visit_' + type(node).__name__
        return getattr(self, method, self._generic_visit)(node)

    def _generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    # ── program ──
    def visit_ProgramNode(self, node):
        for s in node.statements:
            self.visit(s)

    # ── declarations ──
    def visit_DeclarationNode(self, node):
        var = self.visit(node.identifier)
        if node.type_name == "ARRAY" and node.array_spec:
            self._declare(var, SymbolInfo(type="ARRAY", array_spec=node.array_spec,
                                          item_type=node.array_spec.get("item_type", "INTEGER")))
        else:
            self._declare(var, SymbolInfo(type=node.type_name))
        if node.type_name == "ARRAY" and node.array_spec:
            spec = node.array_spec
            item_t = spec.get("item_type", "INTEGER")
            dv = self._default(item_t)
            if spec.get("is_2d"):
                l1, h1 = spec["low_bound"], spec["high_bound"]
                l2, h2 = spec["low_bound2"], spec["high_bound2"]
                if all(isinstance(x, IntegerLiteralNode) for x in (l1, h1, l2, h2)):
                    s1 = h1.value - l1.value + 1
                    s2 = h2.value - l2.value + 1
                    self._add_line(f"{var} = [[{dv} for _ in range({s2})] for _ in range({s1})]")
                    self.array_metadata[var] = {"low_bound": l1.value, "low_bound2": l2.value}
                else:
                    self._add_line(f"{var} = []")
            else:
                l1, h1 = spec["low_bound"], spec["high_bound"]
                if isinstance(l1, IntegerLiteralNode) and isinstance(h1, IntegerLiteralNode):
                    sz = h1.value - l1.value + 1
                    self._add_line(f"{var} = [{dv}] * {sz}")
                    self.array_metadata[var] = {"low_bound": l1.value}
                else:
                    self._add_line(f"{var} = []")
        else:
            dv = self._default(node.type_name)
            if dv == "None" and node.type_name not in ("", "ARRAY"):
                if node.type_name in self._class_types:
                    self._add_line(f"{var} = None")
                else:
                    self._add_line(f"{var} = {node.type_name}()")
            else:
                self._add_line(f"{var} = {dv}")

    def visit_ConstantNode(self, node):
        name = self.visit(node.identifier)
        self._declare(name, SymbolInfo(type="CONSTANT"))
        val = self.visit(node.value)
        self._add_line(f"{name} = {val}")

    def visit_ExpressionStatementNode(self, node):
        self._add_line(self.visit(node.expression))

    # ── statements ──
    def visit_AssignmentNode(self, node):
        if isinstance(node.target, IdentifierNode):
            self._check_declared(node.target.name, node.target.token)
        elif isinstance(node.target, ArrayAccessNode):
            self._check_declared(node.target.identifier.name, node.target.identifier.token)
        target = self.visit(node.target)
        value = self.visit(node.value)
        self._add_line(f"{target} = {value}")

    def visit_InputNode(self, node):
        var = self.visit(node.identifier)
        self._check_declared(var, getattr(node.identifier, 'token', None))
        info = self._lookup(var)
        type_name = info.type if info is not None else "STRING"
        cast = {"INTEGER": "int", "REAL": "float"}.get(type_name)
        prompt = f"'Enter {var} ({type_name}): '"
        if cast:
            self._add_line(f"{var} = {cast}(input({prompt}))")
        else:
            self._add_line(f"{var} = input({prompt})")

    def visit_OutputNode(self, node):
        for e in node.expressions:
            if isinstance(e, IdentifierNode):
                self._check_declared(e.name, e.token)
            elif isinstance(e, ArrayAccessNode):
                self._check_declared(e.identifier.name, e.identifier.token)
        parts = [self.visit(e) for e in node.expressions]
        self._add_line(f"print({', '.join(parts)})")

    def _file_ident_py(self, node):
        self._uses_files = True
        if isinstance(node, IdentifierNode) and self._lookup(node.name) is None:
            return repr(node.name)
        return self.visit(node)

    def visit_OpenFileNode(self, node):
        ident = self._file_ident_py(node.file_ident)
        self._add_line(f"_caie_files.openfile({ident}, {node.mode!r})")

    def visit_ReadFileNode(self, node):
        ident = self._file_ident_py(node.file_ident)
        if isinstance(node.target, IdentifierNode):
            self._check_declared(node.target.name, node.target.token)
        elif isinstance(node.target, ArrayAccessNode):
            self._check_declared(node.target.identifier.name, node.target.identifier.token)
        target = self.visit(node.target)
        self._add_line(f"{target} = _caie_files.readfile({ident})")

    def visit_WriteFileNode(self, node):
        ident = self._file_ident_py(node.file_ident)
        data = self.visit(node.data)
        self._add_line(f"_caie_files.writefile({ident}, {data})")

    def visit_CloseFileNode(self, node):
        ident = self._file_ident_py(node.file_ident)
        self._add_line(f"_caie_files.closefile({ident})")

    def visit_SeekNode(self, node):
        ident = self._file_ident_py(node.file_ident)
        address = self.visit(node.address)
        self._add_line(f"_caie_files.seek({ident}, {address})")

    def visit_GetRecordNode(self, node):
        ident = self._file_ident_py(node.file_ident)
        if isinstance(node.target, IdentifierNode):
            self._check_declared(node.target.name, node.target.token)
        target = self.visit(node.target)
        self._add_line(f"{target} = _caie_files.getrecord({ident}, {target})")

    def visit_PutRecordNode(self, node):
        ident = self._file_ident_py(node.file_ident)
        value = self.visit(node.value)
        self._add_line(f"_caie_files.putrecord({ident}, {value})")

    def visit_IfNode(self, node):
        self._add_line(f"if {self.visit(node.condition)}:")
        self.indent_level += 1
        if not node.then_block:
            self._add_line("pass")
        for s in node.then_block:
            self.visit(s)
        self.indent_level -= 1
        if node.else_block is not None:
            self._add_line("else:")
            self.indent_level += 1
            if not node.else_block:
                self._add_line("pass")
            for s in node.else_block:
                self.visit(s)
            self.indent_level -= 1

    def visit_CaseNode(self, node):
        expr = self.visit(node.expr)
        cvar = f"_case_{expr}"
        self._add_line(f"{cvar} = {expr}")
        first = True
        for br in node.branches:
            val = self.visit(br.value)
            if br.range_end is not None:
                end = self.visit(br.range_end)
                cond = f"{val} <= {cvar} <= {end}"
            else:
                cond = f"{cvar} == {val}"
            kw = "if" if first else "elif"
            self._add_line(f"{kw} {cond}:")
            self.indent_level += 1
            if not br.statements:
                self._add_line("pass")
            for s in br.statements:
                self.visit(s)
            self.indent_level -= 1
            first = False
        if node.otherwise_block is not None:
            self._add_line("else:")
            self.indent_level += 1
            if not node.otherwise_block:
                self._add_line("pass")
            for s in node.otherwise_block:
                self.visit(s)
            self.indent_level -= 1

    def visit_ForNode(self, node):
        var = self.visit(node.variable)
        self._check_declared(var, getattr(node.variable, 'token', None))
        start = self.visit(node.start_expr)
        end = self.visit(node.end_expr)
        if node.step_expr:
            step = self.visit(node.step_expr)
            self._add_line(f"_step = {step}")
            self._add_line(f"_end = {end}")
            self._add_line(f"for {var} in range({start}, _end + (1 if _step > 0 else -1), _step):")
        else:
            self._add_line(f"for {var} in range({start}, {end} + 1):")
        self.indent_level += 1
        if not node.body:
            self._add_line("pass")
        for s in node.body:
            self.visit(s)
        self.indent_level -= 1

    def visit_WhileNode(self, node):
        self._add_line(f"while {self.visit(node.condition)}:")
        self.indent_level += 1
        if not node.body:
            self._add_line("pass")
        for s in node.body:
            self.visit(s)
        self.indent_level -= 1

    def visit_RepeatNode(self, node):
        self._add_line("while True:")
        self.indent_level += 1
        if not node.body:
            self._add_line("pass")
        for s in node.body:
            self.visit(s)
        cond = self.visit(node.condition)
        self._add_line(f"if {cond}:")
        self.indent_level += 1
        self._add_line("break")
        self.indent_level -= 2

    # ── procedures / functions ──
    def visit_ProcedureNode(self, node):
        self._proc_registry[node.name] = node.params
        params = ", ".join(p["name"] for p in node.params)
        self._add_line(f"def {node.name}({params}):")
        self.indent_level += 1
        self._push_scope()
        for p in node.params:
            self._declare(p["name"], SymbolInfo(type=p.get("type", "ANY"),
                                                pass_by=p.get("pass_by", "BYVAL")))
        if not node.body:
            self._add_line("pass")
        for s in node.body:
            self.visit(s)
        self._pop_scope()
        self.indent_level -= 1
        self._add_line("")

    def visit_FunctionDefNode(self, node):
        self._proc_registry[node.name] = node.params
        params = ", ".join(p["name"] for p in node.params)
        self._add_line(f"def {node.name}({params}):")
        self.indent_level += 1
        self._push_scope()
        for p in node.params:
            self._declare(p["name"], SymbolInfo(type=p.get("type", "ANY"),
                                                pass_by=p.get("pass_by", "BYVAL")))
        if not node.body:
            self._add_line("pass")
        for s in node.body:
            self.visit(s)
        self._pop_scope()
        self.indent_level -= 1
        self._add_line("")

    def visit_CallNode(self, node):
        base_name = node.name.split(".")[0] if "." in node.name else node.name
        proc_info = self._proc_registry.get(base_name)
        has_byref = proc_info and any(p.get("pass_by") == "BYREF" for p in proc_info)
        if has_byref:
            ref_vars = []
            arg_strs = []
            for i, arg in enumerate(node.args):
                is_byref = i < len(proc_info) and proc_info[i].get("pass_by") == "BYREF"
                if is_byref and isinstance(arg, IdentifierNode):
                    ref_name = f"_ref_{node.name}_{i}"
                    self._add_line(f"{ref_name} = [{arg.name}]")
                    arg_strs.append(ref_name)
                    ref_vars.append((arg.name, ref_name))
                else:
                    arg_strs.append(self.visit(arg))
            self._add_line(f"{node.name}({', '.join(arg_strs)})")
            for var_name, ref_name in ref_vars:
                self._add_line(f"{var_name} = {ref_name}[0]")
        else:
            args = ", ".join(self.visit(a) for a in node.args)
            self._add_line(f"{node.name}({args})")

    def visit_ReturnNode(self, node):
        self._add_line(f"return {self.visit(node.value)}")

    # ── type definitions ──
    def visit_RecordTypeNode(self, node):
        self._add_line(f"class {node.name}:")
        self.indent_level += 1
        self._add_line("def __init__(self):")
        self.indent_level += 1
        if not node.fields:
            self._add_line("pass")
        for f in node.fields:
            fname = f.identifier.name
            self._add_line(f"self.{fname} = {self._default(f.type_name)}")
        self.indent_level -= 2
        self._add_line("")

    def visit_EnumTypeNode(self, node):
        for i, v in enumerate(node.values):
            self._add_line(f"{v} = {i}")

    def visit_PointerTypeNode(self, node):
        self._add_line(f"# Pointer type {node.name} = ^{node.base_type} (no direct Python equivalent)")

    def visit_SetTypeNode(self, node):
        self._add_line(f"# Set type {node.name} = SET OF {node.item_type}")

    def visit_DefineNode(self, node):
        vals = ", ".join(self.visit(v) for v in node.values)
        self._add_line(f"{node.name} = {{{vals}}}")

    # ── class ──
    def visit_ClassNode(self, node):
        self._class_types.add(node.name)
        parent_str = f"({node.parent})" if node.parent else ""
        self._add_line(f"class {node.name}{parent_str}:")
        self.indent_level += 1
        old_fields = self._class_fields
        self._class_fields = set()

        fields = []
        new_ctor = None
        other_methods = []
        init_stmts = []
        own_field_names = set()
        for mtype, access, member in node.members:
            if mtype == "field":
                fields.append(member)
                own_field_names.add(member.identifier.name)
            elif mtype == "method":
                if isinstance(member, ProcedureNode) and member.name == "NEW":
                    new_ctor = member
                else:
                    other_methods.append(member)
            elif mtype == "init_stmt":
                init_stmts.append(member)

        self._class_registry[node.name] = {
            "own_fields": own_field_names,
            "parent": node.parent,
        }
        self._class_fields = set(own_field_names)
        parent = node.parent
        while parent and parent in self._class_registry:
            self._class_fields |= self._class_registry[parent]["own_fields"]
            parent = self._class_registry[parent]["parent"]

        if fields or new_ctor or init_stmts:
            ctor_params = ""
            if new_ctor:
                ctor_params = ", ".join(p["name"] for p in new_ctor.params)
            ctor_params = f"self, {ctor_params}" if ctor_params else "self"
            self._add_line(f"def __init__({ctor_params}):")
            self.indent_level += 1
            if node.parent and not new_ctor:
                self._add_line("super().__init__()")
            for f in fields:
                fn = f.identifier.name
                self._add_line(f"self.{fn} = {self._default(f.type_name)}")
            for s in init_stmts:
                self.visit(s)
            if new_ctor:
                for s in new_ctor.body:
                    self.visit(s)
            if not fields and not init_stmts and (not new_ctor or not new_ctor.body):
                self._add_line("pass")
            self.indent_level -= 1

        for m in other_methods:
            self._generate_class_method(m)

        if not fields and not new_ctor and not other_methods and not init_stmts:
            self._add_line("pass")

        self.indent_level -= 1
        self._class_fields = old_fields
        self._add_line("")

    def _generate_class_method(self, method):
        if isinstance(method, ProcedureNode):
            params = ", ".join(p["name"] for p in method.params)
            params = f"self, {params}" if params else "self"
            self._add_line(f"def {method.name}({params}):")
        elif isinstance(method, FunctionDefNode):
            params = ", ".join(p["name"] for p in method.params)
            params = f"self, {params}" if params else "self"
            self._add_line(f"def {method.name}({params}):")
        self.indent_level += 1
        self._push_scope()
        for p in method.params:
            self._declare(p["name"], SymbolInfo(type=p.get("type", "ANY")))
        body = method.body if hasattr(method, 'body') else []
        if not body:
            self._add_line("pass")
        for s in body:
            self.visit(s)
        self._pop_scope()
        self.indent_level -= 1

    # ── expression visitors ──
    def visit_IdentifierNode(self, node):
        if self._class_fields and node.name in self._class_fields:
            return f"self.{node.name}"
        info = self._lookup(node.name)
        if info is not None and info.pass_by == "BYREF":
            return f"{node.name}[0]"
        return node.name

    def visit_ArrayAccessNode(self, node):
        arr = self.visit(node.identifier)
        idx = self.visit(node.index_expr)
        off = 1
        if arr in self.array_metadata:
            off = self.array_metadata[arr].get("low_bound", 1)
        if node.index_expr2 is not None:
            idx2 = self.visit(node.index_expr2)
            off2 = 1
            if arr in self.array_metadata:
                off2 = self.array_metadata[arr].get("low_bound2", 1)
            return f"{arr}[({idx}) - {off}][({idx2}) - {off2}]"
        return f"{arr}[({idx}) - {off}]"

    def visit_DotAccessNode(self, node):
        obj = self.visit(node.obj)
        field = node.field.name
        return f"{obj}.{field}"

    def visit_FunctionCallNode(self, node):
        args_py = [self.visit(a) for a in node.args]
        if isinstance(node.callee, IdentifierNode):
            name_upper = node.callee.name.upper()
            if name_upper == "EOF":
                self._uses_files = True
                if node.args:
                    ident = self._file_ident_py(node.args[0])
                    return f"_caie_files.eof({ident})"
                return "_caie_files.eof('')"
            builtin = self._BUILTINS.get(name_upper)
            if builtin:
                return builtin(args_py)
            return f"{node.callee.name}({', '.join(args_py)})"
        if isinstance(node.callee, DotAccessNode):
            obj_node = node.callee.obj
            method_name = node.callee.field.name
            if isinstance(obj_node, IdentifierNode) and obj_node.name == "super":
                py_method = "__init__" if method_name == "NEW" else method_name
                return f"super().{py_method}({', '.join(args_py)})"
            obj = self.visit(obj_node)
            return f"{obj}.{method_name}({', '.join(args_py)})"
        callee = self.visit(node.callee)
        return f"{callee}({', '.join(args_py)})"

    def visit_NewExpressionNode(self, node):
        args = ", ".join(self.visit(a) for a in node.args)
        return f"{node.class_name}({args})"

    def visit_IntegerLiteralNode(self, node):
        return str(node.value)

    def visit_RealLiteralNode(self, node):
        return str(node.value)

    def visit_StringLiteralNode(self, node):
        return repr(node.value)

    def visit_CharLiteralNode(self, node):
        return repr(node.value)

    def visit_BooleanLiteralNode(self, node):
        return "True" if node.value else "False"

    def visit_BinaryOpNode(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_map = {
            TokenType.PLUS: "+", TokenType.MINUS: "-",
            TokenType.MULTIPLY: "*", TokenType.DIVIDE: "/",
            TokenType.KEYWORD_MOD: "%", TokenType.KEYWORD_DIV: "//",
            TokenType.AMPERSAND: "+", TokenType.CARET: "**",
            TokenType.EQUALS: "==", TokenType.NOT_EQUALS: "!=",
            TokenType.LESS_THAN: "<", TokenType.LESS_EQUAL: "<=",
            TokenType.GREATER_THAN: ">", TokenType.GREATER_EQUAL: ">=",
            TokenType.KEYWORD_AND: "and", TokenType.KEYWORD_OR: "or",
        }
        py_op = op_map.get(node.op_token.type, f"#?{node.op_token.value}?#")
        return f"({left} {py_op} {right})"

    def visit_UnaryOpNode(self, node):
        operand = self.visit(node.operand)
        if node.op_token.type == TokenType.KEYWORD_NOT:
            return f"(not {operand})"
        if node.op_token.type == TokenType.MINUS:
            return f"(-{operand})"
        return f"#?{node.op_token.value}?#({operand})"
