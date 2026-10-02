import re
import difflib
from typing import Optional, Dict, Any

EXACT_MATCHES = {
    "what time is it": "get_time",
    "what is the time": "get_time",
    "tell me the time": "get_time",
    "current time": "get_time",
    "time": "get_time",
    "list downloads": "list_directory",
    "show downloads": "list_directory",
    "lock screen": "lock_workstation",
    "lock pc": "lock_workstation"
}

REGEX_PATTERNS = {
    # Permite "tell me what time is it" ou "what time is it please", mas NÃO "in tokyo"
    re.compile(r"^(please\s+)?(tell me\s+)?(what time is it|what is the time|current time)(\s+please)?$"): "get_time",
    re.compile(r"^(please\s+)?(lock\s+(the\s+)?(screen|workstation|pc))(\s+please)?$"): "lock_workstation",
    re.compile(r"^(show|list)\s+(my\s+)?downloads$"): "list_directory"
}

LOCATION_MODIFIERS = {"in", "at", "for", "from", "of", "to"}

FUZZY_TARGETS = {
    "what time is it": "get_time",
    "tell me the time": "get_time",
    "list downloads": "list_directory",
    "lock the screen": "lock_workstation"
}
FUZZY_THRESHOLD = 0.88


def normalize(message: str) -> str:
    message = message.strip().lower()
    message = re.sub(r'[^\w\s]', '', message)
    message = re.sub(r'\s+', ' ', message)
    return message

def route_layer_0(message: str) -> Optional[Dict[str, Any]]:
    clean_msg = normalize(message)
    if not clean_msg:
        return None

    words = set(clean_msg.split())

    if "time" in words and not words.isdisjoint(LOCATION_MODIFIERS):
        return None

    if clean_msg in EXACT_MATCHES:
        return {"name": EXACT_MATCHES[clean_msg], "arguments": {}}

    for pattern, tool_name in REGEX_PATTERNS.items():
        if pattern.match(clean_msg):
            return {"name": tool_name, "arguments": {}}

    matches = difflib.get_close_matches(clean_msg, FUZZY_TARGETS.keys(), n=1, cutoff=FUZZY_THRESHOLD)
    if matches:
        return {"name": FUZZY_TARGETS[matches[0]], "arguments": {}}

    return None