# ─── 数据层（已拆分为独立模块，此处显式 import 重新导出）───────────────────
# 重构（包 A，受 ROS2 数据契约解耦启发）：
#   errors.py    -> ErrorSeverity / CompileError
#   tokens.py    -> TokenType / Token / KEYWORDS
#   ast_nodes.py -> 全部 AST 节点
# compiler.py 仍是唯一对外入口：`from compiler import ...` 一切照旧，
# 因此 test_runner.py / testclass.py 等无需改动。
from errors import ErrorSeverity, CompileError
from tokens import TokenType, Token, KEYWORDS
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

# Characters accepted as CHAR literal delimiters (regular ', curly quotes, saltillo)
_CHAR_DELIMITERS = frozenset({"'", "\u2018", "\u2019", "\ua78b", "\ua78c"})


def tokenizer(source_code: str, errors=None):
    tokens = []
    if errors is None:
        errors = []
    source_lines = source_code.split('\n')

    current_pos = 0
    source_length = len(source_code)
    current_line = 1
    line_start_pos = 0

    _SINGLE_CHAR_MAP = {
        '=': TokenType.EQUALS, '+': TokenType.PLUS, '*': TokenType.MULTIPLY,
        '/': TokenType.DIVIDE, '(': TokenType.LPAREN, ')': TokenType.RPAREN,
        '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
        ',': TokenType.COMMA, ':': TokenType.COLON, '.': TokenType.DOT,
        '&': TokenType.AMPERSAND, '^': TokenType.CARET,
    }

    _CHINESE_PUNCT = {
        '\uff1a': (':', 'colon'), '\uff0c': (',', 'comma'),
        '\uff1b': (';', 'semicolon'),
        '\u201c': ('"', 'opening quote'), '\u201d': ('"', 'closing quote'),
        '\uff08': ('(', 'left parenthesis'), '\uff09': (')', 'right parenthesis'),
        '\u3010': ('[', 'left bracket'), '\u3011': (']', 'right bracket'),
        '\u3002': ('.', 'period'),
    }

    def _src_line(ln):
        return source_lines[ln - 1] if 0 < ln <= len(source_lines) else None

    while current_pos < source_length:
        char = source_code[current_pos]
        start_column = current_pos - line_start_pos + 1

        # 1. Whitespace
        if char.isspace():
            if char == '\n':
                current_line += 1
                line_start_pos = current_pos + 1
            current_pos += 1
            continue

        # 2. Comments
        if char == '/' and current_pos + 1 < source_length and source_code[current_pos + 1] == '/':
            current_pos += 2
            while current_pos < source_length and source_code[current_pos] != '\n':
                current_pos += 1
            continue

        # 3. String Literals (double-quoted)
        if char == '"':
            str_start_line = current_line
            str_start_col = start_column
            current_pos += 1
            buf = []
            while current_pos < source_length and source_code[current_pos] != '"':
                c = source_code[current_pos]
                buf.append(c)
                if c == '\n':
                    current_line += 1
                    line_start_pos = current_pos + 1
                current_pos += 1
            val = "".join(buf)
            if current_pos < source_length and source_code[current_pos] == '"':
                tokens.append(Token(TokenType.STRING_LITERAL, val, str_start_line, str_start_col))
                current_pos += 1
            else:
                errors.append(CompileError(
                    ErrorSeverity.ERROR, str_start_line, str_start_col,
                    "Unterminated string literal.",
                    suggestion="Add a closing '\"' to end the string.",
                    source_line=_src_line(str_start_line)))
                tokens.append(Token(TokenType.UNKNOWN, f'Unterminated: "{val}', str_start_line, str_start_col))
            continue

        # 4. Char Literals (single-quoted)
        if char in _CHAR_DELIMITERS:
            cl_start_line = current_line
            cl_start_col = start_column
            current_pos += 1
            if current_pos >= source_length or source_code[current_pos] == '\n':
                errors.append(CompileError(ErrorSeverity.ERROR, cl_start_line, cl_start_col,
                    "Unterminated character literal.",
                    suggestion="CHAR literals use single quotes with one character, e.g. 'A'.",
                    source_line=_src_line(cl_start_line)))
                tokens.append(Token(TokenType.UNKNOWN, "'", cl_start_line, cl_start_col))
                continue
            if source_code[current_pos] in _CHAR_DELIMITERS:
                errors.append(CompileError(ErrorSeverity.ERROR, cl_start_line, cl_start_col,
                    "Empty character literal.",
                    suggestion="A CHAR literal must contain exactly one character, e.g. 'A'.",
                    source_line=_src_line(cl_start_line)))
                tokens.append(Token(TokenType.UNKNOWN, "''", cl_start_line, cl_start_col))
                current_pos += 1
                continue
            char_value = source_code[current_pos]
            current_pos += 1
            if current_pos < source_length and source_code[current_pos] in _CHAR_DELIMITERS:
                tokens.append(Token(TokenType.CHAR_LITERAL, char_value, cl_start_line, cl_start_col))
                current_pos += 1
            else:
                extra = char_value
                while current_pos < source_length and source_code[current_pos] not in _CHAR_DELIMITERS and source_code[current_pos] != '\n':
                    extra += source_code[current_pos]
                    current_pos += 1
                if current_pos < source_length and source_code[current_pos] in _CHAR_DELIMITERS:
                    current_pos += 1
                    errors.append(CompileError(ErrorSeverity.ERROR, cl_start_line, cl_start_col,
                        f"CHAR literal must contain exactly one character, got '{extra}'.",
                        suggestion=f'Use double quotes for strings: "{extra}"',
                        source_line=_src_line(cl_start_line)))
                    tokens.append(Token(TokenType.STRING_LITERAL, extra, cl_start_line, cl_start_col))
                else:
                    errors.append(CompileError(ErrorSeverity.ERROR, cl_start_line, cl_start_col,
                        "Unterminated character literal.",
                        suggestion="CHAR literals use single quotes with one character, e.g. 'A'.",
                        source_line=_src_line(cl_start_line)))
                    tokens.append(Token(TokenType.UNKNOWN, f"'{extra}", cl_start_line, cl_start_col))
            continue

        # 5. Numbers
        if char.isdigit() or (char == '.' and current_pos + 1 < source_length and source_code[current_pos + 1].isdigit()):
            num_str = ""
            is_real = False
            num_start_col = start_column
            while current_pos < source_length:
                nc = source_code[current_pos]
                if nc.isdigit():
                    num_str += nc
                elif nc == '.' and not is_real:
                    num_str += nc
                    is_real = True
                else:
                    break
                current_pos += 1
            try:
                if is_real:
                    tokens.append(Token(TokenType.REAL_LITERAL, float(num_str), current_line, num_start_col))
                else:
                    tokens.append(Token(TokenType.INTEGER_LITERAL, int(num_str), current_line, num_start_col))
            except ValueError:
                tokens.append(Token(TokenType.UNKNOWN, num_str, current_line, num_start_col))
            continue

        # 6. Identifiers and Keywords
        if char.isalpha() or char == '_':
            ident = ""
            while current_pos < source_length and (source_code[current_pos].isalnum() or source_code[current_pos] == '_'):
                ident += source_code[current_pos]
                current_pos += 1
            kw = KEYWORDS.get(ident.upper())
            if kw:
                tokens.append(Token(kw, ident.upper(), current_line, start_column))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, ident, current_line, start_column))
            continue

        # 7. Multi-char operators
        processed = False
        if char == '<':
            if current_pos + 1 < source_length:
                nc = source_code[current_pos + 1]
                if nc == '-':
                    tokens.append(Token(TokenType.ASSIGN, "<-", current_line, start_column))
                    current_pos += 2; processed = True
                elif nc == '=':
                    tokens.append(Token(TokenType.LESS_EQUAL, "<=", current_line, start_column))
                    current_pos += 2; processed = True
                elif nc == '>':
                    tokens.append(Token(TokenType.NOT_EQUALS, "<>", current_line, start_column))
                    current_pos += 2; processed = True
            if not processed:
                tokens.append(Token(TokenType.LESS_THAN, "<", current_line, start_column))
                current_pos += 1; processed = True
            if processed:
                continue

        if char == '>':
            if current_pos + 1 < source_length and source_code[current_pos + 1] == '=':
                tokens.append(Token(TokenType.GREATER_EQUAL, ">=", current_line, start_column))
                current_pos += 2; processed = True
            else:
                tokens.append(Token(TokenType.GREATER_THAN, ">", current_line, start_column))
                current_pos += 1; processed = True
            if processed:
                continue

        # 7a. Unicode ← as ASSIGN
        if char == '\u2190':
            tokens.append(Token(TokenType.ASSIGN, "<-", current_line, start_column))
            current_pos += 1
            continue

        # 8. Proactive non-standard detection
        if char == '=' and current_pos + 1 < source_length and source_code[current_pos + 1] == '=':
            errors.append(CompileError(ErrorSeverity.WARNING, current_line, start_column,
                "'==' is not valid in pseudocode.",
                suggestion="Use '=' for comparison.",
                source_line=_src_line(current_line)))
            tokens.append(Token(TokenType.EQUALS, "=", current_line, start_column))
            current_pos += 2
            continue

        if char == '!' and current_pos + 1 < source_length and source_code[current_pos + 1] == '=':
            errors.append(CompileError(ErrorSeverity.ERROR, current_line, start_column,
                "'!=' is not valid in pseudocode.",
                suggestion="Use '<>' for not-equals comparison.",
                source_line=_src_line(current_line)))
            tokens.append(Token(TokenType.NOT_EQUALS, "<>", current_line, start_column))
            current_pos += 2
            continue

        if char == '-' and current_pos + 1 < source_length and source_code[current_pos + 1] == '>':
            errors.append(CompileError(ErrorSeverity.ERROR, current_line, start_column,
                "'->' is not valid in pseudocode.",
                suggestion="The assignment arrow points LEFT: use '<-'.",
                source_line=_src_line(current_line)))
            tokens.append(Token(TokenType.ASSIGN, "<-", current_line, start_column))
            current_pos += 2
            continue

        if char == ':' and current_pos + 1 < source_length and source_code[current_pos + 1] == '=':
            errors.append(CompileError(ErrorSeverity.ERROR, current_line, start_column,
                "':=' is not valid in pseudocode.",
                suggestion="Use '<-' for assignment. ':=' is Pascal syntax.",
                source_line=_src_line(current_line)))
            tokens.append(Token(TokenType.ASSIGN, "<-", current_line, start_column))
            current_pos += 2
            continue

        if char == '#':
            errors.append(CompileError(ErrorSeverity.ERROR, current_line, start_column,
                "'#' is not a comment symbol in pseudocode.",
                suggestion="Use '//' to start a comment.",
                source_line=_src_line(current_line)))
            current_pos += 1
            while current_pos < source_length and source_code[current_pos] != '\n':
                current_pos += 1
            continue

        if char == ';':
            errors.append(CompileError(ErrorSeverity.WARNING, current_line, start_column,
                "Semicolons are not needed in pseudocode.",
                suggestion="Simply remove the ';'. Statements end at line breaks.",
                source_line=_src_line(current_line)))
            current_pos += 1
            continue

        # 8a. EN-DASH → MINUS
        if char == '\u2013':
            errors.append(CompileError(ErrorSeverity.WARNING, current_line, start_column,
                "Detected en-dash '\u2013' instead of minus '-'.",
                suggestion="Use the standard minus sign '-'.",
                source_line=_src_line(current_line)))
            tokens.append(Token(TokenType.MINUS, "-", current_line, start_column))
            current_pos += 1
            continue

        # 9. Single char operators
        sc_type = _SINGLE_CHAR_MAP.get(char)
        if sc_type:
            tokens.append(Token(sc_type, char, current_line, start_column))
            current_pos += 1
            continue

        # 9a. MINUS handled here (after -> check)
        if char == '-':
            tokens.append(Token(TokenType.MINUS, "-", current_line, start_column))
            current_pos += 1
            continue

        # 10. Chinese punctuation
        if char in _CHINESE_PUNCT:
            ascii_eq, punct_name = _CHINESE_PUNCT[char]
            errors.append(CompileError(ErrorSeverity.ERROR, current_line, start_column,
                f"Detected Chinese {punct_name} '{char}'.",
                suggestion=f"Use the English character '{ascii_eq}' instead.",
                source_line=_src_line(current_line)))
            mapped = _SINGLE_CHAR_MAP.get(ascii_eq)
            if mapped:
                tokens.append(Token(mapped, ascii_eq, current_line, start_column))
            else:
                tokens.append(Token(TokenType.UNKNOWN, char, current_line, start_column))
            current_pos += 1
            continue

        # 11. Unknown
        errors.append(CompileError(ErrorSeverity.ERROR, current_line, start_column,
            f"Unrecognized character '{char}'.",
            source_line=_src_line(current_line)))
        tokens.append(Token(TokenType.UNKNOWN, char, current_line, start_column))
        current_pos += 1

    eof_col = current_pos - line_start_pos + 1 if source_length > 0 else 1
    tokens.append(Token(TokenType.EOF, "EOF", current_line, eof_col))
    return tokens, errors


# ─── AST Nodes ──────────────────────────────────────────────────────────
# AST node classes moved to ast_nodes.py (see imports at top of file).


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


# ─── Python Code Generator ──────────────────────────────────────────────
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
        self.scope_stack = [symbol_table if symbol_table is not None else {}]
        self.array_metadata = {}
        self._class_fields = set()
        self._class_types = set()
        self._class_registry = {}
        self._proc_registry = {}
        self.errors = []

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

    def _check_declared(self, var_name):
        if self._lookup(var_name) is None and var_name not in self._class_fields:
            self.errors.append(CompileError(
                ErrorSeverity.ERROR, 0, 0,
                f"Variable '{var_name}' is used but has not been declared.",
                suggestion=f"Add 'DECLARE {var_name} : <type>' before using it."))
            return False
        return True

    def generate(self, program_node):
        if not program_node:
            return "# Error during parsing. No Python code generated."
        self.visit(program_node)
        return "\n".join(self.python_code)

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
            self._declare(var, {"type": "ARRAY", "array_spec": node.array_spec,
                                "item_type": node.array_spec.get("item_type", "INTEGER")})
        else:
            self._declare(var, {"type": node.type_name, "array_spec": None})
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
        self._declare(name, {"type": "CONSTANT", "array_spec": None})
        val = self.visit(node.value)
        self._add_line(f"{name} = {val}")

    def visit_ExpressionStatementNode(self, node):
        self._add_line(self.visit(node.expression))

    # ── statements ──
    def visit_AssignmentNode(self, node):
        if isinstance(node.target, IdentifierNode):
            self._check_declared(node.target.name)
        elif isinstance(node.target, ArrayAccessNode):
            self._check_declared(node.target.identifier.name)
        target = self.visit(node.target)
        value = self.visit(node.value)
        self._add_line(f"{target} = {value}")

    def visit_InputNode(self, node):
        var = self.visit(node.identifier)
        self._check_declared(var)
        info = self._lookup(var) or {"type": "STRING"}
        type_name = info.get("type", "STRING")
        cast = {"INTEGER": "int", "REAL": "float"}.get(type_name)
        prompt = f"'Enter {var} ({type_name}): '"
        if cast:
            self._add_line(f"{var} = {cast}(input({prompt}))")
        else:
            self._add_line(f"{var} = input({prompt})")

    def visit_OutputNode(self, node):
        for e in node.expressions:
            if isinstance(e, IdentifierNode):
                self._check_declared(e.name)
            elif isinstance(e, ArrayAccessNode):
                self._check_declared(e.identifier.name)
        parts = [self.visit(e) for e in node.expressions]
        self._add_line(f"print({', '.join(parts)})")

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
        self._check_declared(var)
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
            self._declare(p["name"], {"type": p.get("type", "ANY"), "array_spec": None,
                                      "pass_by": p.get("pass_by", "BYVAL")})
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
            self._declare(p["name"], {"type": p.get("type", "ANY"), "array_spec": None,
                                      "pass_by": p.get("pass_by", "BYVAL")})
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
        parts = ", ".join(f"{v} = {i}" for i, v in enumerate(node.values))
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
            self._declare(p["name"], {"type": p.get("type", "ANY"), "array_spec": None})
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
        if info and info.get("pass_by") == "BYREF":
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


# ─── Interactive Frontend ────────────────────────────────────────────────
def compile_pseudocode(source_code: str):
    all_errors = []
    tokens, _ = tokenizer(source_code, all_errors)
    parser = Parser(tokens, source_code)
    ast = parser.parse()
    all_errors.extend(parser.errors)
    generator = PythonCodeGenerator(parser.symbol_table)
    python_code = generator.generate(ast)
    all_errors.extend(generator.errors)
    return tokens, ast, python_code, all_errors


def _detect_single_callable(ast):
    """If the program is just one FUNCTION or PROCEDURE (with no other
    executable statements), return (name, params, is_function, return_type).
    Otherwise return None."""
    if ast is None:
        return None
    stmts = ast.statements
    callables = []
    has_other = False
    for s in stmts:
        if isinstance(s, (FunctionDefNode, ProcedureNode)):
            callables.append(s)
        elif isinstance(s, (DeclarationNode, ConstantNode, RecordTypeNode,
                            EnumTypeNode, PointerTypeNode, SetTypeNode,
                            DefineNode, ClassNode)):
            pass
        else:
            has_other = True
    if has_other or len(callables) != 1:
        return None
    c = callables[0]
    is_func = isinstance(c, FunctionDefNode)
    return {
        "name": c.name,
        "params": c.params,
        "is_function": is_func,
        "return_type": c.return_type if is_func else None,
    }


HELP_TEXT = r"""
╔══════════════════════════════════════════════════════════════════════╗
║              CAIE 9618 Pseudocode -> Python 编译器                  ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  请输入 CAIE 伪代码，输入完成后在新的一行输入 END 结束。             ║
║  输入 HELP 查看语法说明，输入 QUIT 退出。                           ║
║  输入 EXAMPLE 1 ~ EXAMPLE 9 加载示例代码。                          ║
║                                                                      ║
║  ╌╌╌╌ 数据类型 ╌╌╌╌                                                 ║
║  INTEGER  REAL  STRING  CHAR  BOOLEAN  DATE                          ║
║                                                                      ║
║  ╌╌╌╌ 变量与常量 ╌╌╌╌                                               ║
║  DECLARE x : INTEGER          DECLARE s : STRING                     ║
║  DECLARE a : ARRAY[1:10] OF INTEGER                                  ║
║  DECLARE b : ARRAY[1:3,1:3] OF CHAR        // 二维数组              ║
║  CONSTANT Pi = 3.14                                                  ║
║                                                                      ║
║  ╌╌╌╌ 赋值 / 输入 / 输出 ╌╌╌╌                                       ║
║  x <- 42          name <- "Alice"          ch <- 'A'                 ║
║  INPUT x           OUTPUT "Hello ", name                             ║
║                                                                      ║
║  ╌╌╌╌ 选择 ╌╌╌╌                                                     ║
║  IF ... THEN ... ELSE ... ENDIF                                      ║
║  CASE OF x  /  value : stmt  /  OTHERWISE : stmt  /  ENDCASE        ║
║                                                                      ║
║  ╌╌╌╌ 循环 ╌╌╌╌                                                     ║
║  FOR i <- 1 TO 10 STEP 2 ... NEXT i                                 ║
║  WHILE cond ... ENDWHILE                                             ║
║  REPEAT ... UNTIL cond                                               ║
║                                                                      ║
║  ╌╌╌╌ 过程与函数 ╌╌╌╌                                               ║
║  PROCEDURE Name(x : INTEGER) ... ENDPROCEDURE                       ║
║  FUNCTION F(x : INTEGER) RETURNS INTEGER ... ENDFUNCTION             ║
║  CALL Name(arg)       RETURN value                                   ║
║  BYVAL / BYREF 参数传递方式                                         ║
║                                                                      ║
║  ╌╌╌╌ 自定义类型 ╌╌╌╌                                               ║
║  TYPE Rec ... ENDTYPE (记录)    TYPE Season = (...) (枚举)           ║
║  TYPE TPtr = ^INTEGER (指针)    TYPE S = SET OF CHAR (集合)          ║
║  DEFINE Vowels ('A','E'): S                                          ║
║                                                                      ║
║  ╌╌╌╌ OOP ╌╌╌╌                                                      ║
║  CLASS Cat INHERITS Pet ... ENDCLASS                                 ║
║  PUBLIC / PRIVATE       SUPER.NEW(...)       obj <- NEW Cat(...)     ║
║                                                                      ║
║  ╌╌╌╌ 运算符 ╌╌╌╌                                                   ║
║  + - * / DIV MOD   = <> < <= > >=   AND OR NOT   & (字符串连接)     ║
║                                                                      ║
║  ╌╌╌╌ 内建函数 ╌╌╌╌                                                 ║
║  LENGTH(s)  RIGHT(s,n)  MID(s,x,y)  LCASE(c)  UCASE(c)             ║
║  INT(x)  RAND(n)                                                     ║
║                                                                      ║
║  ╌╌╌╌ 注释 ╌╌╌╌                                                     ║
║  // 这是注释                                                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

EXAMPLES = [
    {
        "title": "示例1: 基本变量与输出",
        "code": """\
DECLARE greeting : STRING
DECLARE age : INTEGER
greeting <- "Hello, World!"
age <- 18
OUTPUT greeting
OUTPUT "Age is: ", age"""
    },
    {
        "title": "示例2: CONSTANT + IF-ELSE",
        "code": """\
CONSTANT PassMark = 50
DECLARE score : INTEGER
score <- 75
IF score >= PassMark THEN
    OUTPUT "Pass"
ELSE
    OUTPUT "Fail"
ENDIF"""
    },
    {
        "title": "示例3: CASE 语句",
        "code": """\
DECLARE grade : CHAR
grade <- 'A'
CASE OF grade
    'A' : OUTPUT "Excellent"
    'B' : OUTPUT "Good"
    'C' : OUTPUT "Average"
    OTHERWISE : OUTPUT "Below average"
ENDCASE"""
    },
    {
        "title": "示例4: FOR 循环 + 内建函数",
        "code": """\
DECLARE total : INTEGER
DECLARE i : INTEGER
total <- 0
FOR i <- 1 TO 10
    total <- total + i
NEXT i
OUTPUT "Sum = ", total
OUTPUT "Length of 'Hello' = ", LENGTH("Hello")
OUTPUT "MID('ABCDEF',2,3) = ", MID("ABCDEF", 2, 3)"""
    },
    {
        "title": "示例5: WHILE + REPEAT-UNTIL",
        "code": """\
DECLARE count : INTEGER
count <- 1
WHILE count <= 5
    OUTPUT "Count: ", count
    count <- count + 1
ENDWHILE
DECLARE x : INTEGER
x <- 0
REPEAT
    x <- x + 3
UNTIL x >= 12
OUTPUT "x = ", x"""
    },
    {
        "title": "示例6: 2D数组 + 嵌套FOR",
        "code": """\
DECLARE grid : ARRAY[1:3,1:3] OF INTEGER
DECLARE row : INTEGER
DECLARE col : INTEGER
DECLARE val : INTEGER
val <- 1
FOR row <- 1 TO 3
    FOR col <- 1 TO 3
        grid[row, col] <- val
        val <- val + 1
    NEXT col
NEXT row
FOR row <- 1 TO 3
    OUTPUT grid[row, 1], " ", grid[row, 2], " ", grid[row, 3]
NEXT row"""
    },
    {
        "title": "示例7: PROCEDURE + FUNCTION",
        "code": """\
FUNCTION Max(a : INTEGER, b : INTEGER) RETURNS INTEGER
    IF a > b THEN
        RETURN a
    ELSE
        RETURN b
    ENDIF
ENDFUNCTION
PROCEDURE ShowMax(x : INTEGER, y : INTEGER)
    OUTPUT "Max = ", Max(x, y)
ENDPROCEDURE
CALL ShowMax(42, 17)"""
    },
    {
        "title": "示例8: TYPE 记录 + 枚举",
        "code": """\
TYPE Season = (Spring, Summer, Autumn, Winter)
TYPE StudentRecord
    DECLARE Name : STRING
    DECLARE Age : INTEGER
    DECLARE Grade : CHAR
ENDTYPE
DECLARE s : StudentRecord
s.Name <- "Alice"
s.Age <- 17
s.Grade <- 'A'
OUTPUT s.Name, " age ", s.Age, " grade ", s.Grade
DECLARE now : INTEGER
now <- Spring
OUTPUT "Season index: ", now"""
    },
    {
        "title": "示例9: 字符串连接 & + RIGHT/LCASE",
        "code": """\
DECLARE first : STRING
DECLARE last : STRING
DECLARE full : STRING
first <- "John"
last <- "Smith"
full <- first & " " & last
OUTPUT full
OUTPUT "Right 3: ", RIGHT(full, 3)
OUTPUT "Lowercase: ", LCASE('Z')"""
    },
]


def print_separator():
    print("\u2500" * 70)


def run_interactive():
    print(HELP_TEXT)
    while True:
        print_separator()
        print("请输入 CAIE 伪代码 (输入 END 结束, HELP 帮助, QUIT 退出):")
        print_separator()
        lines = []
        while True:
            try:
                line = input("  > ")
            except EOFError:
                return
            stripped = line.strip().upper()
            if stripped == "END":
                break
            if stripped == "QUIT":
                print("\n再见！")
                return
            if stripped == "HELP":
                print(HELP_TEXT)
                lines.clear()
                print("请输入 CAIE 伪代码:")
                continue
            if stripped.startswith("EXAMPLE"):
                parts = stripped.split()
                if len(parts) == 2 and parts[1].isdigit():
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(EXAMPLES):
                        ex = EXAMPLES[idx]
                        print(f"\n  ──── {ex['title']} ────")
                        for el in ex["code"].split("\n"):
                            print(f"  │ {el}")
                        print()
                        lines = ex["code"].split("\n")
                        print("  (已加载示例，输入 END 编译)")
                        continue
                print(f"  可用示例: EXAMPLE 1 ~ EXAMPLE {len(EXAMPLES)}")
                continue
            lines.append(line)

        if not lines:
            print("  (空输入，跳过)")
            continue

        source_code = "\n".join(lines)
        print()
        print("=" * 70)
        print("  源代码:")
        print("=" * 70)
        for i, sl in enumerate(source_code.split("\n"), 1):
            print(f"  {i:3d} | {sl}")

        tokens, ast, python_code, errors = compile_pseudocode(source_code)
        warnings = [e for e in errors if e.severity == ErrorSeverity.WARNING]
        errs = [e for e in errors if e.severity == ErrorSeverity.ERROR]

        if warnings:
            print()
            print_separator()
            print(f"  ⚠ 警告 ({len(warnings)}):")
            print_separator()
            for w in warnings:
                print(f"  {w}")
        if errs:
            print()
            print_separator()
            print(f"  ✖ 错误 ({len(errs)}):")
            print_separator()
            for e in errs:
                print(f"  {e}")
            print()
            print("  编译失败，请检查上方错误信息后重试。")
            continue

        print()
        print("=" * 70)
        print("  生成的 Python 代码:")
        print("=" * 70)
        for i, pl in enumerate(python_code.split("\n"), 1):
            print(f"  {i:3d} | {pl}")
        print("=" * 70)
        print()
        print_separator()
        print("  运行结果:")
        print_separator()

        callable_info = _detect_single_callable(ast)
        try:
            exec_globals = {}
            exec(python_code, exec_globals)

            if callable_info:
                name = callable_info["name"]
                params = callable_info["params"]
                is_func = callable_info["is_function"]
                ret_type = callable_info["return_type"]
                kind = "FUNCTION" if is_func else "PROCEDURE"

                print(f"  检测到单独的 {kind} 定义: {name}")
                if params:
                    print(f"  参数: {', '.join(p['name'] + ' : ' + p['type'] for p in params)}")
                if is_func:
                    print(f"  返回类型: {ret_type}")
                print()
                print(f"  请依次输入参数值来测试 (输入 SKIP 跳过):")
                print_separator()

                while True:
                    arg_values = []
                    skip = False
                    for p in params:
                        try:
                            raw = input(f"  {p['name']} ({p['type']}): ")
                        except EOFError:
                            skip = True
                            break
                        if raw.strip().upper() == "SKIP":
                            skip = True
                            break
                        try:
                            if p["type"] == "INTEGER":
                                arg_values.append(int(raw))
                            elif p["type"] == "REAL":
                                arg_values.append(float(raw))
                            elif p["type"] == "BOOLEAN":
                                arg_values.append(raw.strip().upper() == "TRUE")
                            elif p["type"] == "CHAR":
                                arg_values.append(raw.strip()[0] if raw.strip() else '')
                            else:
                                arg_values.append(raw)
                        except ValueError:
                            print(f"  输入格式错误，请重新输入 {p['type']} 类型的值。")
                            skip = True
                            break
                    if skip:
                        break

                    fn = exec_globals.get(name)
                    if fn and callable(fn):
                        try:
                            result = fn(*arg_values)
                            if is_func and result is not None:
                                args_str = ", ".join(repr(v) for v in arg_values)
                                print(f"  >>> {name}({args_str}) = {repr(result)}")
                        except Exception as exc:
                            print(f"  运行时错误: {exc}")
                    else:
                        print(f"  错误: 未找到函数 {name}")
                        break

                    print()
                    try:
                        again = input("  再测试一组? (回车继续, SKIP 退出): ")
                    except EOFError:
                        break
                    if again.strip().upper() == "SKIP":
                        break
        except Exception as exc:
            print(f"  运行时错误: {exc}")
        print_separator()


if __name__ == "__main__":
    run_interactive()
