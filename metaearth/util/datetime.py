"""Datetime utilities."""
from datetime import datetime
from typing import Tuple


def datetime_str_to_value(s: str) -> Tuple[datetime, datetime]:
    """Convert datetime string to a tuple containing a start and end date."""
    components = s.split("/")
    start = datetime.strptime(components[0], "%Y-%m-%d")
    end = datetime.strptime(components[0], "%Y-%m-%d")
    return (start, end)
