"""
基于 AST 的 Python 代码生成器。
"""

from .tokens import TokenType
from .ast_nodes import (
    ProgramNode, DeclarationNode, AssignmentNode, InputNode, OutputNode,
    IfNode, ForNode, WhileNode, RepeatNode,
    IdentifierNode, ArrayAccessNode,
    IntegerLiteralNode, RealLiteralNode, StringLiteralNode, BooleanLiteralNode,
    BinaryOpNode, UnaryOpNode,
)

# 中文注释：该处为编译器实现说明。

class PythonCodeGenerator:
    def __init__(self):
        self.indent_level = 0
        self.python_code = []
        self.declared_variables = {}
        # 中文注释：该处为编译器实现说明。
        self.array_metadata = {}

    def _indent(self):
        return "    " * self.indent_level

    def _add_line(self, line):
        self.python_code.append(self._indent() + line)

    def generate(self, program_node: ProgramNode):
        if not program_node: return "# Error during parsing. No Python code generated."
        self.visit(program_node)
        return "\n".join(self.python_code)

    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_ProgramNode(self, node: ProgramNode):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_DeclarationNode(self, node: DeclarationNode):
        var_name = self.visit(node.identifier)
        self.declared_variables[var_name] = {"type": node.type_name, "array_spec": node.array_spec}
        
        if node.type_name == "INTEGER":
            self._add_line(f"{var_name} = 0")
        elif node.type_name == "REAL":
            self._add_line(f"{var_name} = 0.0")
        elif node.type_name == "STRING":
            self._add_line(f"{var_name} = \"\"")
        elif node.type_name == "BOOLEAN":
            self._add_line(f"{var_name} = False")
        elif node.type_name == "ARRAY":
            item_type, default_val = "INTEGER", "0"
            if node.array_spec:
                item_type = node.array_spec.get("item_type", "INTEGER")
                if item_type == "REAL": default_val = "0.0"
                elif item_type == "STRING": default_val = "\"\""
                elif item_type == "BOOLEAN": default_val = "False"

            low_bound = node.array_spec.get("low_bound")
            high_bound = node.array_spec.get("high_bound")

            if isinstance(low_bound, IntegerLiteralNode) and isinstance(high_bound, IntegerLiteralNode):
                low_val = low_bound.value
                high_val = high_bound.value
                size = high_val - low_val + 1
                self._add_line(f"# Simulating fixed-size array {var_name}[{low_val}:{high_val}]")
                self._add_line(f"{var_name} = [{default_val}] * {size}")
                # 中文注释：该处为编译器实现说明。
                self.array_metadata[var_name] = {"low_bound": low_val}
            else: #中文注释：该处为编译器实现说明。
                 self._add_line(f"{var_name} = [] #中文注释：该处为编译器实现说明。
        else:
            self._add_line(f"{var_name} = None #中文注释：该处为编译器实现说明。

    def visit_AssignmentNode(self, node: AssignmentNode):
        target = self.visit(node.target)
        value = self.visit(node.value)
        self._add_line(f"{target} = {value}")

    def visit_InputNode(self, node: InputNode):
        # 中文注释：该处为编译器实现说明。
        var_name = self.visit(node.identifier)
        var_info = self.declared_variables.get(var_name, {"type": "STRING"})
        
        default_val = "\"<INPUT>\""
        if var_info["type"] == "INTEGER": default_val = "0"
        elif var_info["type"] == "REAL": default_val = "0.0"
        elif var_info["type"] == "BOOLEAN": default_val = "False"
        
        self._add_line(f"# INPUT replaced with a default for GUI execution")
        self._add_line(f"{var_name} = {default_val}")

    def visit_OutputNode(self, node: OutputNode):
        py_exprs = [self.visit(expr) for expr in node.expressions]
        self._add_line(f"print({', '.join(py_exprs)})")

    def visit_IfNode(self, node: IfNode):
        condition = self.visit(node.condition)
        self._add_line(f"if {condition}:")
        self.indent_level += 1
        if not node.then_block: self._add_line("pass")
        for stmt in node.then_block:
            self.visit(stmt)
        self.indent_level -= 1
        
        if node.else_block:
            self._add_line(f"else:")
            self.indent_level += 1
            if not node.else_block: self._add_line("pass")
            for stmt in node.else_block:
                self.visit(stmt)
            self.indent_level -= 1
    
    def visit_ForNode(self, node: ForNode):
        var_name = self.visit(node.variable)
        start_val = self.visit(node.start_expr)
        end_val = self.visit(node.end_expr)
        
        if node.step_expr:
            step_val = self.visit(node.step_expr)
            self._add_line(f"_step = {step_val}")
            self._add_line(f"_end = {end_val}")
            self._add_line(f"for {var_name} in range({start_val}, _end + (1 if _step > 0 else -1), _step):")
        else:
            self._add_line(f"for {var_name} in range({start_val}, {end_val} + 1):")
        
        self.indent_level += 1
        if not node.body: self._add_line("pass")
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

    def visit_WhileNode(self, node: WhileNode):
        condition = self.visit(node.condition)
        self._add_line(f"while {condition}:")
        self.indent_level += 1
        if not node.body: self._add_line("pass")
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

    def visit_RepeatNode(self, node: RepeatNode):
        self._add_line(f"while True:")
        self.indent_level += 1
        if not node.body: self._add_line("pass")
        for stmt in node.body:
            self.visit(stmt)
        condition = self.visit(node.condition)
        self._add_line(f"if {condition}:")
        self.indent_level += 1
        self._add_line(f"break")
        self.indent_level -= 2

    def visit_IdentifierNode(self, node: IdentifierNode):
        return node.name

    def visit_ArrayAccessNode(self, node: ArrayAccessNode):
        array_name = self.visit(node.identifier)
        index_py = self.visit(node.index_expr)
        
        # 中文注释：该处为编译器实现说明。
        offset = 1 #中文注释：该处为编译器实现说明。
        if array_name in self.array_metadata:
            offset = self.array_metadata[array_name].get("low_bound", 1)

        return f"{array_name}[({index_py}) - {offset}]"

    def visit_IntegerLiteralNode(self, node: IntegerLiteralNode):
        return str(node.value)

    def visit_RealLiteralNode(self, node: RealLiteralNode):
        return str(node.value)

    def visit_StringLiteralNode(self, node: StringLiteralNode):
        return repr(node.value)

    def visit_BooleanLiteralNode(self, node: BooleanLiteralNode):
        return "True" if node.value else "False"

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_map = {
            TokenType.PLUS: "+", TokenType.MINUS: "-", TokenType.MULTIPLY: "*",
            TokenType.DIVIDE: "/", TokenType.KEYWORD_MOD: "%", TokenType.KEYWORD_DIV: "//",
            TokenType.EQUALS: "==", TokenType.NOT_EQUALS: "!=",
            TokenType.LESS_THAN: "<", TokenType.LESS_EQUAL: "<=",
            TokenType.GREATER_THAN: ">", TokenType.GREATER_EQUAL: ">=",
            TokenType.KEYWORD_AND: "and", TokenType.KEYWORD_OR: "or"
        }
        py_op = op_map.get(node.op_token.type, f"#?{node.op_token.value}?#")
        return f"({left} {py_op} {right})"

    def visit_UnaryOpNode(self, node: UnaryOpNode):
        operand = self.visit(node.operand)
        if node.op_token.type == TokenType.KEYWORD_NOT:
            return f"(not {operand})"
        elif node.op_token.type == TokenType.MINUS:
            return f"(-{operand})"
        return f"#?{node.op_token.value}?#({operand})"
    

# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。

