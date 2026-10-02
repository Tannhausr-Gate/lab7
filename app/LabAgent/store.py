import json
from datetime import datetime, timezone
from pathlib import Path

import config
from controls import for_storage


def write_event(event: dict) -> dict:
    """Append one event to the audit log. Content is redacted before the write."""
    record = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    safe = for_storage(record)

    path = Path(config.AUDIT_LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(safe) + "\n")
    return safe