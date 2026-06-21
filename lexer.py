"""Lexical analysis stage.

`tokenizer` converts CIE 9618 pseudocode source into a Token stream and
collects lexical diagnostics.
"""
from errors import ErrorSeverity, CompileError
from tokens import TokenType, Token, KEYWORDS


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
