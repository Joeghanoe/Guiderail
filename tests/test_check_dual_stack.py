"""IAC.9: the dual-stack checker finds IPv4-only binds and localhost probes, and honours a stated exception."""
import pathlib
import subprocess
import tempfile
import unittest

TOOL = pathlib.Path(__file__).resolve().parents[1] / "harness" / "tools" / "iac" / "check-dual-stack.py"


class DualStackTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_tool(self):
        return subprocess.run(["python3", "-I", str(TOOL), str(self.root)], capture_output=True, text=True)

    def test_a_clean_repo_passes(self):
        self.write("src/Program.cs", 'builder.WebHost.UseUrls("http://[::]:8080");')
        self.write("docker-compose.yml", 'environment:\n  HOST: "::"\nhealthcheck:\n  test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:8055/server/ping"]\n')
        self.write("infra/edge.conf", "server {\n  listen 8080;\n  listen [::]:8080;\n}\n")
        result = self.run_tool()
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_kestrel_on_the_ipv4_wildcard_is_found(self):
        self.write("src/Program.cs", 'builder.WebHost.UseUrls("http://0.0.0.0:8080");')
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("src/Program.cs:1: IAC.9", result.stdout)

    def test_host_variables_and_server_flags_are_found(self):
        self.write("docker-compose.yml", "environment:\n  HOST: 0.0.0.0\n")
        self.write("run.sh", "uvicorn app:app --host 0.0.0.0 --port 8000\n")
        self.write("server.json", '{"HOST": "0.0.0.0"}')
        found = self.run_tool().stdout.splitlines()
        self.assertEqual(len(found), 3, found)

    def test_a_localhost_probe_is_found_and_a_loopback_probe_is_not(self):
        self.write("a/docker-compose.yml", 'healthcheck:\n  test: ["CMD-SHELL", "wget -qO- http://localhost:8055/server/ping || exit 1"]\n')
        self.write("b/Dockerfile", "HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1\n")
        self.write("c/docker-compose.yml", 'healthcheck:\n  test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:8055/server/ping"]\n')
        found = self.run_tool().stdout
        self.assertIn("a/docker-compose.yml:2", found)
        self.assertIn("b/Dockerfile:1", found)
        self.assertNotIn("c/", found)

    def test_nginx_listening_on_ipv4_only_is_found(self):
        self.write("infra/web.conf", "server {\n  listen 8080;\n}\n")
        self.assertIn("infra/web.conf:2: IAC.9 nginx", self.run_tool().stdout)

    def test_a_stated_exception_is_honoured(self):
        self.write("src/Program.cs", 'app.Urls.Add("http://0.0.0.0:9000"); // dual-stack: ok - sidecar on an IPv4-only host network')
        self.assertEqual(self.run_tool().returncode, 0)

    def test_prose_and_build_output_are_not_scanned(self):
        self.write("docs/notes.md", "Never bind http://0.0.0.0:8080 alone.")
        self.write("node_modules/x/a.json", '{"HOST": "0.0.0.0"}')
        self.assertEqual(self.run_tool().returncode, 0)


if __name__ == "__main__":
    unittest.main()
