"""Regex-based ("master regular expression") tokenizer — a FEATURE-EQUIVALENT
rival to the hand-coded `lexer.py`.

This is a lexer-design experiment (see `docs/词法分析方案对比报告.md`):
build the *best possible* regex-based front end — one that fully replicates
every special case of the hand-coded scanner (proactive error detection,
self-healing, severity levels, line/column pointers, multi-error recovery) —
and see whether the regex version is actually *simpler*.

It uses the canonical Python-docs idiom: one master regex of named groups,
driven by `re.finditer`, plus a `MISMATCH` catch-all. Recognition is done by
regexes; everything else (the part that actually delivers the diagnostics) is
imperative action code — exactly the same imperative code the hand-coded
version has, PLUS the extra machinery the regex idiom forces on you:
ordered alternatives to emulate maximal munch, and offset -> line/column
reconstruction.

`tokenizer(source, errors=None)` is a drop-in replacement for
`lexer.tokenizer`: same Token stream, same CompileError stream.
"""
import re
from bisect import bisect_right

from errors import ErrorSeverity, CompileError
from tokens import TokenType, Token, KEYWORDS


# ── single-char map (identical to lexer.py) ──────────────────────────────
_SINGLE_CHAR_MAP = {
    '=': TokenType.EQUALS, '+': TokenType.PLUS, '*': TokenType.MULTIPLY,
    '/': TokenType.DIVIDE, '(': TokenType.LPAREN, ')': TokenType.RPAREN,
    '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
    ',': TokenType.COMMA, ':': TokenType.COLON, '.': TokenType.DOT,
    '&': TokenType.AMPERSAND, '^': TokenType.CARET,
}

_CHINESE_PUNCT = {
    '：': (':', 'colon'), '，': (',', 'comma'),
    '；': (';', 'semicolon'),
    '“': ('"', 'opening quote'), '”': ('"', 'closing quote'),
    '（': ('(', 'left parenthesis'), '）': (')', 'right parenthesis'),
    '【': ('[', 'left bracket'), '】': (']', 'right bracket'),
    '。': ('.', 'period'),
}

# Char-literal delimiters: regular ', curly quotes, saltillo.
_CD = r"'‘’Ꞌꞌ"          # inside a character class
_NOT_CD = r"[^" + _CD + r"\n]"               # one char that is none of them


# ── the master regex: ORDER IS SEMANTICS ─────────────────────────────────
# Because Python `re` alternation is ordered choice (first matching branch
# wins, NOT longest across branches), every multi-char form MUST be listed
# before its single-char prefix to emulate the scanner's maximal munch.
_TOKEN_SPEC = [
    ('COMMENT',       r'//[^\n]*'),                    # // ...  (before SLASH)
    ('HASHCOMMENT',   r'\#[^\n]*'),                    # #  -> error, skip line
    ('NEWLINE',       r'\n'),
    ('SKIP',          r'[^\S\n]+'),                    # whitespace except \n
    ('STRING',        r'"[^"]*"'),                     # closed (may span \n)
    ('STRING_UNTERM', r'"[^"]*'),                      # unterminated -> EOF
    ('CHARLIT',       r"[" + _CD + r"]" + _NOT_CD + r"*[" + _CD + r"]"),  # closed
    ('CHAR_UNTERM',   r"[" + _CD + r"]" + _NOT_CD + r"*"),                # unterminated
    ('REAL',          r'\d+\.\d*|\.\d+'),              # before INT and DOT
    ('INT',           r'\d+'),
    ('ID',            r'[^\W\d]\w*'),                  # ident / keyword (unicode)
    ('ASSIGN',        r'<-'),
    ('LE',            r'<='),
    ('NE',            r'<>'),
    ('LT',            r'<'),
    ('GE',            r'>='),
    ('GT',            r'>'),
    ('EQEQ',          r'=='),                          # -> warn, heal '='
    ('NEPY',          r'!='),                          # -> error, heal '<>'
    ('ARROWR',        r'->'),                          # -> error, heal '<-'
    ('COLONEQ',       r':='),                          # -> error, heal '<-'
    ('UARROW',        r'←'),                      # ← -> ASSIGN
    ('ENDASH',        r'–'),                      # – -> warn, heal '-'
    ('SEMI',          r';'),                           # -> warn, skip
    ('EQ',            r'='),
    ('PLUS',          r'\+'),
    ('STAR',          r'\*'),
    ('SLASH',         r'/'),
    ('LPAREN',        r'\('),
    ('RPAREN',        r'\)'),
    ('LBRACK',        r'\['),
    ('RBRACK',        r'\]'),
    ('COMMA',         r','),
    ('COLON',         r':'),
    ('DOT',           r'\.'),
    ('AMP',           r'&'),
    ('CARET',         r'\^'),
    ('MINUS',         r'-'),
    ('CJK',           r'[：，；“”（）【】。]'),
    ('MISMATCH',      r'.'),
]
_MASTER = re.compile('|'.join('(?P<%s>%s)' % p for p in _TOKEN_SPEC))

# kind -> (TokenType, value) for the trivial operators/punctuation
_SIMPLE = {
    'ASSIGN': (TokenType.ASSIGN, '<-'), 'LE': (TokenType.LESS_EQUAL, '<='),
    'NE': (TokenType.NOT_EQUALS, '<>'), 'LT': (TokenType.LESS_THAN, '<'),
    'GE': (TokenType.GREATER_EQUAL, '>='), 'GT': (TokenType.GREATER_THAN, '>'),
    'UARROW': (TokenType.ASSIGN, '<-'),
    'EQ': (TokenType.EQUALS, '='), 'PLUS': (TokenType.PLUS, '+'),
    'STAR': (TokenType.MULTIPLY, '*'), 'SLASH': (TokenType.DIVIDE, '/'),
    'LPAREN': (TokenType.LPAREN, '('), 'RPAREN': (TokenType.RPAREN, ')'),
    'LBRACK': (TokenType.LBRACKET, '['), 'RBRACK': (TokenType.RBRACKET, ']'),
    'COMMA': (TokenType.COMMA, ','), 'COLON': (TokenType.COLON, ':'),
    'DOT': (TokenType.DOT, '.'), 'AMP': (TokenType.AMPERSAND, '&'),
    'CARET': (TokenType.CARET, '^'), 'MINUS': (TokenType.MINUS, '-'),
}

# kind -> (severity, message, suggestion, heal TokenType, heal value)
_PROACTIVE = {
    'EQEQ':    (ErrorSeverity.WARNING, "'==' is not valid in pseudocode.",
                "Use '=' for comparison.", TokenType.EQUALS, '='),
    'NEPY':    (ErrorSeverity.ERROR, "'!=' is not valid in pseudocode.",
                "Use '<>' for not-equals comparison.", TokenType.NOT_EQUALS, '<>'),
    'ARROWR':  (ErrorSeverity.ERROR, "'->' is not valid in pseudocode.",
                "The assignment arrow points LEFT: use '<-'.", TokenType.ASSIGN, '<-'),
    'COLONEQ': (ErrorSeverity.ERROR, "':=' is not valid in pseudocode.",
                "Use '<-' for assignment. ':=' is Pascal syntax.", TokenType.ASSIGN, '<-'),
    'ENDASH':  (ErrorSeverity.WARNING, "Detected en-dash '–' instead of minus '-'.",
                "Use the standard minus sign '-'.", TokenType.MINUS, '-'),
}


def tokenizer(source_code: str, errors=None):
    tokens = []
    if errors is None:
        errors = []
    source_lines = source_code.split('\n')

    # offset -> (line, column): the machinery the hand-coded scanner gets for
    # free from its running cursor, but a regex/finditer driver must rebuild.
    line_starts = [0]
    for i, c in enumerate(source_code):
        if c == '\n':
            line_starts.append(i + 1)

    def loc(off):
        idx = bisect_right(line_starts, off) - 1
        return idx + 1, off - line_starts[idx] + 1

    def src_line(ln):
        return source_lines[ln - 1] if 0 < ln <= len(source_lines) else None

    def err(sev, off, msg, suggestion=None):
        ln, col = loc(off)
        errors.append(CompileError(sev, ln, col, msg, suggestion=suggestion,
                                   source_line=src_line(ln)))

    for mo in _MASTER.finditer(source_code):
        kind = mo.lastgroup
        text = mo.group()
        off = mo.start()
        ln, col = loc(off)

        # ── things that emit no token ──
        if kind in ('COMMENT', 'NEWLINE', 'SKIP'):
            continue
        if kind == 'HASHCOMMENT':
            err(ErrorSeverity.ERROR, off, "'#' is not a comment symbol in pseudocode.",
                "Use '//' to start a comment.")
            continue
        if kind == 'SEMI':
            err(ErrorSeverity.WARNING, off, "Semicolons are not needed in pseudocode.",
                "Simply remove the ';'. Statements end at line breaks.")
            continue

        # ── trivial operators / punctuation ──
        if kind in _SIMPLE:
            tt, val = _SIMPLE[kind]
            tokens.append(Token(tt, val, ln, col))
            continue

        # ── proactive non-standard detection + self-heal ──
        if kind in _PROACTIVE:
            sev, msg, sug, tt, val = _PROACTIVE[kind]
            err(sev, off, msg, sug)
            tokens.append(Token(tt, val, ln, col))
            continue

        # ── strings ──
        if kind == 'STRING':
            tokens.append(Token(TokenType.STRING_LITERAL, text[1:-1], ln, col))
            continue
        if kind == 'STRING_UNTERM':
            err(ErrorSeverity.ERROR, off, "Unterminated string literal.",
                "Add a closing '\"' to end the string.")
            tokens.append(Token(TokenType.UNKNOWN, f'Unterminated: "{text[1:]}', ln, col))
            continue

        # ── char literals (one regex rule, three semantic outcomes) ──
        if kind == 'CHARLIT':
            inside = text[1:-1]
            if len(inside) == 0:
                err(ErrorSeverity.ERROR, off, "Empty character literal.",
                    "A CHAR literal must contain exactly one character, e.g. 'A'.")
                tokens.append(Token(TokenType.UNKNOWN, "''", ln, col))
            elif len(inside) == 1:
                tokens.append(Token(TokenType.CHAR_LITERAL, inside, ln, col))
            else:
                err(ErrorSeverity.ERROR, off,
                    f"CHAR literal must contain exactly one character, got '{inside}'.",
                    f'Use double quotes for strings: "{inside}"')
                tokens.append(Token(TokenType.STRING_LITERAL, inside, ln, col))
            continue
        if kind == 'CHAR_UNTERM':
            err(ErrorSeverity.ERROR, off, "Unterminated character literal.",
                "CHAR literals use single quotes with one character, e.g. 'A'.")
            tokens.append(Token(TokenType.UNKNOWN, text, ln, col))
            continue

        # ── numbers ──
        if kind == 'REAL':
            try:
                tokens.append(Token(TokenType.REAL_LITERAL, float(text), ln, col))
            except ValueError:
                tokens.append(Token(TokenType.UNKNOWN, text, ln, col))
            continue
        if kind == 'INT':
            try:
                tokens.append(Token(TokenType.INTEGER_LITERAL, int(text), ln, col))
            except ValueError:
                tokens.append(Token(TokenType.UNKNOWN, text, ln, col))
            continue

        # ── identifiers / keywords ──
        if kind == 'ID':
            kw = KEYWORDS.get(text.upper())
            if kw:
                tokens.append(Token(kw, text.upper(), ln, col))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, text, ln, col))
            continue

        # ── Chinese punctuation -> error + heal to ASCII equivalent ──
        if kind == 'CJK':
            ascii_eq, punct_name = _CHINESE_PUNCT[text]
            err(ErrorSeverity.ERROR, off, f"Detected Chinese {punct_name} '{text}'.",
                f"Use the English character '{ascii_eq}' instead.")
            mapped = _SINGLE_CHAR_MAP.get(ascii_eq)
            if mapped:
                tokens.append(Token(mapped, ascii_eq, ln, col))
            else:
                tokens.append(Token(TokenType.UNKNOWN, text, ln, col))
            continue

        # ── unrecognised character ──
        err(ErrorSeverity.ERROR, off, f"Unrecognized character '{text}'.")
        tokens.append(Token(TokenType.UNKNOWN, text, ln, col))

    eln, ecol = loc(len(source_code)) if source_code else (1, 1)
    tokens.append(Token(TokenType.EOF, "EOF", eln, ecol))
    return tokens, errors
