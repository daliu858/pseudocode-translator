"""
递归下降语法分析器。
"""

from .tokens import TokenType, Token
from .ast_nodes import (
    ProgramNode, DeclarationNode, AssignmentNode, InputNode, OutputNode,
    IfNode, ForNode, WhileNode, RepeatNode,
    IdentifierNode, ArrayAccessNode,
    IntegerLiteralNode, RealLiteralNode, StringLiteralNode, BooleanLiteralNode,
    BinaryOpNode, UnaryOpNode,
)

# 中文注释：该处为编译器实现说明。

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
        # 中文注释：该处为编译器实现说明。
        # 中文注释：该处为编译器实现说明。

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
        """Advance until we find a token that can likely start a new statement."""
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

    # 中文注释：该处为编译器实现说明。
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


# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。

