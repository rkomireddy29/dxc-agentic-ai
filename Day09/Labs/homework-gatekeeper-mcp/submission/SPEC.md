# SPEC: Gatekeeper MCP server v1

- Server name: "AskIT Gatekeeper".
- Tool 1: `route_ticket(text)` calls `route()` from `gatekeeper.py` and returns the team name.
- Tool 2: `needs_approval(action, user_id, hour)` calls `needs_approval()` from `gatekeeper.py` and returns only the boolean `approval` field.
- Match the real parameter names and types of the function in `gatekeeper.py`.
- Every tool has a clear one-sentence description a model can choose by.
- Runs over stdio by default; with the argument `--http` it runs on port `8778`.
- Also write `submission/test_gatekeeper_server.py`: it starts the server, lists the tools, calls each tool with 3 examples, and prints `PASS` or `FAIL` per call.
