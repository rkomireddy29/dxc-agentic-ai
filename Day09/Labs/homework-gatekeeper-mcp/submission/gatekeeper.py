import re


_ROUTE_RULES = (
    ("Security", ("phishing", "malware", "breach", "suspicious", "ransomware")),
    ("Access", ("password", "locked", "login", "mfa", "access")),
    ("Network", ("vpn", "wifi", "network", "internet")),
    ("Hardware", ("laptop", "printer", "screen", "keyboard", "phone")),
)

_READ_ACTIONS = {"search_kb", "get_ticket"}
_WRITE_ACTIONS = {"reset_password", "update_ticket", "grant_access"}
_VIP_USERS = {"EMP-1001", "EMP-1012", "EMP-1023"}


def route(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must not be empty")

    lowered = text.lower()
    for team, keywords in _ROUTE_RULES:
        for keyword in keywords:
            if re.search(r"\b" + re.escape(keyword) + r"\b", lowered):
                return team
    return "General"


def needs_approval(action: str, user_id: str, hour: int) -> dict:
    if action not in _READ_ACTIONS and action not in _WRITE_ACTIONS:
        raise ValueError("invalid action")
    if not isinstance(hour, int) or hour < 0 or hour > 23:
        raise ValueError("hour must be an int from 0 to 23")

    is_vip = user_id in _VIP_USERS
    is_night = hour >= 20 or hour < 8

    if action in _READ_ACTIONS:
        if is_vip:
            return {"approval": True, "approver": "it manager"}
        return {"approval": False, "approver": "none"}

    if is_vip:
        return {"approval": True, "approver": "it manager"}
    if is_night:
        return {"approval": True, "approver": "on-call"}
    return {"approval": True, "approver": "service desk lead"}


def safe_to_remember(text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False

    lowered = text.lower()
    if re.search(r"\b(password|passcode|otp|pin)\b", lowered):
        return False
    if re.search(r"\bhome address\b", lowered) or re.search(r"\baddress\b", lowered):
        return False

    compact = re.sub(r"[\s-]", "", text)
    if re.search(r"\d{6,}", compact):
        return False

    return True