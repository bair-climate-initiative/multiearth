from datetime import datetime
from typing import Tuple


def datetime_str_to_value(s: str) -> Tuple[datetime]:
    components = s.split("/")
    start = datetime.strptime(components[0], "%Y-%m-%d")
    end = datetime.strptime(components[0], "%Y-%m-%d")
    return (start, end)
