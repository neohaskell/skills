# Adapted for consumer applications from the public NeoHaskell project.
"""Exercise the runner's verdicts without requiring framework CI or a toolchain."""
import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
LOADER = importlib.machinery.SourceFileLoader("full_suite", str(SCRIPTS / "run-full-suite"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
RUNNER = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(RUNNER)


class FullSuiteTests(unittest.TestCase):
    def invoke(self, output="Test suite unit: PASS\n", targets=None, strict=True,
               http="NOT_CONFIGURED", returncode=0, timed_out=False, output_limited=False):
        if targets is None:
            targets = [("app", "unit")]
        captured = io.StringIO()
        result = SimpleNamespace(output=output.encode(), returncode=returncode,
                                 timed_out=timed_out, output_limited=output_limited)
        with patch.object(RUNNER, "cabal_test_targets", return_value=targets), \
             patch.object(RUNNER.shutil, "which", return_value="/tools/cabal"), \
             patch.object(RUNNER, "run_bounded", return_value=result) as command, \
             patch.object(RUNNER, "run_testbed", return_value=(http, "fixture status", None)), \
             contextlib.redirect_stdout(captured):
            code = RUNNER.run_inside(Path("/app"), strict, 10)
        return code, captured.getvalue(), command

    def test_declared_cabal_success_does_not_claim_http_coverage(self):
        code, output, command = self.invoke()
        self.assertEqual(code, 0)
        self.assertIn("NOT_CONFIGURED configured HTTP checks", output)
        self.assertIn("PASS: 1 Cabal target(s)", output)
        self.assertIn("--project-file=cabal.project", command.call_args.args[0])

    def test_missing_or_skipped_result_is_incomplete(self):
        for output in ("", "Test suite unit: SKIP\n"):
            for strict in (True, False):
                with self.subTest(output=output, strict=strict):
                    code, report, _ = self.invoke(output=output, strict=strict)
                    self.assertEqual(code, int(strict))
                    self.assertIn("INCOMPLETE", report)

    def test_failures_cannot_be_overridden_by_pass_text(self):
        for failure in ({"returncode": 1}, {"timed_out": True}, {"output_limited": True},
                        {"http": "FAIL"}, {"output": "Test suite unit: FAIL\n"}):
            with self.subTest(failure=failure):
                code, output, _ = self.invoke(**failure)
                self.assertEqual(code, 1)
                self.assertIn("full-suite: FAIL:", output)

    def test_ambiguous_suite_names_cannot_count_one_pass_twice(self):
        code, output, command = self.invoke(targets=[("first", "unit"), ("second", "unit")], strict=False)
        self.assertEqual(code, 1)
        self.assertIn("ambiguous across packages: unit", output)
        command.assert_not_called()

    def test_no_declared_tests_is_incomplete_even_with_http_pass(self):
        code, output, command = self.invoke(targets=[], http="PASS")
        self.assertEqual(code, 1)
        self.assertIn("INCOMPLETE", output)
        command.assert_not_called()

    def test_every_declared_suite_requires_its_own_result(self):
        code, output, _ = self.invoke(targets=[("app", "unit"), ("app", "integration")])
        self.assertEqual(code, 1)
        self.assertIn("app:integration: Cabal reported no result", output)


if __name__ == "__main__":
    unittest.main()
