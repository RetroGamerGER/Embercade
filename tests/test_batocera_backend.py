"""Process contracts and independently installed backend, without launching games."""

import ast
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from embercade.backend import backend_command
from embercade.batocera_config import BatoceraConfigError, resolve_system_choice
from embercade.paths import EmbercadePaths
from embercade.runtime import ProjectRuntime, RUNTIME_LABELS, probe_runtime
from embercade.ui_data import build_complete_catalog, build_ui_data


PROJECT = Path(__file__).resolve().parents[1]
ADAPTER = PROJECT / "integration/batocera/adapter.py"
RUNTIME = ProjectRuntime(PROJECT)


class BatoceraBackendTests(unittest.TestCase):
    def test_client_package_has_no_upstream_imports_or_embedded_api_programs(self):
        for path in (PROJECT / "src/embercade").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse((node.module or "").startswith(("batocera_", "configgen")), path)
                elif isinstance(node, ast.Import):
                    self.assertFalse(any(n.name.startswith(("batocera_", "configgen")) for n in node.names), path)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    # Literal paths, notices and format names are data. Executable
                    # Python API import lines must never return to this package.
                    self.assertNotRegex(node.value, r"(?m)^\s*(?:from|import)\s+(?:batocera_|configgen)")
                elif isinstance(node, ast.Call) and node.args:
                    name = getattr(node.func, "attr", getattr(node.func, "id", ""))
                    if name in ("import_module", "__import__") and isinstance(node.args[0], ast.Constant):
                        self.assertFalse(str(node.args[0].value).startswith(("batocera_", "configgen")), path)

    def test_backend_never_imports_client_even_in_deferred_functions(self):
        for node in ast.walk(ast.parse(ADAPTER.read_text())):
            if isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith("embercade"))
            elif isinstance(node, ast.Import):
                self.assertFalse(any(n.name.startswith("embercade") for n in node.names))

    def test_backend_help_and_protocol_do_not_need_runtime_or_client(self):
        help_result = subprocess.run(backend_command(Path(sys.executable), "--help"),
                                     capture_output=True, text=True, timeout=10)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("build-ui", help_result.stdout)
        result = subprocess.run([sys.executable, "-B", "-I", str(ADAPTER), "--protocol", "2", "probe-runtime"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)

    def fixture_builder(self, root):
        package = root / "source/python-src/batocera-es-system/batocera_es_system"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        (package / "registry.py").write_text(
            "class Registry:\n"
            " @classmethod\n def load_files(cls,files):\n  r=cls();r.files=list(files);return r\n"
            " def get_systems_metadata(self,defaults):return self.files\n")
        (package / "shared.py").write_text(
            "class Defaults:\n @classmethod\n def for_directory(cls,path):return path\n")
        (package / "es_systems.py").write_text(
            "def build(metadata,source,output):\n"
            " print('builder progress')\n"
            " (output/'es_systems.cfg').write_text('<systemList><system><name>nes</name>'"
            "+'<path>x</path><command>x</command></system></systemList>')\n")
        (package / "es_features.py").write_text(
            "def build(registry,output):\n (output/'es_features.cfg').write_text('<features/>')\n")
        return root / "source"

    def test_both_builders_execute_with_upstream_imports_blocked_in_client(self):
        import importlib.abc
        class RejectUpstream(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.startswith(("batocera_", "configgen")):
                    raise AssertionError("API import crossed the process boundary: " + fullname)
        guard = RejectUpstream()
        with TemporaryDirectory(prefix="backend with spaces ") as temp:
            root = Path(temp)
            source = self.fixture_builder(root)
            sys.meta_path.insert(0, guard)
            try:
                with redirect_stdout(StringIO()) as progress:
                    build_ui_data(batocera_source=source, defaults=root / "defaults",
                                  output=root / "selected", rom_path=root / "ROM files",
                                  launch_command=root / "start game")
                    build_complete_catalog(source, root / "defaults", root / "complete")
                self.assertEqual(progress.getvalue().count("builder progress"), 2)
            finally:
                sys.meta_path.remove(guard)
            self.assertIn(str(root / "ROM files"), (root / "selected/es_systems.cfg").read_text())
            self.assertEqual(ET.parse(root / "complete/es_features.cfg").getroot().tag, "features")
            self.assertFalse(any(name.startswith("batocera_es_system") for name in sys.modules))

    def test_ui_builder_failure_and_invalid_results_are_reported(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            cases = [
                subprocess.CompletedProcess([], 1, "", "original builder error"),
                subprocess.CompletedProcess([], 0, "not JSON", ""),
                subprocess.CompletedProcess([], 0, '{"systems":"wrong","features":"wrong"}', ""),
            ]
            for result in cases:
                with self.subTest(result=result), patch("embercade.ui_data.subprocess.run", return_value=result):
                    with self.assertRaisesRegex(ValueError, "builder"):
                        build_complete_catalog(root, root, root / "output")

    def test_system_probe_timeout_keeps_existing_error_contract(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = ProjectRuntime(root)
            runtime.python.parent.mkdir(parents=True)
            runtime.python.write_text("python")
            runtime.python.chmod(0o755)
            paths = EmbercadePaths.from_environment({"HOME": str(root)})
            paths.batocera_conf.parent.mkdir(parents=True)
            paths.batocera_conf.write_text("")
            with patch("embercade.batocera_config.subprocess.run",
                       side_effect=subprocess.TimeoutExpired("backend", 30)):
                with self.assertRaisesRegex(BatoceraConfigError, "probe failed"):
                    resolve_system_choice(system="snes", rom=root / "Game.sfc", paths=paths, runtime=runtime)

    def test_malformed_health_response_never_reports_success(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = ProjectRuntime(root)
            runtime.python.parent.mkdir(parents=True)
            runtime.python.touch()
            runtime.launcher.touch()
            for response in ("null", "[]", '{"python":"3.14","imports":{}}',
                             json.dumps({"python": "3.14", "imports": dict.fromkeys(RUNTIME_LABELS, 1)})):
                with self.subTest(response=response), patch("embercade.runtime.subprocess.run",
                        return_value=subprocess.CompletedProcess([], 0, response, "")):
                    status = probe_runtime(runtime)
                    self.assertFalse(status.healthy)
                    self.assertEqual(status.cli_error, "imports unavailable")

    @unittest.skipUnless(RUNTIME.python.is_file(), "Prepared pinned runtime required")
    def test_installed_backend_path_works_outside_checkout_with_hostile_pythonpath(self):
        with TemporaryDirectory(prefix="installed backend ") as temp:
            root = Path(temp)
            application = root / "prefix/share/embercade"
            client = application / "app/embercade/backend.py"
            adapter = application / "integration/batocera/adapter.py"
            client.parent.mkdir(parents=True)
            adapter.parent.mkdir(parents=True)
            shutil.copy2(PROJECT / "src/embercade/backend.py", client)
            shutil.copy2(ADAPTER, adapter)
            (root / "batocera_launch.py").write_text("raise AssertionError('hostile module loaded')")
            # Load only the copied transport, then use its computed installed path.
            import importlib.util
            spec = importlib.util.spec_from_file_location("copied_transport", client)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            command = module.backend_command(RUNTIME.python, "probe-runtime")
            self.assertEqual(command[3], str(adapter))
            result = subprocess.run(command, cwd=root, env=os.environ | {"PYTHONPATH": str(root)},
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(set(payload["imports"]), set(RUNTIME_LABELS))
            self.assertTrue(all(v is None for v in payload["imports"].values()), payload)

    @unittest.skipUnless(RUNTIME.python.is_file(), "Prepared pinned runtime required")
    def test_runtime_clients_keep_upstream_out_of_parent_process(self):
        import importlib.abc
        from types import SimpleNamespace
        from embercade.batocera_config import _probe_environment
        from embercade.standalone_decoration import resolve_decoration

        class RejectUpstream(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.startswith(("batocera_", "configgen")):
                    raise AssertionError("Client imported upstream: " + fullname)

        with TemporaryDirectory() as temp:
            paths = EmbercadePaths.from_environment({"HOME": temp})
            paths.batocera_conf.parent.mkdir(parents=True)
            paths.batocera_conf.write_text("snes.core=snes9x\nps2.bezel=none\n")
            paths.emulationstation_config.mkdir(parents=True)
            (paths.emulationstation_config / "es_settings.cfg").write_text("<config/>")
            environment = _probe_environment(paths, RUNTIME, os.environ)
            environment.update(EMBERCADE_DESKTOP="1", EMBERCADE_SYSTEM_DECORATIONS=temp)
            guard = RejectUpstream()
            sys.meta_path.insert(0, guard)
            try:
                choice = resolve_system_choice(system="snes", rom=Path(temp)/"Game.sfc",
                                               paths=paths, runtime=RUNTIME, environment=environment)
                self.assertEqual(choice.core, "snes9x")
                self.assertTrue(probe_runtime(RUNTIME).healthy)
                self.assertIsNone(resolve_decoration(SimpleNamespace(
                    command=[str(RUNTIME.launcher)], environment=environment,
                    system="ps2", rom=Path(temp)/"Game.iso")))
            finally:
                sys.meta_path.remove(guard)
        self.assertFalse(any(n.startswith(("batocera_", "configgen")) for n in sys.modules))

    @unittest.skipUnless(RUNTIME.python.is_file(), "Prepared pinned runtime required")
    def test_backend_api_execution_rejects_all_client_imports(self):
        program = r'''
import importlib.abc,runpy,sys
class RejectClient(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('embercade'):raise AssertionError('reverse client import: '+fullname)
sys.meta_path.insert(0,RejectClient())
adapter=sys.argv[1];sys.argv=[adapter,'--protocol','1','probe-runtime']
runpy.run_path(adapter,run_name='__main__')
'''
        result = subprocess.run([str(RUNTIME.python), "-B", "-I", "-c", program, str(ADAPTER)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(v is None for v in json.loads(result.stdout)["imports"].values()))


if __name__ == "__main__":
    unittest.main()
