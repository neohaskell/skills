# Adapted for consumer applications from the public NeoHaskell project.
"""Check portable lint plumbing and finite parsers without a framework lint policy."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from cabal_extensions import parser_source, profiles
from source_rules import signature_violations


class StaticChecks(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.hlint = self.root / "fake-hlint"
        self.hlint.write_text(
            f"#!{sys.executable}\nimport os, sys\n"
            "if '--numeric-version' in sys.argv:\n"
            "    print('3.10'); sys.exit(0)\n"
            "print(os.environ.get('FIXTURE_HLINT_OUTPUT', '[]'))\n"
            "sys.exit(int(os.environ.get('FIXTURE_HLINT_STATUS', '0')))\n"
        )
        self.hlint.chmod(0o755)

    def source(self, text, name="src/Example.hs"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return Path(name)

    def check(self, expected, *arguments, output="[]", status=0):
        env = {**os.environ, "NH_APP_ROOT": str(self.root), "PYTHONDONTWRITEBYTECODE": "1",
               "FIXTURE_HLINT_OUTPUT": output, "FIXTURE_HLINT_STATUS": str(status)}
        result = subprocess.run([sys.executable, str(SCRIPTS / "check.py"), "--hlint", str(self.hlint),
                                 *arguments], cwd=self.root, env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def idea(self, **overrides):
        return {"hint": "Use head", "file": "src/Example.hs", "startLine": 2,
                "severity": "Suggestion", "decl": ["first"], "from": "values !! 0",
                "to": "head values", "note": [], **overrides}

    def test_no_framework_lint_file_is_required(self):
        self.source("module Example where\nvalue = 1\n")
        self.assertIn("PASS", self.check(0))
        self.assertFalse((self.root / ".hlint.yaml").exists())

    def test_consumer_version_pin_is_optional_and_enforced_when_selected(self):
        self.source("module Example where\nvalue = 1\n")
        self.check(0, "--expected-version", "3.10")
        self.assertIn("Expected consumer HLint version 9.9", self.check(2, "--expected-version", "9.9"))

    def test_consumer_findings_keep_source_identity(self):
        self.source("module Example where\nfirst values = values !! 0\n")
        output = self.check(1, output=json.dumps([self.idea()]), status=1)
        self.assertIn("src/Example.hs [first] Use head", output)

    def test_ignored_consumer_suggestion_is_respected(self):
        self.source("module Example where\nfirst values = values !! 0\n")
        self.check(0, output=json.dumps([self.idea(severity="Ignore")]))

    def test_invalid_lint_output_and_parser_failure_are_setup_errors(self):
        self.source("module Example where\nvalue = 1\n")
        for output, status in [("not JSON", 0), ("{}", 0), ("[]", 1),
                               ("[]", 2), (json.dumps([self.idea(hint="Parse error")]), 1)]:
            with self.subTest(output=output, status=status):
                self.check(2, output=output, status=status)

    def test_dialect_signature_policy_is_opt_in(self):
        self.source("module Example where\nimport Core\nrender :: LinkedList Char -> Text\n")
        self.check(0)
        self.assertIn("use Text parameters", self.check(1, "--dialect-rules"))

    def test_signature_policy_has_no_framework_path_exemptions(self):
        source = "module Text where\nimport Core\nfromLinkedList :: LinkedList Char -> Text\n"
        for path in ("src/Text.hs", "core/core/Text.hs"):
            with self.subTest(path=path):
                self.assertEqual(len(list(signature_violations(source, path))), 1)

    def test_signature_scanner_preserves_results_and_unrelated_names(self):
        for source in (
            "module Example where\nimport Core\nrender :: Text -> LinkedList Char\n",
            "module Example where\nimport Other\nrender :: LinkedList Char -> Text\n",
            "module Example where\n-- render :: LinkedList Char -> Text\n",
        ):
            self.assertEqual(list(signature_violations(source, "src/Example.hs")), [])

    def test_runtime_workspace_reference_is_reported(self):
        self.source('path = ".agents-state/runtime.db"\n', "app.py")
        self.assertIn("Agent workspace in runtime source", self.check(1))

    def test_installed_agent_helpers_are_outside_runtime_source_scope(self):
        self.source('path = ".agents-state/run"\n', ".agents/skills/example/scripts/helper.py")
        self.check(0)

    def test_cabal_common_settings_and_component_overrides(self):
        cabal = self.source("common shared\n  default-extensions: Strict\nlibrary\n  import: shared\n  hs-source-dirs: src\ntest-suite unit\n  import: shared\n  hs-source-dirs: tests\n  ghc-options: -XNoStrict\n", "app.cabal")
        source = self.source("module Example where\n")
        test = self.source("module ExampleSpec where\n", "tests/ExampleSpec.hs")
        settings = profiles(self.root, [source, test], [cabal, source, test])
        self.assertIn("Strict", settings[source])
        self.assertIn("NoStrict", settings[test])
        self.assertNotIn("Strict", settings[test])

    def test_unsupported_cabal_settings_fail_visibly(self):
        source = self.source("module Example where\n")
        for config in (
            "library\n  if flag(strict)\n    default-extensions: Strict\n  hs-source-dirs: src\n",
            "common cycle\n  import: cycle\nlibrary\n  import: cycle\n  hs-source-dirs: src\n",
            "library\n  hs-source-dirs: elsewhere\n",
            "library\n  hs-source-dirs: src\n  default-extensions: Strict\ntest-suite unit\n  hs-source-dirs: src\n",
        ):
            cabal = self.source(config, "app.cabal")
            with self.subTest(config=config), self.assertRaises(ValueError):
                profiles(self.root, [source], [cabal, source])

    def test_parser_normalization_preserves_original_source_locations(self):
        source = "{-# LANGUAGE Strict #-}\nmodule Example where\ndefer ~value = Deferred (\\_ -> value)\n"
        normalized = parser_source(source, Path("src/Example.hs"), ("Strict",))
        self.assertIn('{-# LINE 1 "src/Example.hs" #-}', normalized)
        self.assertIn("defer ~value", normalized)
        self.assertIn("Strict", source)
        with self.assertRaises(ValueError):
            parser_source('{-# LINE 9 "another.hs" #-}\n' + source, Path("src/Example.hs"), ())


if __name__ == "__main__":
    unittest.main()
