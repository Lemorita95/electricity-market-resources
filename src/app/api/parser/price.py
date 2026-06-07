import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

from app.config import QUERY_CONFIGS
from app.db.models import Price


def parse_price(root: ET.Element, zone: str) -> list[Price]:
    cfg = QUERY_CONFIGS['price']
    ns = {'ns': cfg['namespace']}
    records = []

    for ts in root.findall('ns:TimeSeries', ns):
        period = ts.find('ns:Period', ns)
        resolution = period.find('ns:resolution', ns).text
        start = datetime.fromisoformat(period.find('ns:timeInterval/ns:start', ns).text.replace('Z', '+00:00'))
        currency = ts.find('ns:currency_Unit.name', ns).text
        interval = 15 if resolution == 'PT15M' else 60

        for point in period.findall('ns:Point', ns):
            pos = int(point.find('ns:position', ns).text)
            price = float(point.find('ns:price.amount', ns).text)
            timestamp = start + timedelta(minutes=interval * (pos - 1))

            records.append(Price(
                zone=zone,
                timestamp=timestamp,
                resolution=resolution,
                price=price,
                currency=currency,
            ))

    return records