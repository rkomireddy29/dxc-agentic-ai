# My notes

Q1. D1: yes, because even read-only access to sensitive internal information should still be reviewed when the requester is a VIP. D2: on-call, because night writes should not wait until morning when the action is time-sensitive. D3: 30 days, because it is long enough to be useful for support follow-up but still bounded for privacy and retention.

Q2. R3, the memory rule. I would never let an LLM decide long-term retention on its own because it can accidentally store secrets or personal data, and that needs a deterministic policy with explicit red lines.

Q3. I edited the spec first, then the code. That order matters because the spec is the source of truth; changing it first makes the code change traceable to an explicit rule update and reduces the risk of silently drifting from the intended behavior.
