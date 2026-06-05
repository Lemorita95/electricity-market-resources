from datetime import datetime, timezone

from app.config import EIC_CODES, QUERY_CONFIGS

from app.api.client import CopernicusClient
from app.api.endpoint import get_era5
from app.api.parser import parse_weather

client = CopernicusClient()

START = datetime(2025, 5, 30, tzinfo=timezone.utc)
END = datetime(2025, 6, 1, tzinfo=timezone.utc)

cfg = QUERY_CONFIGS['copernicus']
dataset = cfg['dataset']
request = cfg['request']

location = 'SE1'

# request["location"] = {"longitude": EIC_CODES[location]['lon'], "latitude": EIC_CODES[location]['lat']}
# request["date"] = ["2023-05-01/2023-05-28"]

# cds_results = client.retrieve(dataset, request)
# parsed = parse_weather(cds_results, 'SE1')

results = get_era5(location, START, END)

print(results)