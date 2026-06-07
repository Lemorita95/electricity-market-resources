from datetime import datetime, timezone
from api.endpoint import get_demand

DATE_START = datetime(2023, 1, 1, tzinfo=timezone.utc)
DATE_END = datetime(2023, 1, 2, tzinfo=timezone.utc)

try:
    results = get_demand('SE1', DATE_START, DATE_END)
except Exception as e:
    print(f"  [{'SE1'}] {'demand'} failed: {e}")

print(results)


