from datetime import datetime, timezone, timedelta

TIMEZONES = {
    "Jordan (UTC+3)":           3,
    "Saudi Arabia (UTC+3)":     3,
    "UAE (UTC+4)":              4,
    "Qatar (UTC+3)":            3,
    "Kuwait (UTC+3)":           3,
    "Egypt (UTC+2)":            2,
    "Turkey (UTC+3)":           3,
    "UK / BST (UTC+1)":         1,
    "UTC":                      0,
    "USA Eastern (UTC-4)":     -4,
    "USA Central (UTC-5)":     -5,
    "USA Mountain (UTC-6)":    -6,
    "USA Pacific (UTC-7)":     -7,
    "Canada Eastern (UTC-4)":  -4,
    "Mexico City (UTC-5)":     -5,
}

DEFAULT_TZ_NAME   = "Jordan (UTC+3)"
DEFAULT_TZ_OFFSET = 3


def _parse(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)


def format_kickoff(kickoff_utc: str, offset: int) -> str:
    """Return 'DD Mon YYYY, HH:MM' in local time."""
    local = _parse(kickoff_utc) + timedelta(hours=offset)
    return local.strftime("%d %b %Y, %H:%M")


def format_time_only(kickoff_utc: str, offset: int) -> str:
    local = _parse(kickoff_utc) + timedelta(hours=offset)
    return local.strftime("%H:%M")


def local_date(kickoff_utc: str, offset: int) -> str:
    local = _parse(kickoff_utc) + timedelta(hours=offset)
    return local.strftime("%Y-%m-%d")


def tz_label(offset: int) -> str:
    sign = "+" if offset >= 0 else ""
    return f"UTC{sign}{offset}"
