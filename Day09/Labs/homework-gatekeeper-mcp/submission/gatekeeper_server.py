from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parent
GATEKEEPER_PATH = BASE_DIR / "gatekeeper.py"

spec = importlib.util.spec_from_file_location("gatekeeper", GATEKEEPER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load gatekeeper.py")
gatekeeper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gatekeeper)

mcp = FastMCP("AskIT Gatekeeper")


@mcp.tool(description="Route a ticket description to the correct support team.")
def route_ticket(text: str) -> str:
    return gatekeeper.route(text)


@mcp.tool(description="Decide whether an action needs approval and return only the approval flag.")
def needs_approval(action: str, user_id: str, hour: int) -> bool:
    result = gatekeeper.needs_approval(action, user_id, hour)
    return bool(result["approval"])


def main() -> None:
    parser = argparse.ArgumentParser(prog="gatekeeper_server")
    parser.add_argument("--http", action="store_true", help="Run the server over HTTP on port 8778.")
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8778)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
