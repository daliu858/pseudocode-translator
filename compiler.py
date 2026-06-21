# Public compatibility layer.
# Data definitions and the three compiler stages live in separate modules;
# this file preserves the historical `from compiler import ...` API.
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
from lexer import tokenizer
from parser import Parser
from codegen import PythonCodeGenerator


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
