from datetime import datetime
from db import models
from db.connection import init_db, get_session
from api.endpoint import get_price

# create tables
init_db()
print("tables created")

# fetch from API
zone = 'SE3'
start = datetime(2024, 7, 27, 22, 0)
end = datetime(2024, 7, 28, 22, 0)

records = get_price(zone, start, end)
print(f"fetched {len(records)} records")
