"""诊断错误数据层。

不依赖任何其他模块（依赖方向的最底层）。
由 compiler.py 通过显式 import 重新导出，保持对外 API 不变。
"""
from enum import Enum


class ErrorSeverity(Enum):
    WARNING = "Warning"
    ERROR = "Error"


class CompileError:
    def __init__(self, severity, line, column, message, suggestion=None, source_line=None):
        self.severity = severity
        self.line = line
        self.column = column
        self.message = message
        self.suggestion = suggestion
        self.source_line = source_line

    def __str__(self):
        prefix = self.severity.value
        result = f"[{prefix}] L{self.line}:C{self.column} - {self.message}"
        if self.suggestion:
            result += f"\n  Hint: {self.suggestion}"
        if self.source_line is not None:
            stripped = self.source_line.rstrip('\n')
            result += f"\n  | {stripped}"
            if self.column > 0:
                result += f"\n  | {' ' * (self.column - 1)}^"
        return result

    def __repr__(self):
        return self.__str__()
