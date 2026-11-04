import importlib.util
import os
import pathlib
import subprocess
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("design_check", HERE.parent / "harness" / "tools" / "greenfield" / "design-check.py")
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)

DESIGN = "# Design\n" + "\n".join(f"## {h}\nText about {h}. " + "x" * 300 for h in
                                  ["Scope and out of scope", "Components", "Stored layout", "Failure model",
                                   "Observability events", "Retention", "Decisions ADR"])
ADR = "# 0001 Layout\n## Context\nwhy\n## Decision\nthis\n## Consequences\n" + "y" * 400
AGENTS = "# Repo\n## Layout\nx\n## Decisions\nx\n## Verifying\nx\n" + "z" * 800
PROGRAM = "builder.Services.AddSingleton<A>();builder.Services.AddSingleton<B>();" \
          "builder.Services.AddSingleton<C>();builder.Services.AddSingleton<D>();"


def write(root, rel, body):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class DesignCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_repos_do_not_receive_optional_harness_gate_files(self):
        initializer = HERE.parent / "harness/tools/greenfield/greenfield-init.sh"
        for profile in ("--service", "--web-app", None):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                command = ["bash", str(initializer)]
                if profile:
                    command.append(profile)
                subprocess.run(command + [directory], check=True, capture_output=True, text=True,
                               env=dict(os.environ, GOLDEN_PATH_HOME=str(self.root / 'runtime')))
                root = pathlib.Path(directory)
                for optional in ("BannedSymbols.txt", "Directory.Build.props", ".harness-scenarios.json"):
                    self.assertFalse((root / optional).exists(), optional)
                files = [path for path in root.rglob("*") if path.is_file()]
                self.assertFalse(any("BannedApiAnalyzers" in path.read_text() for path in files))

    def statuses(self):
        return {c["id"]: c["status"] for c in dc.run(self.root)["checks"]}

    def test_empty_workspace_fails_everything(self):
        self.assertEqual(set(self.statuses().values()), {"fail"})

    def test_design_only_passes_before_any_code_exists(self):
        write(self.root, "docs/solution-design.md", DESIGN)
        write(self.root, "docs/adr/0001-layout.md", ADR)
        write(self.root, "docs/adr/0002-run.md", ADR)
        write(self.root, "AGENTS.md", AGENTS)
        result = dc.run(self.root, "service", design_only=True)
        self.assertEqual(result["status"], "pass")
        self.assertEqual([c["id"] for c in result["checks"]], ["D01", "D02", "D03"])
        self.assertEqual(dc.run(self.root, "service")["status"], "fail")

    def test_complete_workspace_passes(self):
        write(self.root, "docs/solution-design.md", DESIGN)
        write(self.root, "docs/adr/0001-layout.md", ADR)
        write(self.root, "docs/adr/0002-run.md", ADR)
        write(self.root, "AGENTS.md", AGENTS)
        write(self.root, "scripts/verify.sh", "dotnet format; dotnet build -warnaserror; dotnet test")
        write(self.root, "src/Program.cs", PROGRAM)
        write(self.root, "src/Interfaces.cs", "interface IStore {} interface ISource {} interface IClock {} interface IRunner {} interface IEventSink {}")
        write(self.root, "src/Impl.cs", "class FileStore : IStore {}")
        write(self.root, "src/ErrorCodes.cs", "class ErrorCodes { const string RunStarted = \"x\"; } class RunStatusService {}")
        write(self.root, "tests/UnitA.cs", "[Fact] void a(){}" * 6)
        write(self.root, "tests/UnitB.cs", "[Fact] void a(){}" * 4)
        write(self.root, "tests/UnitC.cs", "[Fact] void a(){}" * 4)
        self.assertEqual(self.statuses(), {k: "pass" for k in self.statuses()})

    def web_app_workspace(self):
        write(self.root, "docs/solution-design.md", DESIGN)
        write(self.root, "docs/adr/0001-layout.md", ADR)
        write(self.root, "docs/adr/0002-run.md", ADR)
        write(self.root, "AGENTS.md", AGENTS)
        write(self.root, "scripts/verify.sh", "dotnet format; dotnet build -warnaserror; dotnet test")
        write(self.root, "src/Program.cs", PROGRAM + 'app.MapGet("/api/health", () => 1);')
        write(self.root, "src/Ports.cs", "interface IClientDirectory {} interface IMenuGateway {} interface IPdfRenderer {} interface IMailer {}")
        write(self.root, "src/Adapters.cs", "class DirectusClients : IClientDirectory {} class DirectusMenus : IMenuGateway {} "
                                            "class QuestPdf : IPdfRenderer {} class Smtp : IMailer {} class Uses { TimeProvider t; }")
        write(self.root, "src/ErrorCodes.cs", "class ErrorCodes { const string X = \"x\"; }")
        for name in "ABC":
            write(self.root, f"tests/Unit{name}.cs", "[Fact] void a(){}" * 5)

    def test_web_app_profile_passes_without_service_role_names(self):
        self.web_app_workspace()
        result = dc.run(self.root, "web-app")
        self.assertEqual(result["status"], "pass", result["checks"])
        self.assertEqual(dc.run(self.root, "service")["status"], "fail")  # the same code is not a batch service

    def test_web_app_without_a_health_endpoint_fails_d08(self):
        self.web_app_workspace()
        write(self.root, "src/Program.cs", PROGRAM)
        self.assertEqual({c["id"]: c["status"] for c in dc.run(self.root, "web-app")["checks"]}["D08"], "fail")

    def test_web_app_with_interfaces_nobody_implements_fails_d06(self):
        self.web_app_workspace()
        write(self.root, "src/Adapters.cs", "class Uses { TimeProvider t; }")
        self.assertEqual({c["id"]: c["status"] for c in dc.run(self.root, "web-app")["checks"]}["D06"], "fail")

    def test_operation_building_its_collaborator_fails_d07(self):
        write(self.root, "src/FileStore.cs", "class FileStore : IStore {}")
        write(self.root, "src/BackupOperation.cs", "class BackupOperation { IStore s = new FileStore(); }")
        self.assertEqual(self.statuses()["D07"], "fail")

    def test_base_copy_is_not_the_repos_agents_file(self):
        write(self.root, "AGENTS.md", "Harness check: `tvh-loaded`.\n## Layout\n## Verifying\n## Decisions\n" + "z" * 900)
        self.assertEqual(self.statuses()["D03"], "fail")

    def test_symlinked_design_is_not_followed(self):
        outside = pathlib.Path(tempfile.mkdtemp()) / "d.md"
        outside.write_text(DESIGN, encoding="utf-8")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "solution-design.md").symlink_to(outside)
        self.assertEqual(self.statuses()["D01"], "fail")


if __name__ == "__main__":
    unittest.main()
