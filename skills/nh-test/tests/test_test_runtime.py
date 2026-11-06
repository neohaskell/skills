# Adapted for consumer applications from the public NeoHaskell project.
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from test_runtime import cabal_packages, cabal_test_targets, dependency_source_dirs, run_testbed


class TestRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "cabal.project").write_text("packages: domain/*.cabal api/*.cabal\n")
        for name, dependency in (("domain", "base"), ("api", "domain")):
            package = self.root / name
            package.mkdir()
            (package / f"{name}.cabal").write_text(
                f"name: {name}\nlibrary\n  hs-source-dirs: src\n  default-language: GHC2021\n"
                f"  default-extensions: NoImplicitPrelude\n  build-depends: {dependency}\n"
                f"test-suite {name}-spec\n  hs-source-dirs: tests\n")
        self.env = {**os.environ, "NH_APP_ROOT": str(self.root), "NH_TOOLCHAIN": "host"}
        self.env.pop("NH_HTTP_TEST_COMMAND_JSON", None)

    def test_component_packages_targets_and_dependencies_are_discovered(self):
        packages = cabal_packages(self.root)
        self.assertEqual({p.name for p in packages}, {"domain", "api"})
        self.assertEqual(set(cabal_test_targets(self.root)), {("domain", "domain-spec"), ("api", "api-spec")})
        api = next(p for p in packages if p.name == "api")
        domain = next(p for p in packages if p.name == "domain")
        self.assertIn(domain.source_dirs[0], dependency_source_dirs(api, packages))
        self.assertEqual(domain.language, "GHC2021")
        self.assertIn("NoImplicitPrelude", domain.extensions)

    def test_http_runner_is_optional_and_does_not_assume_framework_services(self):
        status, reason, result = run_testbed(self.root, self.env, 1)
        self.assertEqual(status, "NOT_CONFIGURED")
        self.assertIn("not exercised", reason)
        self.assertIsNone(result)

    def test_http_command_is_an_argument_array_with_literal_arguments(self):
        literal = "$(do-not-execute) argument with spaces"
        env = {**self.env, "NH_HTTP_TEST_COMMAND_JSON": json.dumps([sys.executable, "-c", "import sys; print(sys.argv[1])", literal])}
        status, _, result = run_testbed(self.root, env, 3)
        self.assertEqual(status, "PASS")
        self.assertEqual(result.output.decode().strip(), literal)

    def test_invalid_unavailable_failed_and_timed_out_http_runners_do_not_pass(self):
        commands = ["not JSON", '{}', '[]', '[""]', '[42]',
                    json.dumps([str(self.root / "missing-runner")]),
                    json.dumps([sys.executable, "-c", "raise SystemExit(4)"]),
                    json.dumps([sys.executable, "-c", "import time; time.sleep(5)"])]
        for command in commands:
            with self.subTest(command=command):
                env = {**self.env, "NH_HTTP_TEST_COMMAND_JSON": command}
                status, _, _ = run_testbed(self.root, env, 0.2)
                self.assertEqual(status, "FAIL")

    def test_missing_http_runner_is_incomplete_and_strict_mode_fails(self):
        for strict, code in ((False, 0), (True, 1)):
            result = subprocess.run([sys.executable, str(SCRIPTS / "run-testbed"), "--_inside-toolchain", *(["--strict"] if strict else [])],
                                    cwd=self.root, env=self.env, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertIn("INCOMPLETE", result.stdout)

    def test_nonfinite_timeouts_are_rejected_before_toolchain_entry(self):
        for script in ("run-doctest", "run-full-suite", "run-testbed"):
            for value in ("nan", "inf"):
                with self.subTest(script=script, value=value):
                    result = subprocess.run([sys.executable, str(SCRIPTS / script), "--timeout", value], capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("timeout must", result.stderr)


if __name__ == "__main__":
    unittest.main()
