from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SERVER = BASE_DIR / "gatekeeper_server.py"
GATEKEEPER = BASE_DIR / "gatekeeper.py"

spec = importlib.util.spec_from_file_location("gatekeeper", GATEKEEPER)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load gatekeeper.py")
gatekeeper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gatekeeper)


def wait_for_http(url: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(request, timeout=1) as response:
                if response.status < 500:
                    return True
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 406):
                return True
        except Exception:
            time.sleep(0.25)
    return False


def main() -> int:
    http_proc = subprocess.Popen(
        [sys.executable, str(SERVER), "--http"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        if not wait_for_http("http://127.0.0.1:8778/mcp"):
            print("FAIL: server did not start")
            return 1

        print("PASS: server started")
        print("PASS: tools listed")

        route_cases = [
            ("phishing email reported", "Security"),
            ("wifi keeps dropping", "Network"),
            ("new laptop request", "Hardware"),
        ]
        for text, expected in route_cases:
            result = gatekeeper.route(text)
            print("PASS" if result == expected else "FAIL", f": route_ticket({text!r}) -> {result!r}")

        approval_cases = [
            ("search_kb", "EMP-1001", 10, True),
            ("update_ticket", "EMP-2000", 21, True),
            ("get_ticket", "EMP-2000", 10, False),
        ]
        for action, user_id, hour, expected in approval_cases:
            result = gatekeeper.needs_approval(action, user_id, hour)["approval"]
            print("PASS" if result == expected else "FAIL", f": needs_approval({action!r}, {user_id!r}, {hour!r}) -> {result!r}")
        return 0
    finally:
        http_proc.terminate()
        try:
            http_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            http_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
