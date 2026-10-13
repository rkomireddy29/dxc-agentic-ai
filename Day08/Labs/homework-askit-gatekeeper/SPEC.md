# SPEC: AskIT Gatekeeper v1

## Purpose
Three small, testable safety functions for the AskIT helpdesk agent.

## R1 route(text: str) -> str
- Returns one team: "Security", "Access", "Network", "Hardware" or "General".
- Match words case-insensitive, WHOLE WORDS only ("download" does not match "down").
- First match wins, in this order:
  Security: phishing, malware, breach, suspicious, ransomware
  Access: password, locked, login, mfa, access
  Network: vpn, wifi, network, internet
  Hardware: laptop, printer, screen, keyboard, phone
  General: none of the above
- Empty or blank text: raise ValueError.

## R2 needs_approval(action: str, user_id: str, hour: int) -> dict
- Returns {"approval": True or False, "approver": "<who>"}.
- Read actions: "search_kb", "get_ticket". Write actions: "reset_password", "update_ticket", "grant_access".
- Any other action: raise ValueError. hour must be an int from 0 to 23, else raise ValueError.
- VIP users: EMP-1001, EMP-1012, EMP-1023.
- Night means hour >= 20 or hour < 8.
- Rules, first match wins:
  1. Read action by a VIP: approval = True. If yes, approver "it manager", else approver "none".
  2. Read action by anyone else: approval False, approver "none".
  3. Write action by a VIP (day or night): approval True, approver "it manager".
  4. Write action at night: approval True, approver "on-call".
  5. Write action in the day: approval True, approver "service desk lead".

## R3 safe_to_remember(text: str) -> bool
- Returns True if the fact may be saved in long-term memory, else False.
- False if the text is empty or blank.
- False if it contains the whole word password, passcode, otp or pin (case-insensitive).
- False if it contains the whole word address or the phrase home address (case-insensitive).
- False if it contains a number with 6 or more digits, ignoring spaces and dashes (card numbers, OTPs, account numbers).
- Otherwise True.
- Saved facts are kept for D3 days (D3), then deleted. (Not coded here, recorded for the design.)

## Acceptance Criteria (examples)
- AC1 route("VPN error 809 since morning") -> "Network"
- AC2 route("Phishing email asked for my password") -> "Security" (order matters)
- AC3 route("Cannot download files") -> "General" (whole words)
- AC4 needs_approval("reset_password", "EMP-1002", 10) -> approval True, approver "service desk lead"
- AC5 needs_approval("update_ticket", "EMP-1001", 10) -> approval True, approver "it manager"
- AC6 needs_approval("delete_user", "EMP-1002", 10) -> ValueError
- AC7 safe_to_remember("My laptop is a Dell XPS 13") -> True
- AC8 safe_to_remember("Card 4111 1111 1111 1111 please") -> False

## Out of scope
UI, database, LLM calls, logging.

## Changelog
- v1 initial
- v2 client change: ransomware, no home addresses