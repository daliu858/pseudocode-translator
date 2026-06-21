"""Parsing stage.

`Parser` consumes a Token stream and produces an AST while collecting syntax
diagnostics.
"""
from errors import ErrorSeverity, CompileError
from tokens import TokenType, Token
from ast_nodes import (
    ASTNode, ProgramNode, DeclarationNode, ConstantNode, AssignmentNode,
    InputNode, OutputNode, IfNode, CaseBranch, CaseNode, ForNode, WhileNode,
    RepeatNode, ProcedureNode, FunctionDefNode, CallNode, ReturnNode,
    RecordTypeNode, EnumTypeNode, PointerTypeNode, SetTypeNode, DefineNode,
    ClassNode, ExpressionStatementNode, ExpressionNode, IdentifierNode,
    ArrayAccessNode, DotAccessNode, FunctionCallNode, NewExpressionNode,
    IntegerLiteralNode, RealLiteralNode, StringLiteralNode, CharLiteralNode,
    BooleanLiteralNode, BinaryOpNode, UnaryOpNode,
)


# ─── Parser ─────────────────────────────────────────────────────────────
class Parser:
    def __init__(self, tokens, source_code=""):
        self.tokens = [t for t in tokens if t.type != TokenType.COMMENT]
        self.current_token_index = 0
        self.errors = []
        self.scope_stack = [{}]
        self.source_lines = source_code.split('\n') if source_code else []

    @property
    def symbol_table(self):
        return self.scope_stack[-1]

    def _initialize_scope(self):
        self.scope_stack.append({})

    def _finalize_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def _lookup(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def _get_source_line(self, ln):
        return self.source_lines[ln - 1] if 0 < ln <= len(self.source_lines) else None

    def _current_token(self):
        return self.tokens[self.current_token_index]

    def _peek(self, offset=1):
        idx = self.current_token_index + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def _advance(self):
        if self.current_token_index < len(self.tokens) - 1:
            self.current_token_index += 1

    def _eat(self, expected, error_message=None):
        token = self._current_token()
        if token.type == expected:
            self._advance()
            return token
        if error_message is None:
            name = expected.name.replace('KEYWORD_', '')
            if token.type == TokenType.EOF:
                error_message = f"Expected '{name}' but reached end of input."
            else:
                error_message = f"Expected '{name}', but got '{token.value}'."
        self._error(error_message, token)
        raise SyntaxError(error_message)

    def _error(self, message, token=None, severity=ErrorSeverity.ERROR, suggestion=None):
        token = token or self._current_token()
        err = CompileError(severity, token.line, token.column, message, suggestion,
                           self._get_source_line(token.line))
        self.errors.append(err)

    def _warning(self, message, token=None, suggestion=None):
        self._error(message, token, ErrorSeverity.WARNING, suggestion)

    # ── entry ──
    def _collect_stmt(self, body):
        stmt = self._parse_statement()
        if stmt is None:
            return
        if isinstance(stmt, list):
            body.extend(stmt)
        else:
            body.append(stmt)

    def parse(self):
        statements = []
        while self._current_token().type != TokenType.EOF:
            try:
                self._collect_stmt(statements)
            except SyntaxError:
                self._synchronize()
        if any(e.severity == ErrorSeverity.ERROR for e in self.errors):
            return None
        return ProgramNode(statements)

    def _synchronize(self):
        self._advance()
        sync_tokens = {
            TokenType.KEYWORD_DECLARE, TokenType.KEYWORD_CONSTANT, TokenType.IDENTIFIER,
            TokenType.KEYWORD_IF, TokenType.KEYWORD_FOR, TokenType.KEYWORD_WHILE,
            TokenType.KEYWORD_REPEAT, TokenType.KEYWORD_INPUT, TokenType.KEYWORD_OUTPUT,
            TokenType.KEYWORD_PRINT, TokenType.KEYWORD_CALL, TokenType.KEYWORD_RETURN,
            TokenType.KEYWORD_CASE, TokenType.KEYWORD_PROCEDURE, TokenType.KEYWORD_FUNCTION,
            TokenType.KEYWORD_TYPE, TokenType.KEYWORD_CLASS, TokenType.KEYWORD_DEFINE,
            TokenType.KEYWORD_ENDIF, TokenType.KEYWORD_ENDWHILE, TokenType.KEYWORD_NEXT,
            TokenType.KEYWORD_UNTIL, TokenType.KEYWORD_ENDCASE, TokenType.KEYWORD_ENDPROCEDURE,
            TokenType.KEYWORD_ENDFUNCTION, TokenType.KEYWORD_ENDTYPE, TokenType.KEYWORD_ENDCLASS,
            TokenType.KEYWORD_OTHERWISE,
        }
        while self._current_token().type != TokenType.EOF:
            if self._current_token().type in sync_tokens:
                return
            self._advance()

    # ── statement dispatch ──
    def _parse_statement(self):
        tt = self._current_token().type
        if tt == TokenType.KEYWORD_DECLARE:
            return self._parse_declaration()
        if tt == TokenType.KEYWORD_CONSTANT:
            return self._parse_constant()
        if tt == TokenType.IDENTIFIER:
            return self._parse_assignment_or_call()
        if tt in (TokenType.KEYWORD_OUTPUT, TokenType.KEYWORD_PRINT):
            return self._parse_output()
        if tt == TokenType.KEYWORD_INPUT:
            return self._parse_input()
        if tt == TokenType.KEYWORD_IF:
            return self._parse_if_statement()
        if tt == TokenType.KEYWORD_CASE:
            return self._parse_case()
        if tt == TokenType.KEYWORD_FOR:
            return self._parse_for_statement()
        if tt == TokenType.KEYWORD_WHILE:
            return self._parse_while_statement()
        if tt == TokenType.KEYWORD_REPEAT:
            return self._parse_repeat_statement()
        if tt == TokenType.KEYWORD_PROCEDURE:
            return self._parse_procedure()
        if tt == TokenType.KEYWORD_FUNCTION:
            return self._parse_function_def()
        if tt == TokenType.KEYWORD_CALL:
            return self._parse_call_statement()
        if tt == TokenType.KEYWORD_RETURN:
            return self._parse_return()
        if tt == TokenType.KEYWORD_TYPE:
            return self._parse_type_def()
        if tt == TokenType.KEYWORD_DEFINE:
            return self._parse_define()
        if tt == TokenType.KEYWORD_CLASS:
            return self._parse_class()
        if tt == TokenType.KEYWORD_SUPER:
            expr = self._parse_expression()
            return ExpressionStatementNode(expr)
        if tt in (TokenType.KEYWORD_PUBLIC, TokenType.KEYWORD_PRIVATE):
            self._advance()
            return self._parse_statement()

        tok = self._current_token()
        valid = ("DECLARE, CONSTANT, IF, CASE, FOR, WHILE, REPEAT, "
                 "INPUT, OUTPUT, CALL, RETURN, PROCEDURE, FUNCTION, TYPE, CLASS, or an identifier")
        self._error(f"Unexpected token '{tok.value}' at start of statement.", tok,
                    suggestion=f"A statement must start with: {valid}.")
        raise SyntaxError("Invalid start of statement")

    # ── helpers ──
    def _eat_type(self):
        token = self._current_token()
        valid_types = {"INTEGER", "REAL", "STRING", "BOOLEAN", "CHAR", "DATE"}
        wrong = {"INT": "INTEGER", "FLOAT": "REAL", "DOUBLE": "REAL",
                 "STR": "STRING", "BOOL": "BOOLEAN", "NUMBER": "INTEGER", "NUM": "INTEGER"}
        if token.type == TokenType.IDENTIFIER:
            upper = token.value.upper()
            if upper in valid_types:
                self._advance()
                return Token(token.type, upper, token.line, token.column)
            fix = wrong.get(upper)
            if fix:
                self._error(f"'{token.value}' is not a valid pseudocode type.", token,
                            suggestion=f"Did you mean '{fix}'?")
                raise SyntaxError("Invalid type name")
            self._advance()
            return Token(token.type, token.value, token.line, token.column)
        self._error(f"Expected a type name (INTEGER, REAL, STRING, BOOLEAN, CHAR, DATE), got '{token.value}'.", token)
        raise SyntaxError("Invalid type name")

    def _parse_access_chain(self):
        id_tok = self._eat(TokenType.IDENTIFIER)
        node = IdentifierNode(id_tok.value, id_tok)
        while True:
            if self._current_token().type == TokenType.LBRACKET:
                self._eat(TokenType.LBRACKET)
                idx1 = self._parse_expression()
                idx2 = None
                if self._current_token().type == TokenType.COMMA:
                    self._eat(TokenType.COMMA)
                    idx2 = self._parse_expression()
                self._eat(TokenType.RBRACKET)
                node = ArrayAccessNode(node, idx1, idx2)
            elif self._current_token().type == TokenType.DOT:
                self._eat(TokenType.DOT)
                if self._current_token().type == TokenType.KEYWORD_NEW:
                    ft = self._current_token()
                    self._advance()
                else:
                    ft = self._eat(TokenType.IDENTIFIER)
                node = DotAccessNode(node, IdentifierNode(ft.value, ft))
            elif self._current_token().type == TokenType.LPAREN:
                self._eat(TokenType.LPAREN)
                args = []
                if self._current_token().type != TokenType.RPAREN:
                    args.append(self._parse_expression())
                    while self._current_token().type == TokenType.COMMA:
                        self._eat(TokenType.COMMA)
                        args.append(self._parse_expression())
                self._eat(TokenType.RPAREN)
                node = FunctionCallNode(node, args, id_tok)
            else:
                break
        return node

    # ── statement parsers ──
    def _parse_declaration(self):
        self._eat(TokenType.KEYWORD_DECLARE)
        ids = [self._eat(TokenType.IDENTIFIER)]
        while self._current_token().type == TokenType.COMMA:
            self._eat(TokenType.COMMA)
            ids.append(self._eat(TokenType.IDENTIFIER))
        self._eat(TokenType.COLON)

        type_tok = self._current_token()
        array_spec = None
        if type_tok.type == TokenType.KEYWORD_ARRAY:
            self._eat(TokenType.KEYWORD_ARRAY)
            self._eat(TokenType.LBRACKET)
            low1 = self._parse_expression()
            self._eat(TokenType.COLON)
            high1 = self._parse_expression()
            low2 = high2 = None
            is_2d = False
            if self._current_token().type == TokenType.COMMA:
                self._eat(TokenType.COMMA)
                low2 = self._parse_expression()
                self._eat(TokenType.COLON)
                high2 = self._parse_expression()
                is_2d = True
            self._eat(TokenType.RBRACKET)
            self._eat(TokenType.KEYWORD_OF)
            item_type = self._eat_type()
            type_name = "ARRAY"
            array_spec = {"item_type": item_type.value,
                          "low_bound": low1, "high_bound": high1}
            if is_2d:
                array_spec["is_2d"] = True
                array_spec["low_bound2"] = low2
                array_spec["high_bound2"] = high2
            for idt in ids:
                self.symbol_table[idt.value] = {"type": "ARRAY", "array_spec": array_spec, "item_type": item_type.value}
        else:
            tp = self._eat_type()
            type_name = tp.value
            for idt in ids:
                self.symbol_table[idt.value] = {"type": type_name, "array_spec": None}

        if len(ids) == 1:
            return DeclarationNode(IdentifierNode(ids[0].value, ids[0]), type_name, array_spec)
        return [DeclarationNode(IdentifierNode(idt.value, idt), type_name, array_spec) for idt in ids]

    def _parse_constant(self):
        self._eat(TokenType.KEYWORD_CONSTANT)
        id_tok = self._eat(TokenType.IDENTIFIER)
        id_node = IdentifierNode(id_tok.value, id_tok)
        self.symbol_table[id_tok.value] = {"type": "CONSTANT", "array_spec": None}
        self._eat(TokenType.EQUALS)
        value = self._parse_expression()
        return ConstantNode(id_node, value)

    def _parse_assignment_or_call(self):
        node = self._parse_access_chain()
        if self._current_token().type == TokenType.ASSIGN:
            self._eat(TokenType.ASSIGN)
            value = self._parse_expression()
            return AssignmentNode(node, value)
        if self._current_token().type == TokenType.EQUALS:
            self._error("Cannot use '=' for assignment.", self._current_token(),
                        suggestion="Use '<-' for assignment. '=' is only for comparison.")
            self._advance()
            value = self._parse_expression()
            return AssignmentNode(node, value)
        if isinstance(node, FunctionCallNode):
            return ExpressionStatementNode(node)
        self._error("Expected '<-' for assignment.", self._current_token())
        raise SyntaxError("Expected assignment")

    def _parse_input(self):
        self._eat(TokenType.KEYWORD_INPUT)
        id_tok = self._eat(TokenType.IDENTIFIER)
        return InputNode(IdentifierNode(id_tok.value, id_tok))

    def _parse_output(self):
        tok = self._current_token()
        if tok.type == TokenType.KEYWORD_PRINT:
            self._warning("'PRINT' is not standard CAIE pseudocode.", tok,
                          suggestion="Use 'OUTPUT' instead.")
            self._eat(TokenType.KEYWORD_PRINT)
        else:
            self._eat(TokenType.KEYWORD_OUTPUT)
        exprs = [self._parse_expression()]
        while self._current_token().type == TokenType.COMMA:
            self._eat(TokenType.COMMA)
            exprs.append(self._parse_expression())
        return OutputNode(exprs)

    def _parse_if_statement(self):
        if_tok = self._current_token()
        self._eat(TokenType.KEYWORD_IF)
        cond = self._parse_expression()
        self._eat(TokenType.KEYWORD_THEN, "Expected 'THEN' after IF condition.")
        then_block = []
        while self._current_token().type not in (TokenType.KEYWORD_ELSE, TokenType.KEYWORD_ENDIF, TokenType.EOF):
            self._collect_stmt(then_block)
        else_block = None
        if self._current_token().type == TokenType.KEYWORD_ELSE:
            self._eat(TokenType.KEYWORD_ELSE)
            else_block = []
            while self._current_token().type not in (TokenType.KEYWORD_ENDIF, TokenType.EOF):
                self._collect_stmt(else_block)
        if self._current_token().type == TokenType.EOF:
            self._error("Missing 'ENDIF'.", if_tok, suggestion="Every IF must end with ENDIF.")
            raise SyntaxError("Missing ENDIF")
        self._eat(TokenType.KEYWORD_ENDIF)
        return IfNode(cond, then_block, else_block)

    # ── CASE ──
    def _at_case_boundary(self):
        tok = self._current_token()
        if tok.type in (TokenType.KEYWORD_OTHERWISE, TokenType.KEYWORD_ENDCASE, TokenType.EOF):
            return True
        if tok.type in (TokenType.INTEGER_LITERAL, TokenType.REAL_LITERAL,
                        TokenType.STRING_LITERAL, TokenType.CHAR_LITERAL,
                        TokenType.BOOLEAN_LITERAL):
            nt = self._peek()
            return nt.type in (TokenType.COLON, TokenType.KEYWORD_TO)
        if tok.type == TokenType.IDENTIFIER:
            nt = self._peek()
            return nt.type in (TokenType.COLON, TokenType.KEYWORD_TO)
        return False

    def _parse_case(self):
        self._eat(TokenType.KEYWORD_CASE)
        self._eat(TokenType.KEYWORD_OF)
        id_tok = self._eat(TokenType.IDENTIFIER)
        expr = IdentifierNode(id_tok.value, id_tok)
        branches = []
        otherwise_block = None
        while self._current_token().type not in (TokenType.KEYWORD_ENDCASE, TokenType.EOF):
            if self._current_token().type == TokenType.KEYWORD_OTHERWISE:
                self._eat(TokenType.KEYWORD_OTHERWISE)
                self._eat(TokenType.COLON)
                stmts = []
                while self._current_token().type not in (TokenType.KEYWORD_ENDCASE, TokenType.EOF):
                    self._collect_stmt(stmts)
                otherwise_block = stmts
                break
            value = self._parse_expression()
            range_end = None
            if self._current_token().type == TokenType.KEYWORD_TO:
                self._eat(TokenType.KEYWORD_TO)
                range_end = self._parse_expression()
            self._eat(TokenType.COLON)
            stmts = []
            while not self._at_case_boundary():
                self._collect_stmt(stmts)
            branches.append(CaseBranch(value, range_end, stmts))
        self._eat(TokenType.KEYWORD_ENDCASE)
        return CaseNode(expr, branches, otherwise_block)

    # ── loops ──
    def _parse_for_statement(self):
        self._eat(TokenType.KEYWORD_FOR)
        var_tok = self._eat(TokenType.IDENTIFIER)
        variable = IdentifierNode(var_tok.value, var_tok)
        self._eat(TokenType.ASSIGN)
        start = self._parse_expression()
        self._eat(TokenType.KEYWORD_TO)
        end = self._parse_expression()
        step = None
        if self._current_token().type == TokenType.KEYWORD_STEP:
            self._eat(TokenType.KEYWORD_STEP)
            step = self._parse_expression()
        body = []
        while self._current_token().type not in (TokenType.KEYWORD_NEXT, TokenType.EOF):
            self._collect_stmt(body)
        self._eat(TokenType.KEYWORD_NEXT)
        if self._current_token().type == TokenType.IDENTIFIER:
            nv = self._eat(TokenType.IDENTIFIER)
            if nv.value != variable.name:
                self._error(f"FOR variable '{variable.name}' does not match NEXT variable '{nv.value}'.", nv,
                            suggestion=f"Change to 'NEXT {variable.name}'.")
        return ForNode(variable, start, end, step, body)

    def _parse_while_statement(self):
        self._eat(TokenType.KEYWORD_WHILE)
        cond = self._parse_expression()
        if self._current_token().type == TokenType.KEYWORD_DO:
            self._warning("'DO' is not part of standard CAIE WHILE syntax.",
                          suggestion="Use: WHILE <condition> ... ENDWHILE (without DO).")
            self._advance()
        body = []
        while self._current_token().type not in (TokenType.KEYWORD_ENDWHILE, TokenType.EOF):
            self._collect_stmt(body)
        self._eat(TokenType.KEYWORD_ENDWHILE)
        return WhileNode(cond, body)

    def _parse_repeat_statement(self):
        self._eat(TokenType.KEYWORD_REPEAT)
        body = []
        while self._current_token().type not in (TokenType.KEYWORD_UNTIL, TokenType.EOF):
            self._collect_stmt(body)
        self._eat(TokenType.KEYWORD_UNTIL)
        cond = self._parse_expression()
        return RepeatNode(body, cond)

    # ── PROCEDURE / FUNCTION ──
    def _parse_param_list(self):
        params = []
        pass_by = "BYVAL"
        while True:
            if self._current_token().type in (TokenType.KEYWORD_BYVAL, TokenType.KEYWORD_BYREF):
                pass_by = self._current_token().value
                self._advance()
            names = [self._eat(TokenType.IDENTIFIER)]
            while self._current_token().type == TokenType.COMMA:
                saved_pos = self.current_token_index
                self._eat(TokenType.COMMA)
                if self._current_token().type == TokenType.IDENTIFIER and self._peek().type in (TokenType.COMMA, TokenType.COLON):
                    names.append(self._eat(TokenType.IDENTIFIER))
                else:
                    self.current_token_index = saved_pos
                    break
            self._eat(TokenType.COLON)
            tp = self._eat_type()
            for nt in names:
                params.append({"name": nt.value, "type": tp.value, "pass_by": pass_by})
            if self._current_token().type != TokenType.COMMA:
                break
            self._eat(TokenType.COMMA)
        return params

    def _parse_procedure(self):
        self._eat(TokenType.KEYWORD_PROCEDURE)
        if self._current_token().type == TokenType.KEYWORD_NEW:
            name_tok = self._current_token()
            self._advance()
        else:
            name_tok = self._eat(TokenType.IDENTIFIER)
        self._eat(TokenType.LPAREN)
        params = []
        if self._current_token().type != TokenType.RPAREN:
            params = self._parse_param_list()
        self._eat(TokenType.RPAREN)
        self._initialize_scope()
        for p in params:
            self.symbol_table[p["name"]] = {"type": p.get("type", "ANY"), "array_spec": None}
        body = []
        while self._current_token().type not in (TokenType.KEYWORD_ENDPROCEDURE, TokenType.EOF):
            self._collect_stmt(body)
        self._eat(TokenType.KEYWORD_ENDPROCEDURE)
        self._finalize_scope()
        return ProcedureNode(name_tok.value, params, body)

    def _parse_function_def(self):
        self._eat(TokenType.KEYWORD_FUNCTION)
        if self._current_token().type == TokenType.KEYWORD_NEW:
            name_tok = self._current_token()
            self._advance()
        else:
            name_tok = self._eat(TokenType.IDENTIFIER)
        self._eat(TokenType.LPAREN)
        params = []
        if self._current_token().type != TokenType.RPAREN:
            params = self._parse_param_list()
        self._eat(TokenType.RPAREN)
        self._eat(TokenType.KEYWORD_RETURNS)
        ret_type = self._eat_type()
        self._initialize_scope()
        for p in params:
            self.symbol_table[p["name"]] = {"type": p.get("type", "ANY"), "array_spec": None}
        body = []
        while self._current_token().type not in (TokenType.KEYWORD_ENDFUNCTION, TokenType.EOF):
            self._collect_stmt(body)
        self._eat(TokenType.KEYWORD_ENDFUNCTION)
        self._finalize_scope()
        return FunctionDefNode(name_tok.value, params, ret_type.value, body)

    def _parse_call_statement(self):
        self._eat(TokenType.KEYWORD_CALL)
        name_tok = self._eat(TokenType.IDENTIFIER)
        name = name_tok.value
        while self._current_token().type == TokenType.DOT:
            self._eat(TokenType.DOT)
            ft = self._eat(TokenType.IDENTIFIER)
            name = f"{name}.{ft.value}"
        args = []
        if self._current_token().type == TokenType.LPAREN:
            self._eat(TokenType.LPAREN)
            if self._current_token().type != TokenType.RPAREN:
                args.append(self._parse_expression())
                while self._current_token().type == TokenType.COMMA:
                    self._eat(TokenType.COMMA)
                    args.append(self._parse_expression())
            self._eat(TokenType.RPAREN)
        return CallNode(name, args)

    def _parse_return(self):
        self._eat(TokenType.KEYWORD_RETURN)
        value = self._parse_expression()
        return ReturnNode(value)

    # ── TYPE / DEFINE / CLASS ──
    def _parse_type_def(self):
        self._eat(TokenType.KEYWORD_TYPE)
        name_tok = self._eat(TokenType.IDENTIFIER)
        if self._current_token().type == TokenType.EQUALS:
            self._eat(TokenType.EQUALS)
            if self._current_token().type == TokenType.LPAREN:
                return self._parse_enum_type(name_tok.value)
            if self._current_token().type == TokenType.CARET:
                return self._parse_pointer_type(name_tok.value)
            if self._current_token().type == TokenType.KEYWORD_SET:
                return self._parse_set_type(name_tok.value)
            self._error("Expected '(', '^', or 'SET' after '='.")
            raise SyntaxError("Invalid type definition")
        return self._parse_record_type(name_tok.value)

    def _parse_enum_type(self, name):
        self._eat(TokenType.LPAREN)
        values = [self._eat(TokenType.IDENTIFIER).value]
        while self._current_token().type == TokenType.COMMA:
            self._eat(TokenType.COMMA)
            values.append(self._eat(TokenType.IDENTIFIER).value)
        self._eat(TokenType.RPAREN)
        return EnumTypeNode(name, values)

    def _parse_pointer_type(self, name):
        self._eat(TokenType.CARET)
        tp = self._eat_type()
        return PointerTypeNode(name, tp.value)

    def _parse_set_type(self, name):
        self._eat(TokenType.KEYWORD_SET)
        self._eat(TokenType.KEYWORD_OF)
        tp = self._eat_type()
        return SetTypeNode(name, tp.value)

    def _parse_record_type(self, name):
        fields = []
        while self._current_token().type not in (TokenType.KEYWORD_ENDTYPE, TokenType.EOF):
            if self._current_token().type == TokenType.KEYWORD_DECLARE:
                result = self._parse_declaration()
                if isinstance(result, list):
                    fields.extend(result)
                else:
                    fields.append(result)
            else:
                self._error("Expected 'DECLARE' inside TYPE definition.")
                raise SyntaxError("Invalid record field")
        self._eat(TokenType.KEYWORD_ENDTYPE)
        return RecordTypeNode(name, fields)

    def _parse_define(self):
        self._eat(TokenType.KEYWORD_DEFINE)
        name_tok = self._eat(TokenType.IDENTIFIER)
        self._eat(TokenType.LPAREN)
        values = [self._parse_expression()]
        while self._current_token().type == TokenType.COMMA:
            self._eat(TokenType.COMMA)
            values.append(self._parse_expression())
        self._eat(TokenType.RPAREN)
        self._eat(TokenType.COLON)
        type_tok = self._eat(TokenType.IDENTIFIER)
        return DefineNode(name_tok.value, values, type_tok.value)

    def _parse_class(self):
        self._eat(TokenType.KEYWORD_CLASS)
        name_tok = self._eat(TokenType.IDENTIFIER)
        parent = None
        if self._current_token().type == TokenType.KEYWORD_INHERITS:
            self._eat(TokenType.KEYWORD_INHERITS)
            parent = self._eat(TokenType.IDENTIFIER).value
        self._initialize_scope()
        members = []
        while self._current_token().type not in (TokenType.KEYWORD_ENDCLASS, TokenType.EOF):
            access = "PUBLIC"
            if self._current_token().type in (TokenType.KEYWORD_PUBLIC, TokenType.KEYWORD_PRIVATE):
                access = self._current_token().value
                self._advance()
            tt = self._current_token().type
            if tt == TokenType.KEYWORD_PROCEDURE:
                members.append(("method", access, self._parse_procedure()))
            elif tt == TokenType.KEYWORD_FUNCTION:
                members.append(("method", access, self._parse_function_def()))
            elif tt == TokenType.KEYWORD_DECLARE:
                result = self._parse_declaration()
                if isinstance(result, list):
                    for decl in result:
                        members.append(("field", access, decl))
                else:
                    members.append(("field", access, result))
            elif tt == TokenType.IDENTIFIER:
                if self._peek().type == TokenType.COLON:
                    id_tok = self._eat(TokenType.IDENTIFIER)
                    self._eat(TokenType.COLON)
                    tp = self._eat_type()
                    id_node = IdentifierNode(id_tok.value, id_tok)
                    members.append(("field", access, DeclarationNode(id_node, tp.value)))
                else:
                    members.append(("init_stmt", access, self._parse_assignment_or_call()))
            else:
                self._error(f"Unexpected token in class body: '{self._current_token().value}'.")
                raise SyntaxError("Invalid class member")
        self._eat(TokenType.KEYWORD_ENDCLASS)
        self._finalize_scope()
        return ClassNode(name_tok.value, parent, members)

    # ── expressions ──
    def _parse_expression(self):
        return self._parse_logical_or()

    def _parse_logical_or(self):
        node = self._parse_logical_and()
        while self._current_token().type == TokenType.KEYWORD_OR:
            op = self._eat(TokenType.KEYWORD_OR)
            node = BinaryOpNode(node, op, self._parse_logical_and())
        return node

    def _parse_logical_and(self):
        node = self._parse_comparison()
        while self._current_token().type == TokenType.KEYWORD_AND:
            op = self._eat(TokenType.KEYWORD_AND)
            node = BinaryOpNode(node, op, self._parse_comparison())
        return node

    def _parse_comparison(self):
        node = self._parse_term()
        comp_ops = {TokenType.EQUALS, TokenType.NOT_EQUALS, TokenType.LESS_THAN,
                    TokenType.LESS_EQUAL, TokenType.GREATER_THAN, TokenType.GREATER_EQUAL}
        if self._current_token().type in comp_ops:
            op = self._current_token()
            self._advance()
            node = BinaryOpNode(node, op, self._parse_term())
        return node

    def _parse_term(self):
        node = self._parse_factor()
        while self._current_token().type in (TokenType.PLUS, TokenType.MINUS, TokenType.AMPERSAND):
            op = self._current_token()
            self._advance()
            node = BinaryOpNode(node, op, self._parse_factor())
        return node

    def _parse_factor(self):
        node = self._parse_unary()
        ops = {TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.KEYWORD_DIV, TokenType.KEYWORD_MOD}
        while self._current_token().type in ops:
            op = self._current_token()
            self._advance()
            node = BinaryOpNode(node, op, self._parse_unary())
        return node

    def _parse_unary(self):
        tok = self._current_token()
        if tok.type == TokenType.KEYWORD_NOT:
            self._advance()
            return UnaryOpNode(tok, self._parse_unary())
        if tok.type == TokenType.MINUS:
            self._advance()
            return UnaryOpNode(tok, self._parse_unary())
        return self._parse_power()

    def _parse_power(self):
        node = self._parse_primary()
        if self._current_token().type == TokenType.CARET:
            op = self._current_token()
            self._advance()
            node = BinaryOpNode(node, op, self._parse_power())
        return node

    def _parse_primary(self):
        tok = self._current_token()
        if tok.type == TokenType.INTEGER_LITERAL:
            self._advance(); return IntegerLiteralNode(tok.value, tok)
        if tok.type == TokenType.REAL_LITERAL:
            self._advance(); return RealLiteralNode(tok.value, tok)
        if tok.type == TokenType.STRING_LITERAL:
            self._advance(); return StringLiteralNode(tok.value, tok)
        if tok.type == TokenType.CHAR_LITERAL:
            self._advance(); return CharLiteralNode(tok.value, tok)
        if tok.type == TokenType.BOOLEAN_LITERAL:
            self._advance(); return BooleanLiteralNode(tok.value.upper() == "TRUE", tok)
        if tok.type == TokenType.IDENTIFIER:
            return self._parse_access_chain()
        if tok.type == TokenType.LPAREN:
            self._eat(TokenType.LPAREN)
            expr = self._parse_expression()
            self._eat(TokenType.RPAREN)
            return expr
        if tok.type == TokenType.KEYWORD_NEW:
            self._advance()
            cls_tok = self._eat(TokenType.IDENTIFIER)
            self._eat(TokenType.LPAREN)
            args = []
            if self._current_token().type != TokenType.RPAREN:
                args.append(self._parse_expression())
                while self._current_token().type == TokenType.COMMA:
                    self._eat(TokenType.COMMA)
                    args.append(self._parse_expression())
            self._eat(TokenType.RPAREN)
            return NewExpressionNode(cls_tok.value, args, tok)
        if tok.type == TokenType.KEYWORD_SUPER:
            self._advance()
            node = IdentifierNode("super", tok)
            if self._current_token().type == TokenType.DOT:
                self._eat(TokenType.DOT)
                if self._current_token().type == TokenType.KEYWORD_NEW:
                    ft = self._current_token()
                    self._advance()
                else:
                    ft = self._eat(TokenType.IDENTIFIER)
                node = DotAccessNode(node, IdentifierNode(ft.value, ft))
                if self._current_token().type == TokenType.LPAREN:
                    self._eat(TokenType.LPAREN)
                    args = []
                    if self._current_token().type != TokenType.RPAREN:
                        args.append(self._parse_expression())
                        while self._current_token().type == TokenType.COMMA:
                            self._eat(TokenType.COMMA)
                            args.append(self._parse_expression())
                    self._eat(TokenType.RPAREN)
                    node = FunctionCallNode(node, args, tok)
            return node
        self._error(f"Unexpected token in expression: '{tok.value}'.", tok,
                    suggestion="Expected a number, string, char, boolean, identifier, or '(' here.")
        raise SyntaxError("Invalid expression")
