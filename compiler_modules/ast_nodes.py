"""
抽象语法树节点定义。
"""

# 中文注释：该处为编译器实现说明。

# 中文注释：该处为编译器实现说明。
class ASTNode:
    pass

class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class DeclarationNode(ASTNode):
    def __init__(self, identifier, type_name, array_spec=None):
        self.identifier = identifier
        self.type_name = type_name
        self.array_spec = array_spec

class AssignmentNode(ASTNode):
    def __init__(self, target, value):
        self.target = target #中文注释：该处为编译器实现说明。
        self.value = value

class InputNode(ASTNode):
    def __init__(self, identifier):
        self.identifier = identifier

class OutputNode(ASTNode):
    def __init__(self, expressions):
        self.expressions = expressions

class IfNode(ASTNode):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class ForNode(ASTNode):
    def __init__(self, variable, start_expr, end_expr, step_expr, body):
        self.variable = variable
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.step_expr = step_expr
        self.body = body

class WhileNode(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class RepeatNode(ASTNode):
    def __init__(self, body, condition):
        self.body = body
        self.condition = condition

class ExpressionNode(ASTNode):
    pass

class IdentifierNode(ExpressionNode):
    def __init__(self, name, token):
        self.name = name
        self.token = token

# 中文注释：该处为编译器实现说明。
class ArrayAccessNode(ExpressionNode):
    def __init__(self, identifier, index_expr):
        self.identifier = identifier
        self.index_expr = index_expr

class IntegerLiteralNode(ExpressionNode):
    def __init__(self, value, token):
        self.value = value
        self.token = token

class RealLiteralNode(ExpressionNode):
    def __init__(self, value, token):
        self.value = value
        self.token = token

class StringLiteralNode(ExpressionNode):
    def __init__(self, value, token):
        self.value = value
        self.token = token

class BooleanLiteralNode(ExpressionNode):
    def __init__(self, value, token):
        self.value = value
        self.token = token

class BinaryOpNode(ExpressionNode):
    def __init__(self, left, op_token, right):
        self.left = left
        self.op_token = op_token
        self.right = right

class UnaryOpNode(ExpressionNode):
    def __init__(self, op_token, operand):
        self.op_token = op_token
        self.operand = operand


# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。

