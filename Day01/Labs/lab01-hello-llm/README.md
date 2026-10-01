# Lab 1 — Hello, LLM

**AskIT today:** reads a helpdesk ticket, answers it, and turns it into clean, validated data.

| Part | File | Time | Challenges |
|---|---|---|---|
| **A** | `A_bedrock_playground.md` | 40 min (incl. setup) | Tasks A1, A2 (+ stretch) |
| **B** | `lab01a_first_call.py` | 40 min | Challenge 1, 2, 3 (+ stretch) |
| **C** | `lab01b_extract.py` | 40 min | Challenge 4, 5 (+ stretch) |

## How to work
1. Open the file in VS Code. Find `TODO-n` — the hints tell you exactly what to write.
2. Run it (VS Code terminal, `(.venv)` must be showing):
   ```
   python Day01\Labs\lab01-hello-llm\lab01a_first_call.py
   ```
3. Check yourself any time:
   ```
   pytest Day01\Labs\lab01-hello-llm
   ```
   5 tests = 5 challenges. Aim for **5 passed**.
4. At the end of class click **🏁 Day End** in the session page — it pushes everything.

## Lab B — first Bedrock call (`lab01a_first_call.py`)
| # | Do | Test |
|---|---|---|
| Challenge 1 | TODO-1: call `client.converse(...)`, return the reply text | `test_challenge_1` |
| Challenge 2 | TODO-2: return input tokens, output tokens (latency is ready-made) | `test_challenge_2` |
| Challenge 3 | TODO-3: ask 2 models about 5 tickets, then **run the script** (saves `submission\lab01a_results.json`) | `test_challenge_3` |
| ⭐ Stretch | Look up Bedrock on-demand prices for your two models. Estimate the daily cost of answering **1,000 tickets/day** with each. Write it in `submission\stretch_cost.md`. | — |

**Think:** which model would you pick for AskIT's first reply? Why?

## Lab C — structured extraction (`lab01b_extract.py`)
| # | Do | Test |
|---|---|---|
| Challenge 4 | TODO-4: complete the `Ticket` schema (5 fields, with rules) | `test_challenge_4` |
| Challenge 5 | TODO-5: force the model to fill the schema using a tool, then validate | `test_challenge_5` |
| Run | `python Day01\Labs\lab01-hello-llm\lab01b_extract.py` → 5 tickets marked OK / DIFF. *(Ignore the TODO-6 note in the file and the Langfuse message at the end — later session.)* | — |
| ⭐ Stretch A | Extract the same ticket 5× at temperature 0 and 5× at 1.0. How many fields changed? Note it in `submission\stretch_temperature.md` | — |
| ⭐ Stretch B | Run all 100 tickets (change `[:5]`). What % match the human labels for category and priority? Where does AskIT disagree — and who is right? | — |

## Stuck?
| Symptom | Fix |
|---|---|
| `Set BEDROCK_..._MODEL_ID in .env` | Paste the model IDs the trainer shared into `.env` |
| `AccessDeniedException` | Model not enabled for your user — tell the trainer |
| `ThrottlingException` (after long wait) | Whole class calling at once — wait 30 s and re-run |
| `ModuleNotFoundError` | `(.venv)` not showing — close terminal, open a new one in VS Code |
