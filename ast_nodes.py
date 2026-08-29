"""抽象语法树（AST）节点定义。

纯数据类，不依赖 tokens / errors（节点只持有 Token 对象引用与字面值，
不引用 TokenType / CompileError 这两个类本身）。
AST 是 parser 与 code generator 之间的"通信契约"：parser 产出 AST，
code generator 消费 AST。两者不互相调用内部方法。
"""


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

class ConstantNode(ASTNode):
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value

class AssignmentNode(ASTNode):
    def __init__(self, target, value):
        self.target = target
        self.value = value

class InputNode(ASTNode):
    def __init__(self, identifier):
        self.identifier = identifier

class OutputNode(ASTNode):
    def __init__(self, expressions):
        self.expressions = expressions

class OpenFileNode(ASTNode):
    def __init__(self, file_ident, mode):
        self.file_ident = file_ident
        self.mode = mode

class ReadFileNode(ASTNode):
    def __init__(self, file_ident, target):
        self.file_ident = file_ident
        self.target = target

class WriteFileNode(ASTNode):
    def __init__(self, file_ident, data):
        self.file_ident = file_ident
        self.data = data

class CloseFileNode(ASTNode):
    def __init__(self, file_ident):
        self.file_ident = file_ident

class SeekNode(ASTNode):
    def __init__(self, file_ident, address):
        self.file_ident = file_ident
        self.address = address

class GetRecordNode(ASTNode):
    def __init__(self, file_ident, target):
        self.file_ident = file_ident
        self.target = target

class PutRecordNode(ASTNode):
    def __init__(self, file_ident, value):
        self.file_ident = file_ident
        self.value = value

class IfNode(ASTNode):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class CaseBranch:
    def __init__(self, value, range_end, statements):
        self.value = value
        self.range_end = range_end
        self.statements = statements

class CaseNode(ASTNode):
    def __init__(self, expr, branches, otherwise_block=None):
        self.expr = expr
        self.branches = branches
        self.otherwise_block = otherwise_block

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

class ProcedureNode(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FunctionDefNode(ASTNode):
    def __init__(self, name, params, return_type, body):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body

class CallNode(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ReturnNode(ASTNode):
    def __init__(self, value):
        self.value = value

class RecordTypeNode(ASTNode):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class EnumTypeNode(ASTNode):
    def __init__(self, name, values):
        self.name = name
        self.values = values

class PointerTypeNode(ASTNode):
    def __init__(self, name, base_type):
        self.name = name
        self.base_type = base_type

class SetTypeNode(ASTNode):
    def __init__(self, name, item_type):
        self.name = name
        self.item_type = item_type

class DefineNode(ASTNode):
    def __init__(self, name, values, type_name):
        self.name = name
        self.values = values
        self.type_name = type_name

class ClassNode(ASTNode):
    def __init__(self, name, parent, members):
        self.name = name
        self.parent = parent
        self.members = members

# ── Expression Nodes ──
class ExpressionStatementNode(ASTNode):
    def __init__(self, expression):
        self.expression = expression

class ExpressionNode(ASTNode):
    pass

class IdentifierNode(ExpressionNode):
    def __init__(self, name, token):
        self.name = name
        self.token = token

class ArrayAccessNode(ExpressionNode):
    def __init__(self, identifier, index_expr, index_expr2=None):
        self.identifier = identifier
        self.index_expr = index_expr
        self.index_expr2 = index_expr2

class DotAccessNode(ExpressionNode):
    def __init__(self, obj, field):
        self.obj = obj
        self.field = field

class FunctionCallNode(ExpressionNode):
    def __init__(self, callee, args, token):
        self.callee = callee
        self.args = args
        self.token = token

class NewExpressionNode(ExpressionNode):
    def __init__(self, class_name, args, token):
        self.class_name = class_name
        self.args = args
        self.token = token

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

class CharLiteralNode(ExpressionNode):
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
