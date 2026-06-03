from api.endpoint import get_price
from datetime import datetime, timezone

START = datetime(2026, 5, 30, tzinfo=timezone.utc)
END = datetime.now(timezone.utc)

all_results = get_price('SE1', start=START, end=END, progress_callback=None)
print()