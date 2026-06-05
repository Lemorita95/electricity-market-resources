from datetime import datetime

from app.bootstrap.init_db import init_db
from app.db import model
from app.db.connection import init_db, get_session
from app.api.endpoint import get_price

# create tables
init_db()
print("tables created")

# fetch from API
zone = 'SE3'
start = datetime(2024, 7, 27, 22, 0)
end = datetime(2024, 7, 28, 22, 0)

records = get_price(zone, start, end)
print(f"fetched {len(records)} records")
