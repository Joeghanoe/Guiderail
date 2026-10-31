"""Stand-in grader: reads the prompt on stdin and answers with a fixed verdict."""
import json
import sys

prompt = sys.stdin.read()
assert "G01" in prompt and "public class Added" in prompt
verdict = sys.argv[1] if len(sys.argv) > 1 else "pass"
print(json.dumps({"items": [{"id": "G01", "verdict": verdict, "evidence": "Services/Thing.cs:3"},
                    {"id": "CODE.5", "verdict": "pass", "evidence": "n/a"}],
                  "hard_gates": [{"id": "T.1", "verdict": "inconclusive"}], "regressions": []}))
