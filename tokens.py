"""词法 token 数据层：TokenType / Token / KEYWORDS。

只依赖标准库（不依赖 errors / ast_nodes）。
这是各阶段之间的"通信契约"之一——tokenizer 产出 Token 列表，
parser 消费它。换一个 front-end（例如正则版 tokenizer）只要产出同样
格式的 Token 列表，下游无需改动。
"""
import collections
from enum import Enum, auto


class TokenType(Enum):
    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    REAL_LITERAL = auto()
    STRING_LITERAL = auto()
    CHAR_LITERAL = auto()
    BOOLEAN_LITERAL = auto()

    KEYWORD_IF = auto()
    KEYWORD_THEN = auto()
    KEYWORD_ELSE = auto()
    KEYWORD_ENDIF = auto()
    KEYWORD_FOR = auto()
    KEYWORD_TO = auto()
    KEYWORD_STEP = auto()
    KEYWORD_NEXT = auto()
    KEYWORD_WHILE = auto()
    KEYWORD_DO = auto()
    KEYWORD_ENDWHILE = auto()
    KEYWORD_REPEAT = auto()
    KEYWORD_UNTIL = auto()
    KEYWORD_CASE = auto()
    KEYWORD_OF = auto()
    KEYWORD_ENDCASE = auto()
    KEYWORD_OTHERWISE = auto()
    KEYWORD_PROCEDURE = auto()
    KEYWORD_ENDPROCEDURE = auto()
    KEYWORD_FUNCTION = auto()
    KEYWORD_RETURNS = auto()
    KEYWORD_RETURN = auto()
    KEYWORD_ENDFUNCTION = auto()
    KEYWORD_CALL = auto()
    KEYWORD_BYVAL = auto()
    KEYWORD_BYREF = auto()
    KEYWORD_INPUT = auto()
    KEYWORD_OUTPUT = auto()
    KEYWORD_PRINT = auto()
    KEYWORD_DECLARE = auto()
    KEYWORD_CONSTANT = auto()
    KEYWORD_ARRAY = auto()
    KEYWORD_TYPE = auto()
    KEYWORD_ENDTYPE = auto()
    KEYWORD_SET = auto()
    KEYWORD_DEFINE = auto()
    KEYWORD_CLASS = auto()
    KEYWORD_ENDCLASS = auto()
    KEYWORD_INHERITS = auto()
    KEYWORD_SUPER = auto()
    KEYWORD_PUBLIC = auto()
    KEYWORD_PRIVATE = auto()
    KEYWORD_NEW = auto()
    KEYWORD_OPENFILE = auto()
    KEYWORD_READFILE = auto()
    KEYWORD_WRITEFILE = auto()
    KEYWORD_CLOSEFILE = auto()
    KEYWORD_SEEK = auto()
    KEYWORD_GETRECORD = auto()
    KEYWORD_PUTRECORD = auto()
    KEYWORD_EOF = auto()

    KEYWORD_AND = auto()
    KEYWORD_OR = auto()
    KEYWORD_NOT = auto()
    KEYWORD_MOD = auto()
    KEYWORD_DIV = auto()

    ASSIGN = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_EQUAL = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    AMPERSAND = auto()
    CARET = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()

    COMMENT = auto()
    UNKNOWN = auto()
    EOF = auto()


Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])


KEYWORDS = {
    "IF": TokenType.KEYWORD_IF, "THEN": TokenType.KEYWORD_THEN,
    "ELSE": TokenType.KEYWORD_ELSE, "ENDIF": TokenType.KEYWORD_ENDIF,
    "FOR": TokenType.KEYWORD_FOR, "TO": TokenType.KEYWORD_TO,
    "STEP": TokenType.KEYWORD_STEP, "NEXT": TokenType.KEYWORD_NEXT,
    "WHILE": TokenType.KEYWORD_WHILE, "DO": TokenType.KEYWORD_DO,
    "ENDWHILE": TokenType.KEYWORD_ENDWHILE,
    "REPEAT": TokenType.KEYWORD_REPEAT, "UNTIL": TokenType.KEYWORD_UNTIL,
    "CASE": TokenType.KEYWORD_CASE, "OF": TokenType.KEYWORD_OF,
    "ENDCASE": TokenType.KEYWORD_ENDCASE, "OTHERWISE": TokenType.KEYWORD_OTHERWISE,
    "PROCEDURE": TokenType.KEYWORD_PROCEDURE, "ENDPROCEDURE": TokenType.KEYWORD_ENDPROCEDURE,
    "FUNCTION": TokenType.KEYWORD_FUNCTION, "RETURNS": TokenType.KEYWORD_RETURNS,
    "RETURN": TokenType.KEYWORD_RETURN, "ENDFUNCTION": TokenType.KEYWORD_ENDFUNCTION,
    "CALL": TokenType.KEYWORD_CALL,
    "BYVAL": TokenType.KEYWORD_BYVAL, "BYVALUE": TokenType.KEYWORD_BYVAL,
    "BYREF": TokenType.KEYWORD_BYREF,
    "INPUT": TokenType.KEYWORD_INPUT, "OUTPUT": TokenType.KEYWORD_OUTPUT,
    "PRINT": TokenType.KEYWORD_PRINT,
    "DECLARE": TokenType.KEYWORD_DECLARE, "CONSTANT": TokenType.KEYWORD_CONSTANT,
    "ARRAY": TokenType.KEYWORD_ARRAY,
    "TYPE": TokenType.KEYWORD_TYPE, "ENDTYPE": TokenType.KEYWORD_ENDTYPE,
    "SET": TokenType.KEYWORD_SET, "DEFINE": TokenType.KEYWORD_DEFINE,
    "CLASS": TokenType.KEYWORD_CLASS, "ENDCLASS": TokenType.KEYWORD_ENDCLASS,
    "INHERITS": TokenType.KEYWORD_INHERITS, "SUPER": TokenType.KEYWORD_SUPER,
    "PUBLIC": TokenType.KEYWORD_PUBLIC, "PRIVATE": TokenType.KEYWORD_PRIVATE,
    "NEW": TokenType.KEYWORD_NEW,
    "OPENFILE": TokenType.KEYWORD_OPENFILE,
    "READFILE": TokenType.KEYWORD_READFILE,
    "WRITEFILE": TokenType.KEYWORD_WRITEFILE,
    "CLOSEFILE": TokenType.KEYWORD_CLOSEFILE,
    "SEEK": TokenType.KEYWORD_SEEK,
    "GETRECORD": TokenType.KEYWORD_GETRECORD,
    "PUTRECORD": TokenType.KEYWORD_PUTRECORD,
    "EOF": TokenType.KEYWORD_EOF,
    "TRUE": TokenType.BOOLEAN_LITERAL, "FALSE": TokenType.BOOLEAN_LITERAL,
    "AND": TokenType.KEYWORD_AND, "OR": TokenType.KEYWORD_OR,
    "NOT": TokenType.KEYWORD_NOT,
    "MOD": TokenType.KEYWORD_MOD, "DIV": TokenType.KEYWORD_DIV,
}
