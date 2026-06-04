import time
from datetime import datetime, timezone

from app.api.endpoint import eumet_client, get_sarah3

START = datetime(2026, 5, 30, tzinfo=timezone.utc)
END = datetime.now(timezone.utc)


def status(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


eumet_client._status_callback = status

t0 = time.time()
results = get_sarah3('SE1', start=START, end=END, progress_callback=status)
total_time = time.time() - t0

print(f"\ntotal: {total_time:.2f}s — {len(results)} records")

# compute GTI for each spatial resolution > aggregate by NUTS2 > save to db
