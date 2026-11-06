# Adapted for consumer applications from the public NeoHaskell project.
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts"


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "application"
        self.root.mkdir()
        (self.root / "cabal.project").write_text("packages: backend/*.cabal\n")
        (self.root / "backend").mkdir()
        (self.root / "backend/app.cabal").write_text("name: app\nbuild-depends: base\n")
        self.tools = self.base / "tools"
        self.tools.mkdir()
        for name in ("bash", "dirname", "cat", "cut", "sha256sum", "shasum"):
            executable = shutil.which(name)
            if executable:
                (self.tools / name).symlink_to(executable)
        self.env = {**os.environ, "PATH": str(self.tools), "NH_APP_ROOT": str(self.root)}
        self.env.pop("NH_TOOLCHAIN", None)

    def command(self, name, body):
        target = self.tools / name
        target.write_text("#!/usr/bin/env bash\n" + body)
        target.chmod(0o755)

    def run_script(self, name, *args, env=None, cwd=None):
        environment = self.env.copy()
        for key, value in (env or {}).items():
            if value is None:
                environment.pop(key, None)
            else:
                environment[key] = value
        return subprocess.run([str(SOURCE / name), *args], cwd=cwd or self.root,
                              env=environment, text=True, capture_output=True, timeout=10)

    def test_discovery_uses_invocation_component_not_installed_script_location(self):
        component = self.root / "frontend"
        nested = component / "src"
        nested.mkdir(parents=True)
        (component / "neo.json").write_text("{}")
        result = self.run_script("repo-root", env={"NH_APP_ROOT": None}, cwd=nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(component))

    def test_explicit_root_accepts_a_component_without_framework_layout(self):
        component = self.base / "worker"
        component.mkdir()
        result = self.run_script("repo-root", env={"NH_APP_ROOT": str(component)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(component))

    def test_explicit_root_must_exist(self):
        result = self.run_script("repo-root", env={"NH_APP_ROOT": str(self.base / "missing")})
        self.assertEqual(result.returncode, 2)
        self.assertIn("existing application component", result.stderr)

    def test_discovery_stops_at_the_consumer_git_boundary(self):
        (self.base / "flake.nix").write_text("{}")
        isolated = self.base / "other-app"
        (isolated / ".git").mkdir(parents=True)
        result = self.run_script("repo-root", env={"NH_APP_ROOT": None}, cwd=isolated)
        self.assertEqual(result.returncode, 2)

    def test_host_selection_preserves_arguments_and_exit_status(self):
        self.command("selected-tool", 'printf "<%s>\\n" "$@"; exit 23\n')
        result = self.run_script("with-toolchain", "selected-tool", "argument with spaces", "")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(result.stdout.splitlines(), ["<argument with spaces>", "<>"])
        self.assertIn("selected host toolchain", result.stderr)

    def test_declared_flake_uses_nix_without_running_host_fallback(self):
        (self.root / "flake.nix").write_text("{}")
        self.command("nix", 'printf "<%s>\\n" "$@"; exit 37\n')
        self.command("selected-tool", 'printf "unexpected host fallback\\n"\n')
        result = self.run_script("with-toolchain", "selected-tool", "argument with spaces")
        self.assertEqual(result.returncode, 37)
        self.assertEqual(result.stdout.splitlines(), ["<develop>", "<--command>", "<selected-tool>", "<argument with spaces>"])

    def test_missing_declared_nix_fails_without_host_fallback(self):
        (self.root / "flake.nix").write_text("{}")
        self.command("selected-tool", 'printf "unexpected host fallback\\n"\n')
        result = self.run_script("with-toolchain", "selected-tool")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_explicit_host_selection_does_not_invoke_nix(self):
        (self.root / "flake.nix").write_text("{}")
        self.command("nix", 'exit 99\n')
        self.command("selected-tool", 'printf "host selected\\n"\n')
        result = self.run_script("with-toolchain", "selected-tool", env={"NH_TOOLCHAIN": "host"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "host selected")

    def test_invalid_mode_and_missing_nix_declaration_fail(self):
        for mode in ("invalid", "nix"):
            with self.subTest(mode=mode):
                result = self.run_script("with-toolchain", "selected-tool", env={"NH_TOOLCHAIN": mode})
                self.assertEqual(result.returncode, 2)

    def test_fingerprint_tracks_component_cabal_and_nix_inputs(self):
        if not (self.tools / "sha256sum").exists() and not (self.tools / "shasum").exists():
            self.skipTest("SHA-256 utility unavailable")
        first = self.run_script("toolchain-fp")
        self.assertEqual(first.returncode, 0, first.stderr)
        (self.root / "app.cabal").write_text("name: root-app\n")
        second = self.run_script("toolchain-fp")
        self.assertNotEqual(first.stdout, second.stdout)
        (self.root / "nix").mkdir()
        (self.root / "nix/environment.nix").write_text("{}")
        third = self.run_script("toolchain-fp")
        self.assertNotEqual(second.stdout, third.stdout)


if __name__ == "__main__":
    unittest.main()
