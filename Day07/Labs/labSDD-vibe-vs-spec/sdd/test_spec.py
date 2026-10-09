import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from triage import triage


def test_ac1_60_affected_users_is_p1_and_sla_2():
    assert triage({"title": "Issue", "affected_users": 60}) == {
        "priority": "P1",
        "queue": "General",
        "sla_hours": 2,
    }


def test_ac2_email_outage_is_p1():
    assert triage({"title": "Email outage"})["priority"] == "P1"


def test_ac3_download_does_not_match_down():
    assert triage({"title": "Slow download speed"})["priority"] == "P4"


def test_ac4_12_users_is_p2_and_sla_8():
    assert triage({"title": "Issue", "affected_users": 12}) == {
        "priority": "P2",
        "queue": "General",
        "sla_hours": 8,
    }


def test_ac5_urgent_is_p2():
    assert triage({"title": "URGENT: cannot print"})["priority"] == "P2"


def test_ac6_3_users_is_p3_and_sla_24():
    assert triage({"title": "Issue", "affected_users": 3}) == {
        "priority": "P3",
        "queue": "General",
        "sla_hours": 24,
    }


def test_ac7_laptop_wifi_broken_uses_network_queue():
    assert triage({"title": "Laptop wifi broken"})["queue"] == "Network"


def test_ac8_password_reset_uses_access_queue():
    assert triage({"title": "Password reset"})["queue"] == "Access"


def test_ac9_empty_title_and_zero_users_raise_value_error():
    try:
        triage({"title": ""})
        raise AssertionError("expected ValueError for empty title")
    except ValueError:
        pass

    try:
        triage({"title": "Issue", "affected_users": 0})
        raise AssertionError("expected ValueError for zero affected_users")
    except ValueError:
        pass


def test_ac10_vip_issue_with_one_user_is_p3_and_sla_24():
    assert triage({"title": "Issue", "customer_tier": "vip"}) == {
        "priority": "P3",
        "queue": "General",
        "sla_hours": 24,
    }


def test_ac11_vip_email_outage_is_p1_and_sla_2():
    assert triage({"title": "Email outage", "customer_tier": "vip"}) == {
        "priority": "P1",
        "queue": "General",
        "sla_hours": 2,
    }


def test_ac12_phishing_attempt_uses_security_queue():
    assert triage({"title": "Phishing attempt"})["queue"] == "Security"