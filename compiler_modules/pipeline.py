"""
编译流水线入口。
"""

from .tokens import tokenizer
from .parser import Parser
from .codegen import PythonCodeGenerator


def compile_to_python(source_code: str):
    """
    Return tuple: (success, python_code, parse_errors).
    """
    tokens = tokenizer(source_code)
    parser = Parser(tokens)
    ast = parser.parse()

    generator = PythonCodeGenerator()
    py_code = generator.generate(ast)

    success = ast is not None and not parser.errors
    return success, py_code, parser.errors


