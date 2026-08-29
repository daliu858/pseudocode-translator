"""Compile and execute CAIE file-handling programs against a workspace folder."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from compiler import compile_pseudocode, ErrorSeverity
from ide.runner import execute_python


COPY_PROGRAM = """\
DECLARE LineOfText : STRING
OPENFILE "FileA.txt" FOR READ
OPENFILE "FileB.txt" FOR WRITE
WHILE NOT EOF("FileA.txt")
    READFILE "FileA.txt", LineOfText
    IF LineOfText = "" THEN
        WRITEFILE "FileB.txt", " ----------------------------"
    ELSE
        WRITEFILE "FileB.txt", LineOfText
    ENDIF
ENDWHILE
CLOSEFILE "FileA.txt"
CLOSEFILE "FileB.txt"
OUTPUT "done"
"""

APPEND_PROGRAM = """\
DECLARE FileData : STRING
FileData <- "event-1"
OPENFILE "LoginFile.txt" FOR APPEND
WRITEFILE "LoginFile.txt", FileData
CLOSEFILE "LoginFile.txt"
"""

RANDOM_PROGRAM = """\
TYPE Student
    DECLARE LastName : STRING
    DECLARE YearGroup : INTEGER
ENDTYPE
DECLARE NewPupil : Student
DECLARE Pupil : Student
NewPupil.LastName <- "Johnson"
NewPupil.YearGroup <- 6
OPENFILE "StudentFile.Dat" FOR RANDOM
SEEK "StudentFile.Dat", 1
PUTRECORD "StudentFile.Dat", NewPupil
SEEK "StudentFile.Dat", 1
GETRECORD "StudentFile.Dat", Pupil
OUTPUT Pupil.LastName
OUTPUT Pupil.YearGroup
CLOSEFILE "StudentFile.Dat"
"""


def _compile_ok(source: str) -> str:
    tokens, ast, python_code, errors = compile_pseudocode(source)
    real_errors = [error for error in errors if error.severity == ErrorSeverity.ERROR]
    if real_errors:
        raise AssertionError(real_errors)
    if ast is None:
        raise AssertionError("parser returned no AST")
    return python_code


class FileHandlingCompilerTests(unittest.TestCase):
    def test_official_guide_copy_compiles(self):
        python_code = _compile_ok(COPY_PROGRAM)
        self.assertIn("_caie_files.openfile", python_code)
        self.assertIn("_caie_files.eof", python_code)

    def test_unquoted_identifier_filename_without_declaration(self):
        python_code = _compile_ok(
            'OPENFILE OldFile FOR READ\nCLOSEFILE OldFile\n'
        )
        self.assertIn("openfile('OldFile'", python_code)
        python_code = _compile_ok(
            'OPENFILE FileA.txt FOR READ\nCLOSEFILE FileA.txt\n'
        )
        self.assertIn("openfile('FileA.txt'", python_code)


class FileHandlingRuntimeTests(unittest.TestCase):
    def test_sequential_copy_and_blank_line_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "FileA.txt").write_text(
                "alpha\nbeta\n\ngamma\n", encoding="utf-8", newline="\n"
            )
            result = execute_python(
                _compile_ok(COPY_PROGRAM),
                workspace=workspace,
            )
            self.assertEqual(result["stderr"], "", result["stderr"])
            self.assertEqual(result["exitCode"], 0)
            self.assertEqual(result["stdout"].strip(), "done")
            copied = (workspace / "FileB.txt").read_text(encoding="utf-8")
            self.assertEqual(
                copied.splitlines(),
                ["alpha", "beta", " ----------------------------", "gamma"],
            )

    def test_append_creates_file(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            result = execute_python(
                _compile_ok(APPEND_PROGRAM),
                workspace=workspace,
            )
            self.assertEqual(result["exitCode"], 0, result["stderr"])
            self.assertEqual(
                (workspace / "LoginFile.txt").read_text(encoding="utf-8").splitlines(),
                ["event-1"],
            )

    def test_random_put_and_get_record(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            result = execute_python(
                _compile_ok(RANDOM_PROGRAM),
                workspace=workspace,
            )
            self.assertEqual(result["exitCode"], 0, result["stderr"])
            self.assertEqual(result["stdout"].splitlines(), ["Johnson", "6"])
            stored = json.loads(
                (workspace / "StudentFile.Dat").read_text(encoding="utf-8")
            )
            self.assertEqual(stored[0]["LastName"], "Johnson")
            self.assertEqual(stored[0]["YearGroup"], 6)

    def test_unquoted_identifier_is_the_filename(self):
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder)
            (workspace / "OldFile").write_text("keep\n", encoding="utf-8")
            source = """\
DECLARE Line : STRING
OPENFILE OldFile FOR READ
READFILE OldFile, Line
CLOSEFILE OldFile
OUTPUT Line
"""
            result = execute_python(_compile_ok(source), workspace=workspace)
            self.assertEqual(result["exitCode"], 0, result["stderr"])
            self.assertEqual(result["stdout"].strip(), "keep")

    def test_path_escape_is_rejected(self):
        python_code = _compile_ok(
            'OPENFILE "../secret.txt" FOR WRITE\nCLOSEFILE "../secret.txt"\n'
        )
        with tempfile.TemporaryDirectory() as folder:
            result = execute_python(python_code, workspace=Path(folder))
            self.assertNotEqual(result["exitCode"], 0)
            self.assertIn("workspace folder", result["stderr"])


if __name__ == "__main__":
    unittest.main()
