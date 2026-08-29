"""Tests for bounded execution of compiler-generated Python.

Run with:  python -m unittest -v test_ide_runner.py
"""

from __future__ import annotations

import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from ide.application import IDEApplication
from ide.runner import MAX_OUTPUT_BYTES, MAX_STDIN_BYTES, execute_python
from ide.server import create_server


class BoundedRunnerTests(unittest.TestCase):
    def test_successful_output_and_unicode(self):
        result = execute_python("print('hello')\nprint('\\u4f60\\u597d')")
        self.assertEqual(result["exitCode"], 0)
        self.assertFalse(result["timedOut"])
        self.assertFalse(result["truncated"])
        self.assertEqual(result["stdout"].splitlines(), ["hello", "你好"])
        self.assertEqual(result["stderr"], "")

    def test_runtime_error_is_captured(self):
        result = execute_python("print(1 / 0)")
        self.assertEqual(result["exitCode"], 1)
        self.assertFalse(result["timedOut"])
        self.assertIn("ZeroDivisionError", result["stderr"])
        self.assertIn("<generated-pseudocode>", result["stderr"])

    def test_timeout_terminates_child(self):
        result = execute_python("while True:\n    pass", timeout_seconds=0.15)
        self.assertTrue(result["timedOut"])
        self.assertIsNone(result["exitCode"])
        # Leave ample room for loaded CI hosts while still detecting a child
        # that was never forcefully terminated.
        self.assertLess(result["elapsedMs"], 2500)

    def test_output_is_truncated_to_combined_byte_budget(self):
        result = execute_python("print('x' * 70000)")
        self.assertEqual(result["exitCode"], 0)
        self.assertTrue(result["truncated"])
        self.assertLessEqual(
            len((result["stdout"] + result["stderr"]).encode("utf-8")),
            MAX_OUTPUT_BYTES,
        )

    def test_stdin_byte_limit(self):
        with self.assertRaisesRegex(ValueError, "stdin is too large"):
            execute_python("pass", "x" * (MAX_STDIN_BYTES + 1))

    def test_generated_code_has_restricted_builtins_and_imports(self):
        no_open = execute_python("open('should-not-exist.txt', 'w')")
        self.assertEqual(no_open["exitCode"], 1)
        self.assertIn("NameError", no_open["stderr"])

        no_os = execute_python("__import__('os')")
        self.assertEqual(no_os["exitCode"], 1)
        self.assertIn("may only import 'random'", no_os["stderr"])

        random_allowed = execute_python(
            "print(__import__('random').random() >= 0)"
        )
        self.assertEqual(random_allowed["exitCode"], 0)
        self.assertEqual(random_allowed["stdout"].strip(), "True")

        random_does_not_leak_its_os_module = execute_python(
            "print(__import__('random')._os)"
        )
        self.assertEqual(random_does_not_leak_its_os_module["exitCode"], 1)
        self.assertIn("AttributeError", random_does_not_leak_its_os_module["stderr"])


class IDEApplicationRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = IDEApplication.from_release()

    def test_compiles_then_runs_with_input(self):
        source = "DECLARE value : INTEGER\nINPUT value\nOUTPUT value"
        result = self.application.run(source, "42\n")
        self.assertTrue(result["ok"])
        self.assertEqual(result["exitCode"], 0)
        self.assertIn("input(", result["python"])
        self.assertIn("Enter value (INTEGER):", result["stdout"])
        self.assertTrue(result["stdout"].rstrip().endswith("42"))
        self.assertEqual(result["diagnostics"], [])

    def test_compile_error_never_starts_runner(self):
        source = "IF TRUE THEN\n    OUTPUT \"never\""
        with patch("ide.application.execute_python") as child:
            result = self.application.run(source)
        child.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertIsNone(result["exitCode"])
        self.assertTrue(result["diagnostics"])
        self.assertEqual(result["stdout"], "")

    def test_runtime_error_is_not_a_compiler_diagnostic(self):
        result = self.application.run("OUTPUT 1 / 0")
        self.assertFalse(result["ok"])
        self.assertEqual(result["exitCode"], 1)
        self.assertIn("ZeroDivisionError", result["stderr"])
        self.assertEqual(result["diagnostics"], [])

    def test_single_function_is_invoked_from_typed_stdin_lines(self):
        source = (
            "FUNCTION Add(left : INTEGER, right : REAL) RETURNS REAL\n"
            "    RETURN left + right\n"
            "ENDFUNCTION"
        )
        result = self.application.run(source, "2\n3.5\n")
        self.assertTrue(result["ok"])
        self.assertEqual(result["entrypoint"], {
            "name": "Add",
            "kind": "function",
            "parameters": [
                {"name": "left", "type": "INTEGER", "passBy": "BYVAL"},
                {"name": "right", "type": "REAL", "passBy": "BYVAL"},
            ],
            "returnType": "REAL",
        })
        self.assertIn(">>> Add(2, 3.5) = 5.5", result["stdout"])

    def test_single_procedure_is_invoked_and_output_is_captured(self):
        source = (
            "PROCEDURE Greet(name : STRING)\n"
            "    OUTPUT \"Hello\", name\n"
            "ENDPROCEDURE"
        )
        result = self.application.run(source, "Ada Lovelace\n")
        self.assertTrue(result["ok"])
        self.assertEqual(result["entrypoint"]["kind"], "procedure")
        self.assertEqual(result["entrypoint"]["returnType"], None)
        self.assertIn("Hello Ada Lovelace", result["stdout"])


class IDEHTTPRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = IDEApplication.from_release()
        cls.server = create_server(cls.application, port=0)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()
        host, port = cls.server.server_address[:2]
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_run_endpoint_returns_program_output(self):
        payload = json.dumps({
            "source": "DECLARE name : STRING\nINPUT name\nOUTPUT name",
            "stdin": "Ada\n",
        }).encode("utf-8")
        request = Request(
            self.base_url + "/api/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertTrue(result["ok"])
        self.assertEqual(result["exitCode"], 0)
        self.assertTrue(result["stdout"].rstrip().endswith("Ada"))
        self.assertIn("python", result)
        self.assertIn("diagnostics", result)
        self.assertTrue(result["tokens"])
        self.assertIn("elapsedMs", result)


if __name__ == "__main__":
    unittest.main()
