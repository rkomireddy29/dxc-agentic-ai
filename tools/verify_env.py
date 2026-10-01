"""Environment check. Every line must say [OK]. Run: python tools\\verify_env.py"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ok_all = True


def check(label, ok, hint=""):
    global ok_all
    ok_all &= bool(ok)
    print(("[OK]  " if ok else "[!!]  ") + label + ("" if ok else f"  ->  {hint}"))


def git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip()


check("Python 3.11+", sys.version_info >= (3, 11), "install Python 3.11 or newer")
check("Repo is at C:\\AskIT\\dxc-agentic-ai", str(ROOT).lower() == r"c:\askit\dxc-agentic-ai", f"repo is at {ROOT}; re-clone into C:\\AskIT")
check("Git installed", shutil.which("git") is not None, "install Git for Windows")
check("Running inside .venv", sys.prefix != sys.base_prefix, "use SETUP.bat / START_DAY.bat")
check("Remote 'origin' = your fork", "github.com" in git("remote", "get-url", "origin"), "clone YOUR fork")
check("Remote 'upstream' = trainer repo", "github.com" in git("remote", "get-url", "upstream"), "run SETUP.bat")
me = ROOT / "me.json"
check("me.json exists", me.exists(), "run: python tools\\setup_me.py")
if me.exists():
    m = json.loads(me.read_text(encoding="utf-8"))
    check("me.json complete", all(m.get(k) for k in ("name", "github_user", "team")), "run: python tools\\setup_me.py")
check(".env exists", (ROOT / ".env").exists(), "copy .env.example to .env")

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    import boto3
    sess = boto3.Session(region_name=os.getenv("AWS_REGION", "us-east-1"))
    ident = sess.client("sts").get_caller_identity()
    check("AWS credentials work", True)
    print("      account", ident["Account"], "|", ident["Arn"].split("/")[-1])
    model = os.getenv("BEDROCK_SMALL_MODEL_ID", "")
    if model and model != "REPLACE_ME":
        r = sess.client("bedrock-runtime").converse(
            modelId=model,
            messages=[{"role": "user", "content": [{"text": "Reply with the single word: ready"}]}],
            inferenceConfig={"maxTokens": 10},
        )
        check("Bedrock model call works", True)
        print("      model says:", r["output"]["message"]["content"][0]["text"].strip())
    else:
        check("Bedrock model ID set in .env", False, "trainer shares model ID on Day 1")
except Exception as e:  # noqa: BLE001
    check("AWS / Bedrock", False, f"{type(e).__name__}: {str(e)[:150]}")

print("\nALL GREEN - you're ready!" if ok_all else "\nFix the [!!] lines, then run again. Stuck? Call the trainer.")
