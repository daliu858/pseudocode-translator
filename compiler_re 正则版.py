import re
import collections
from enum import Enum, auto

class TokenType(Enum):
    # Literals
    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    REAL_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOLEAN_LITERAL = auto() # TRUE, FALSE

    # Keywords (CAIE focused)
    KEYWORD_IF = auto()
    KEYWORD_THEN = auto()
    KEYWORD_ELSE = auto()
    KEYWORD_ENDIF = auto()
    KEYWORD_FOR = auto()
    KEYWORD_TO = auto()
    KEYWORD_STEP = auto()
    KEYWORD_NEXT = auto()
    KEYWORD_WHILE = auto()
    KEYWORD_DO = auto() # Used in WHILE ... DO ... ENDWHILE
    KEYWORD_ENDWHILE = auto()
    KEYWORD_REPEAT = auto()
    KEYWORD_UNTIL = auto()
    KEYWORD_PROCEDURE = auto()
    KEYWORD_ENDPROCEDURE = auto()
    KEYWORD_FUNCTION = auto()
    KEYWORD_RETURNS = auto()
    KEYWORD_RETURN = auto()
    KEYWORD_ENDFUNCTION = auto()
    KEYWORD_CALL = auto()
    KEYWORD_INPUT = auto()
    KEYWORD_OUTPUT = auto()      # Primary CAIE output keyword
    KEYWORD_PRINT = auto()       # Often used as alias for OUTPUT, kept from original
    KEYWORD_DECLARE = auto()
    KEYWORD_CONSTANT = auto()
    KEYWORD_ARRAY = auto()
    KEYWORD_OF = auto()
    KEYWORD_TYPE = auto()        # For user-defined record types (TYPE ... ENDTYPE)

    # Operator Keywords (CAIE)
    KEYWORD_AND = auto()
    KEYWORD_OR = auto()
    KEYWORD_NOT = auto()
    KEYWORD_MOD = auto() # Modulo operator
    KEYWORD_DIV = auto() # Integer division operator

    # Operators and Delimiters (CAIE focused)
    ASSIGN = auto()          # <- (CAIE assignment)
    EQUALS = auto()          # =  (CAIE comparison)
    NOT_EQUALS = auto()      # <> (CAIE not equals)
    LESS_THAN = auto()       # <
    LESS_EQUAL = auto()      # <=
    GREATER_THAN = auto()    # >
    GREATER_EQUAL = auto()   # >=
    PLUS = auto()            # +
    MINUS = auto()           # -
    MULTIPLY = auto()        # *
    DIVIDE = auto()          # / (real division)

    LPAREN = auto()          # (
    RPAREN = auto()          # )
    LBRACKET = auto()        # [ (for arrays)
    RBRACKET = auto()        # ]
    COMMA = auto()           # ,
    COLON = auto()           # : (used in DECLARE, FUNCTION/PROCEDURE parameters)
    DOT = auto()             # . (for record access e.g. MyRecord.Field)

    # Special
    COMMENT = auto()         # // comment (optional to tokenize, usually skipped)
    UNKNOWN = auto()         # Unrecognized token
    EOF = auto()             # End of File / End of Input

Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

KEYWORDS = {
    "IF": TokenType.KEYWORD_IF, "THEN": TokenType.KEYWORD_THEN, "ELSE": TokenType.KEYWORD_ELSE, "ENDIF": TokenType.KEYWORD_ENDIF,
    "FOR": TokenType.KEYWORD_FOR, "TO": TokenType.KEYWORD_TO, "STEP": TokenType.KEYWORD_STEP, "NEXT": TokenType.KEYWORD_NEXT,
    "WHILE": TokenType.KEYWORD_WHILE, "DO": TokenType.KEYWORD_DO, "ENDWHILE": TokenType.KEYWORD_ENDWHILE,
    "REPEAT": TokenType.KEYWORD_REPEAT, "UNTIL": TokenType.KEYWORD_UNTIL,
    "PROCEDURE": TokenType.KEYWORD_PROCEDURE, "ENDPROCEDURE": TokenType.KEYWORD_ENDPROCEDURE,
    "FUNCTION": TokenType.KEYWORD_FUNCTION, "RETURNS": TokenType.KEYWORD_RETURNS, "RETURN": TokenType.KEYWORD_RETURN, "ENDFUNCTION": TokenType.KEYWORD_ENDFUNCTION,
    "CALL": TokenType.KEYWORD_CALL,
    "INPUT": TokenType.KEYWORD_INPUT, "OUTPUT": TokenType.KEYWORD_OUTPUT, "PRINT": TokenType.KEYWORD_PRINT,
    "DECLARE": TokenType.KEYWORD_DECLARE, "CONSTANT": TokenType.KEYWORD_CONSTANT,
    "ARRAY": TokenType.KEYWORD_ARRAY, "OF": TokenType.KEYWORD_OF,
    "TYPE": TokenType.KEYWORD_TYPE,
    "TRUE": TokenType.BOOLEAN_LITERAL, "FALSE": TokenType.BOOLEAN_LITERAL,
    # Operator keywords
    "AND": TokenType.KEYWORD_AND,
    "OR": TokenType.KEYWORD_OR,
    "NOT": TokenType.KEYWORD_NOT,
    "MOD": TokenType.KEYWORD_MOD,
    "DIV": TokenType.KEYWORD_DIV
}


# ============================================================
# RE-based Tokenizer (generated scanner using regular expressions)
# ============================================================

# All token patterns, ordered by priority (longer/more specific first)
_TOKEN_SPECIFICATION = [
    ('COMMENT',         r'//[^\n]*'),              # // single-line comment
    ('REAL_LITERAL',    r'\d+\.\d*|\.\d+'),        # 3.14, .5, 42. etc.
    ('INTEGER_LITERAL', r'\d+'),                    # 42
    ('STRING_LITERAL',  r'"[^"]*"'),               # "hello world"
    ('IDENTIFIER',      r'[A-Za-z_]\w*'),          # variable names & keywords
    ('ASSIGN',          r'<-'),                     # <- (must precede < patterns)
    ('NOT_EQUALS',      r'<>'),                     # <>
    ('LESS_EQUAL',      r'<='),                     # <=
    ('GREATER_EQUAL',   r'>='),                     # >=
    ('LESS_THAN',       r'<'),                      # <
    ('GREATER_THAN',    r'>'),                      # >
    ('EQUALS',          r'='),                      # =
    ('PLUS',            r'\+'),                     # +
    ('MINUS',           r'-'),                      # -
    ('MULTIPLY',        r'\*'),                     # *
    ('DIVIDE',          r'/'),                      # /
    ('LPAREN',          r'\('),                     # (
    ('RPAREN',          r'\)'),                     # )
    ('LBRACKET',        r'\['),                     # [
    ('RBRACKET',        r'\]'),                     # ]
    ('COMMA',           r','),                      # ,
    ('COLON',           r':'),                      # :
    ('DOT',             r'\.'),                     # .
    ('NEWLINE',         r'\n'),                     # newline (for line tracking)
    ('SKIP',            r'[ \t\r]+'),               # whitespace (non-newline)
    ('UNKNOWN',         r'.'),                      # any other single character
]

# Compile the master pattern once (outside the function for efficiency)
_MASTER_PATTERN = re.compile(
    '|'.join(f'(?P<{name}>{pattern})' for name, pattern in _TOKEN_SPECIFICATION)
)

# Map from regex group names to TokenType for simple operator/delimiter tokens
_SIMPLE_TOKEN_MAP = {
    'ASSIGN':        TokenType.ASSIGN,
    'NOT_EQUALS':    TokenType.NOT_EQUALS,
    'LESS_EQUAL':    TokenType.LESS_EQUAL,
    'GREATER_EQUAL': TokenType.GREATER_EQUAL,
    'LESS_THAN':     TokenType.LESS_THAN,
    'GREATER_THAN':  TokenType.GREATER_THAN,
    'EQUALS':        TokenType.EQUALS,
    'PLUS':          TokenType.PLUS,
    'MINUS':         TokenType.MINUS,
    'MULTIPLY':      TokenType.MULTIPLY,
    'DIVIDE':        TokenType.DIVIDE,
    'LPAREN':        TokenType.LPAREN,
    'RPAREN':        TokenType.RPAREN,
    'LBRACKET':      TokenType.LBRACKET,
    'RBRACKET':      TokenType.RBRACKET,
    'COMMA':         TokenType.COMMA,
    'COLON':         TokenType.COLON,
    'DOT':           TokenType.DOT,
}


def tokenizer(source_code: str):
    """RE-based tokenizer: uses a compiled master regex to scan all tokens."""
    tokens = []
    current_line = 1
    line_start_pos = 0

    for match in _MASTER_PATTERN.finditer(source_code):
        kind = match.lastgroup
        value = match.group()
        col = match.start() - line_start_pos + 1

        if kind == 'NEWLINE':
            current_line += 1
            line_start_pos = match.end()
            continue

        if kind == 'SKIP' or kind == 'COMMENT':
            continue

        if kind == 'STRING_LITERAL':
            tokens.append(Token(TokenType.STRING_LITERAL, value[1:-1], current_line, col))
            continue

        if kind == 'INTEGER_LITERAL':
            tokens.append(Token(TokenType.INTEGER_LITERAL, int(value), current_line, col))
            continue

        if kind == 'REAL_LITERAL':
            tokens.append(Token(TokenType.REAL_LITERAL, float(value), current_line, col))
            continue

        if kind == 'IDENTIFIER':
            keyword_type = KEYWORDS.get(value.upper())
            if keyword_type:
                tokens.append(Token(keyword_type, value.upper(), current_line, col))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, value, current_line, col))
            continue

        if kind == 'UNKNOWN':
            tokens.append(Token(TokenType.UNKNOWN, value, current_line, col))
            continue

        # Operators and delimiters
        token_type = _SIMPLE_TOKEN_MAP.get(kind)
        if token_type:
            tokens.append(Token(token_type, value, current_line, col))

    eof_col = len(source_code) - line_start_pos + 1 if source_code else 1
    tokens.append(Token(TokenType.EOF, "EOF", current_line, eof_col))
    return tokens


# ============================================================
# Hand-crafted Tokenizer (original version, kept for comparison)
# ============================================================

def tokenizer_handcrafted(source_code: str):
    tokens = []
    current_pos = 0
    source_length = len(source_code)
    
    current_line = 1
    line_start_pos = 0

    while current_pos < source_length:
        char = source_code[current_pos]
        start_column = current_pos - line_start_pos + 1

        if char.isspace():
            if char == '\n':
                current_line += 1
                line_start_pos = current_pos + 1
            current_pos += 1
            continue

        if char == '/' and current_pos + 1 < source_length and source_code[current_pos + 1] == '/':
            current_pos += 2 
            while current_pos < source_length and source_code[current_pos] != '\n':
                current_pos += 1
            continue

        if char == '"':
            string_literal_start_line = current_line
            string_literal_start_col = start_column
            current_pos += 1
            value_builder = []
            while current_pos < source_length and source_code[current_pos] != '"':
                current_char_in_string = source_code[current_pos]
                value_builder.append(current_char_in_string)
                if current_char_in_string == '\n':
                    current_line += 1
                    line_start_pos = current_pos + 1
                current_pos += 1
            final_string_value = "".join(value_builder)
            if current_pos < source_length and source_code[current_pos] == '"':
                tokens.append(Token(TokenType.STRING_LITERAL, final_string_value, string_literal_start_line, string_literal_start_col))
                current_pos += 1
            else:
                tokens.append(Token(TokenType.UNKNOWN, f"Unterminated string: \"{final_string_value}", string_literal_start_line, string_literal_start_col))
            continue

        if char.isdigit() or (char == '.' and current_pos + 1 < source_length and source_code[current_pos + 1].isdigit()):
            num_str_value = ""
            is_real_num = False
            num_original_start_column = start_column
            while current_pos < source_length:
                next_char = source_code[current_pos]
                if next_char.isdigit():
                    num_str_value += next_char
                elif next_char == '.' and not is_real_num:
                    num_str_value += next_char
                    is_real_num = True
                else:
                    break
                current_pos += 1
            try:
                if is_real_num:
                    tokens.append(Token(TokenType.REAL_LITERAL, float(num_str_value), current_line, num_original_start_column))
                else:
                    tokens.append(Token(TokenType.INTEGER_LITERAL, int(num_str_value), current_line, num_original_start_column))
            except ValueError:
                tokens.append(Token(TokenType.UNKNOWN, num_str_value, current_line, num_original_start_column))
            continue

        if char.isalpha() or char == '_':
            ident_str = ""
            start_pos_ident = current_pos
            while current_pos < source_length and (source_code[current_pos].isalnum() or source_code[current_pos] == '_'):
                ident_str += source_code[current_pos]
                current_pos += 1
            keyword_type = KEYWORDS.get(ident_str.upper())
            if keyword_type:
                tokens.append(Token(keyword_type, ident_str.upper(), current_line, start_column))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, ident_str, current_line, start_column))
            continue

        processed_operator = False
        if char == '<':
            if current_pos + 1 < source_length:
                next_char_op = source_code[current_pos + 1]
                if next_char_op == '-':
                    tokens.append(Token(TokenType.ASSIGN, "<-", current_line, start_column))
                    current_pos += 2
                    processed_operator = True
                elif next_char_op == '=':
                    tokens.append(Token(TokenType.LESS_EQUAL, "<=", current_line, start_column))
                    current_pos += 2
                    processed_operator = True
                elif next_char_op == '>':
                    tokens.append(Token(TokenType.NOT_EQUALS, "<>", current_line, start_column))
                    current_pos += 2
                    processed_operator = True
            if processed_operator: continue
        elif char == '>':
            if current_pos + 1 < source_length and source_code[current_pos + 1] == '=':
                tokens.append(Token(TokenType.GREATER_EQUAL, ">=", current_line, start_column))
                current_pos += 2
                processed_operator = True
            if processed_operator: continue
        
        single_char_map = {
            '=': TokenType.EQUALS, '<': TokenType.LESS_THAN, '>': TokenType.GREATER_THAN,
            '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.MULTIPLY, '/': TokenType.DIVIDE,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN, '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
            ',': TokenType.COMMA, ':': TokenType.COLON, '.': TokenType.DOT
        }
        single_char_token_type = single_char_map.get(char)
        if single_char_token_type:
            tokens.append(Token(single_char_token_type, char, current_line, start_column))
            current_pos += 1
            continue
        
        tokens.append(Token(TokenType.UNKNOWN, char, current_line, start_column))
        current_pos += 1

    eof_column = current_pos - line_start_pos + 1 if source_length > 0 else 1
    tokens.append(Token(TokenType.EOF, "EOF", current_line, eof_column))
    return tokens


# --- AST Node Definitions ---
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
        self.target = target
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


# --- Parser Definition ---
class Parser:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type != TokenType.COMMENT]
        self.current_token_index = 0
        self.errors = []
        self.symbol_table = {}

    def _current_token(self):
        return self.tokens[self.current_token_index]

    def _advance(self):
        if self.current_token_index < len(self.tokens) - 1:
            self.current_token_index += 1

    def _eat(self, expected_token_type, error_message=None):
        token = self._current_token()
        if token.type == expected_token_type:
            self._advance()
            return token
        else:
            msg = error_message or f"Expected {expected_token_type}, but got {token.type} ('{token.value}')"
            self._error(msg, token)
            raise SyntaxError(msg)

    def _error(self, message, token=None):
        token = token or self._current_token()
        error_msg = f"ParseError at L{token.line}C{token.column}: {message}"
        self.errors.append(error_msg)

    def parse(self):
        statements = []
        while self._current_token().type != TokenType.EOF:
            try:
                statement = self._parse_statement()
                if statement:
                    statements.append(statement)
            except SyntaxError:
                self._synchronize()
        if self.errors:
            return None
        return ProgramNode(statements)

    def _synchronize(self):
        self._advance()
        while self._current_token().type != TokenType.EOF:
            if self._current_token().type in [
                TokenType.KEYWORD_DECLARE, TokenType.IDENTIFIER, TokenType.KEYWORD_IF,
                TokenType.KEYWORD_FOR, TokenType.KEYWORD_WHILE, TokenType.KEYWORD_REPEAT,
                TokenType.KEYWORD_INPUT, TokenType.KEYWORD_OUTPUT, TokenType.KEYWORD_PRINT,
                TokenType.KEYWORD_ENDIF, TokenType.KEYWORD_ENDWHILE, TokenType.KEYWORD_NEXT,
                TokenType.KEYWORD_UNTIL
            ]:
                return
            self._advance()

    def _parse_statement(self):
        token_type = self._current_token().type
        if token_type == TokenType.KEYWORD_DECLARE:
            return self._parse_declaration()
        elif token_type == TokenType.IDENTIFIER:
            return self._parse_assignment_or_call()
        elif token_type == TokenType.KEYWORD_INPUT:
            return self._parse_input()
        elif token_type == TokenType.KEYWORD_OUTPUT or token_type == TokenType.KEYWORD_PRINT:
            return self._parse_output()
        elif token_type == TokenType.KEYWORD_IF:
            return self._parse_if_statement()
        elif token_type == TokenType.KEYWORD_FOR:
            return self._parse_for_statement()
        elif token_type == TokenType.KEYWORD_WHILE:
            return self._parse_while_statement()
        elif token_type == TokenType.KEYWORD_REPEAT:
            return self._parse_repeat_statement()
        else:
            self._error(f"Unexpected token '{self._current_token().value}' at start of statement.")
            raise SyntaxError("Invalid start of statement")

    def _parse_declaration(self):
        self._eat(TokenType.KEYWORD_DECLARE)
        identifier_token = self._eat(TokenType.IDENTIFIER)
        identifier_node = IdentifierNode(identifier_token.value, identifier_token)
        self._eat(TokenType.COLON)
        type_name_token = self._current_token()
        array_spec = None
        if type_name_token.type == TokenType.KEYWORD_ARRAY:
            self._eat(TokenType.KEYWORD_ARRAY)
            self._eat(TokenType.LBRACKET)
            low_bound_expr = self._parse_expression()
            self._eat(TokenType.COLON)
            high_bound_expr = self._parse_expression()
            self._eat(TokenType.RBRACKET)
            self._eat(TokenType.KEYWORD_OF)
            item_type_token = self._eat_type()
            type_name = "ARRAY"
            array_spec = {
                "item_type": item_type_token.value,
                "low_bound": low_bound_expr,
                "high_bound": high_bound_expr
            }
            self.symbol_table[identifier_node.name] = {"type": "ARRAY", "item_type": item_type_token.value}
        else:
            type_token = self._eat_type()
            type_name = type_token.value
            self.symbol_table[identifier_node.name] = {"type": type_name}
        return DeclarationNode(identifier_node, type_name, array_spec)

    def _eat_type(self):
        token = self._current_token()
        valid_types = ["INTEGER", "REAL", "STRING", "BOOLEAN", "CHAR", "DATE"]
        if token.type == TokenType.IDENTIFIER and token.value.upper() in valid_types:
            self._advance()
            return Token(token.type, token.value.upper(), token.line, token.column)
        else:
            self._error(f"Expected a type name (e.g., INTEGER), got {token.value}")
            raise SyntaxError("Invalid type name")

    def _parse_assignment_or_call(self):
        target_node = self._parse_target()
        self._eat(TokenType.ASSIGN, "Expected '<-' for assignment")
        value_expr = self._parse_expression()
        return AssignmentNode(target_node, value_expr)

    def _parse_target(self):
        identifier_token = self._eat(TokenType.IDENTIFIER)
        identifier_node = IdentifierNode(identifier_token.value, identifier_token)
        if self._current_token().type == TokenType.LBRACKET:
            self._eat(TokenType.LBRACKET)
            index_expr = self._parse_expression()
            self._eat(TokenType.RBRACKET)
            return ArrayAccessNode(identifier_node, index_expr)
        return identifier_node

    def _parse_input(self):
        self._eat(TokenType.KEYWORD_INPUT)
        identifier_token = self._eat(TokenType.IDENTIFIER)
        identifier_node = IdentifierNode(identifier_token.value, identifier_token)
        return InputNode(identifier_node)

    def _parse_output(self):
        if self._current_token().type == TokenType.KEYWORD_OUTPUT:
            self._eat(TokenType.KEYWORD_OUTPUT)
        else:
            self._eat(TokenType.KEYWORD_PRINT)
        expressions = [self._parse_expression()]
        while self._current_token().type == TokenType.COMMA:
            self._eat(TokenType.COMMA)
            expressions.append(self._parse_expression())
        return OutputNode(expressions)

    def _parse_if_statement(self):
        self._eat(TokenType.KEYWORD_IF)
        condition = self._parse_expression()
        self._eat(TokenType.KEYWORD_THEN)
        then_block = []
        while self._current_token().type not in [TokenType.KEYWORD_ELSE, TokenType.KEYWORD_ENDIF, TokenType.EOF]:
            then_block.append(self._parse_statement())
        else_block = None
        if self._current_token().type == TokenType.KEYWORD_ELSE:
            self._eat(TokenType.KEYWORD_ELSE)
            else_block = []
            while self._current_token().type not in [TokenType.KEYWORD_ENDIF, TokenType.EOF]:
                else_block.append(self._parse_statement())
        self._eat(TokenType.KEYWORD_ENDIF)
        return IfNode(condition, then_block, else_block)

    def _parse_for_statement(self):
        self._eat(TokenType.KEYWORD_FOR)
        var_token = self._eat(TokenType.IDENTIFIER)
        variable = IdentifierNode(var_token.value, var_token)
        self._eat(TokenType.ASSIGN)
        start_expr = self._parse_expression()
        self._eat(TokenType.KEYWORD_TO)
        end_expr = self._parse_expression()
        step_expr = None
        if self._current_token().type == TokenType.KEYWORD_STEP:
            self._eat(TokenType.KEYWORD_STEP)
            step_expr = self._parse_expression()
        body = []
        while self._current_token().type not in [TokenType.KEYWORD_NEXT, TokenType.EOF]:
            body.append(self._parse_statement())
        self._eat(TokenType.KEYWORD_NEXT)
        if self._current_token().type == TokenType.IDENTIFIER:
            next_var_token = self._eat(TokenType.IDENTIFIER)
            if next_var_token.value != variable.name:
                self._error(f"FOR loop variable '{variable.name}' does not match NEXT variable '{next_var_token.value}'.")
        return ForNode(variable, start_expr, end_expr, step_expr, body)

    def _parse_while_statement(self):
        self._eat(TokenType.KEYWORD_WHILE)
        condition = self._parse_expression()
        self._eat(TokenType.KEYWORD_DO)
        body = []
        while self._current_token().type not in [TokenType.KEYWORD_ENDWHILE, TokenType.EOF]:
            body.append(self._parse_statement())
        self._eat(TokenType.KEYWORD_ENDWHILE)
        return WhileNode(condition, body)

    def _parse_repeat_statement(self):
        self._eat(TokenType.KEYWORD_REPEAT)
        body = []
        while self._current_token().type not in [TokenType.KEYWORD_UNTIL, TokenType.EOF]:
            body.append(self._parse_statement())
        self._eat(TokenType.KEYWORD_UNTIL)
        condition = self._parse_expression()
        return RepeatNode(body, condition)

    def _parse_expression(self):
        return self._parse_logical_or()

    def _parse_logical_or(self):
        node = self._parse_logical_and()
        while self._current_token().type == TokenType.KEYWORD_OR:
            op_token = self._eat(TokenType.KEYWORD_OR)
            right_node = self._parse_logical_and()
            node = BinaryOpNode(node, op_token, right_node)
        return node

    def _parse_logical_and(self):
        node = self._parse_comparison()
        while self._current_token().type == TokenType.KEYWORD_AND:
            op_token = self._eat(TokenType.KEYWORD_AND)
            right_node = self._parse_comparison()
            node = BinaryOpNode(node, op_token, right_node)
        return node

    def _parse_comparison(self):
        node = self._parse_term()
        comp_ops = [TokenType.EQUALS, TokenType.NOT_EQUALS, TokenType.LESS_THAN,
                    TokenType.LESS_EQUAL, TokenType.GREATER_THAN, TokenType.GREATER_EQUAL]
        if self._current_token().type in comp_ops:
            op_token = self._current_token()
            self._advance()
            right_node = self._parse_term()
            node = BinaryOpNode(node, op_token, right_node)
        return node

    def _parse_term(self):
        node = self._parse_factor()
        while self._current_token().type in [TokenType.PLUS, TokenType.MINUS]:
            op_token = self._current_token()
            self._advance()
            right_node = self._parse_factor()
            node = BinaryOpNode(node, op_token, right_node)
        return node

    def _parse_factor(self):
        node = self._parse_unary()
        op_types = [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.KEYWORD_DIV, TokenType.KEYWORD_MOD]
        while self._current_token().type in op_types:
            op_token = self._current_token()
            self._advance()
            right_node = self._parse_unary()
            node = BinaryOpNode(node, op_token, right_node)
        return node

    def _parse_unary(self):
        token = self._current_token()
        if token.type == TokenType.KEYWORD_NOT:
            op_token = self._eat(TokenType.KEYWORD_NOT)
            operand = self._parse_unary()
            return UnaryOpNode(op_token, operand)
        elif token.type == TokenType.MINUS:
            op_token = self._eat(TokenType.MINUS)
            operand = self._parse_unary()
            return UnaryOpNode(op_token, operand)
        else:
            return self._parse_primary()

    def _parse_primary(self):
        token = self._current_token()
        if token.type == TokenType.INTEGER_LITERAL:
            self._advance()
            return IntegerLiteralNode(token.value, token)
        elif token.type == TokenType.REAL_LITERAL:
            self._advance()
            return RealLiteralNode(token.value, token)
        elif token.type == TokenType.STRING_LITERAL:
            self._advance()
            return StringLiteralNode(token.value, token)
        elif token.type == TokenType.BOOLEAN_LITERAL:
            self._advance()
            return BooleanLiteralNode(token.value.upper() == "TRUE", token)
        elif token.type == TokenType.IDENTIFIER:
            return self._parse_target()
        elif token.type == TokenType.LPAREN:
            self._eat(TokenType.LPAREN)
            expr_node = self._parse_expression()
            self._eat(TokenType.RPAREN)
            return expr_node
        else:
            self._error(f"Unexpected token in expression: {token.value} ({token.type})")
            raise SyntaxError("Invalid expression component")


# --- Python Code Generator ---
class PythonCodeGenerator:
    def __init__(self):
        self.indent_level = 0
        self.python_code = []
        self.declared_variables = {}
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
                self.array_metadata[var_name] = {"low_bound": low_val}
            else:
                 self._add_line(f"{var_name} = [] # Dynamic array, cannot simulate fixed bounds")
        else:
            self._add_line(f"{var_name} = None # Unknown CAIE type: {node.type_name}")

    def visit_AssignmentNode(self, node: AssignmentNode):
        target = self.visit(node.target)
        value = self.visit(node.value)
        self._add_line(f"{target} = {value}")

    def visit_InputNode(self, node: InputNode):
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
        offset = 1
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


# ============================================================
# Comparison Test: RE tokenizer vs Hand-crafted tokenizer
# ============================================================

if __name__ == "__main__":
    test_source = """\
// This is a comment
DECLARE x : INTEGER
DECLARE name : STRING
DECLARE scores : ARRAY[1:10] OF INTEGER
DECLARE pi : REAL

x <- 42
name <- "Hello World"
pi <- 3.14
scores[1] <- 100

INPUT x

OUTPUT "The value is: ", x, " and pi is ", pi

IF x > 10 AND x <= 100 THEN
    OUTPUT "x is between 11 and 100"
ELSE
    OUTPUT "x is out of range"
ENDIF

FOR i <- 1 TO 10 STEP 2
    scores[i] <- i * 10
    OUTPUT scores[i]
NEXT i

WHILE x <> 0 DO
    x <- x - 1
ENDWHILE

REPEAT
    x <- x + 1
    OUTPUT x
UNTIL x >= 5

OUTPUT x MOD 3, x DIV 2
OUTPUT NOT TRUE OR FALSE
OUTPUT (x + 1) * (x - 1)
OUTPUT x <= 10, x >= 0, x <> 5
"""

    print("=" * 70)
    print("  COMPARISON: RE-based tokenizer vs Hand-crafted tokenizer")
    print("=" * 70)

    tokens_re = tokenizer(test_source)
    tokens_hc = tokenizer_handcrafted(test_source)

    print(f"\n  RE tokenizer produced:          {len(tokens_re)} tokens")
    print(f"  Hand-crafted tokenizer produced: {len(tokens_hc)} tokens")

    # Compare token by token
    max_len = max(len(tokens_re), len(tokens_hc))
    mismatches = []
    for i in range(max_len):
        t_re = tokens_re[i] if i < len(tokens_re) else None
        t_hc = tokens_hc[i] if i < len(tokens_hc) else None
        if t_re != t_hc:
            mismatches.append((i, t_re, t_hc))

    if not mismatches:
        print("\n  [PASS] All tokens are IDENTICAL! The two tokenizers produce the same output.")
    else:
        print(f"\n  [DIFF] Found {len(mismatches)} difference(s):\n")
        for idx, t_re, t_hc in mismatches[:20]:
            print(f"    Token #{idx}:")
            print(f"      RE:          {t_re}")
            print(f"      Hand-crafted: {t_hc}")

    # Full pipeline test: feed RE tokens into parser and code generator
    print("\n" + "=" * 70)
    print("  Full pipeline test (RE tokenizer -> Parser -> Code Generator)")
    print("=" * 70)

    parser = Parser(tokens_re)
    ast = parser.parse()

    if parser.errors:
        print("\n  Parse errors:")
        for err in parser.errors:
            print(f"    {err}")
    else:
        codegen = PythonCodeGenerator()
        python_code = codegen.generate(ast)
        print("\n  Generated Python code:\n")
        for line in python_code.split('\n'):
            print(f"    {line}")

    print("\n" + "=" * 70)
    print("  Full pipeline test (Hand-crafted tokenizer -> Parser -> Code Generator)")
    print("=" * 70)

    parser_hc = Parser(tokens_hc)
    ast_hc = parser_hc.parse()

    if parser_hc.errors:
        print("\n  Parse errors:")
        for err in parser_hc.errors:
            print(f"    {err}")
    else:
        codegen_hc = PythonCodeGenerator()
        python_code_hc = codegen_hc.generate(ast_hc)
        print("\n  Generated Python code:\n")
        for line in python_code_hc.split('\n'):
            print(f"    {line}")

    # Compare final outputs
    print("\n" + "=" * 70)
    if not parser.errors and not parser_hc.errors:
        if python_code == python_code_hc:
            print("  [PASS] Both pipelines produce IDENTICAL Python code!")
        else:
            print("  [DIFF] The generated Python code differs!")
    print("=" * 70)
