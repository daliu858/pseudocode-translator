"""
词法分析模块。
"""

# 中文注释：该处为编译器实现说明。

import collections
from enum import Enum, auto

class TokenType(Enum):
    # 中文注释：该处为编译器实现说明。
    IDENTIFIER = auto()
    INTEGER_LITERAL = auto()
    REAL_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOLEAN_LITERAL = auto() #中文注释：该处为编译器实现说明。

    # 中文注释：该处为编译器实现说明。
    KEYWORD_IF = auto()
    KEYWORD_THEN = auto()
    KEYWORD_ELSE = auto()
    KEYWORD_ENDIF = auto()
    KEYWORD_FOR = auto()
    KEYWORD_TO = auto()
    KEYWORD_STEP = auto()
    KEYWORD_NEXT = auto()
    KEYWORD_WHILE = auto()
    KEYWORD_DO = auto() #中文注释：该处为编译器实现说明。
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
    KEYWORD_OUTPUT = auto()      #中文注释：该处为编译器实现说明。
    KEYWORD_PRINT = auto()       #中文注释：该处为编译器实现说明。
    KEYWORD_DECLARE = auto()
    KEYWORD_CONSTANT = auto()
    KEYWORD_ARRAY = auto()
    KEYWORD_OF = auto()
    KEYWORD_TYPE = auto()        #中文注释：该处为编译器实现说明。

    # 中文注释：该处为编译器实现说明。
    KEYWORD_AND = auto()
    KEYWORD_OR = auto()
    KEYWORD_NOT = auto()
    KEYWORD_MOD = auto() #中文注释：该处为编译器实现说明。
    KEYWORD_DIV = auto() #中文注释：该处为编译器实现说明。

    # 中文注释：该处为编译器实现说明。
    ASSIGN = auto()          #中文注释：该处为编译器实现说明。
    EQUALS = auto()          #中文注释：该处为编译器实现说明。
    NOT_EQUALS = auto()      #中文注释：该处为编译器实现说明。
    LESS_THAN = auto()       #中文注释：该处为编译器实现说明。
    LESS_EQUAL = auto()      #中文注释：该处为编译器实现说明。
    GREATER_THAN = auto()    #中文注释：该处为编译器实现说明。
    GREATER_EQUAL = auto()   #中文注释：该处为编译器实现说明。
    PLUS = auto()            #中文注释：该处为编译器实现说明。
    MINUS = auto()           #中文注释：该处为编译器实现说明。
    MULTIPLY = auto()        #中文注释：该处为编译器实现说明。
    DIVIDE = auto()          #中文注释：该处为编译器实现说明。

    LPAREN = auto()          #中文注释：该处为编译器实现说明。
    RPAREN = auto()          #中文注释：该处为编译器实现说明。
    LBRACKET = auto()        #中文注释：该处为编译器实现说明。
    RBRACKET = auto()        #中文注释：该处为编译器实现说明。
    COMMA = auto()           #中文注释：该处为编译器实现说明。
    COLON = auto()           #中文注释：该处为编译器实现说明。
    DOT = auto()             #中文注释：该处为编译器实现说明。

    # 中文注释：该处为编译器实现说明。
    COMMENT = auto()         #中文注释：该处为编译器实现说明。
    UNKNOWN = auto()         #中文注释：该处为编译器实现说明。
    EOF = auto()             #中文注释：该处为编译器实现说明。

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
    # 中文注释：该处为编译器实现说明。
    "AND": TokenType.KEYWORD_AND,
    "OR": TokenType.KEYWORD_OR,
    "NOT": TokenType.KEYWORD_NOT,
    "MOD": TokenType.KEYWORD_MOD,
    "DIV": TokenType.KEYWORD_DIV
}

def tokenizer(source_code: str):
    tokens = []
    current_pos = 0
    source_length = len(source_code)
    
    current_line = 1
    line_start_pos = 0

    while current_pos < source_length:
        char = source_code[current_pos]
        start_column = current_pos - line_start_pos + 1

        # 中文注释：该处为编译器实现说明。
        if char.isspace():
            if char == '\n':
                current_line += 1
                line_start_pos = current_pos + 1
            current_pos += 1
            continue

        # 中文注释：该处为编译器实现说明。
        if char == '/' and current_pos + 1 < source_length and source_code[current_pos + 1] == '/':
            current_pos += 2 
            while current_pos < source_length and source_code[current_pos] != '\n':
                current_pos += 1
            continue

        # 中文注释：该处为编译器实现说明。
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

        # 中文注释：该处为编译器实现说明。
        if char.isdigit() or (char == '.' and current_pos + 1 < source_length and source_code[current_pos + 1].isdigit()):
            num_str_value = ""
            is_real_num = False
            num_original_start_column = start_column
            
            # 中文注释：该处为编译器实现说明。
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

        # 中文注释：该处为编译器实现说明。
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

        # 中文注释：该处为编译器实现说明。
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
        
        # 中文注释：该处为编译器实现说明。
        tokens.append(Token(TokenType.UNKNOWN, char, current_line, start_column))
        current_pos += 1

    eof_column = current_pos - line_start_pos + 1 if source_length > 0 else 1
    tokens.append(Token(TokenType.EOF, "EOF", current_line, eof_column))
    return tokens

# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。
# 中文注释：该处为编译器实现说明。

