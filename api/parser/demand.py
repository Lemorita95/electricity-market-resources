import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from config import QUERY_CONFIGS
from db.models import Demand


def parse_demand(root: ET.Element, zone: str) -> list[Demand]:
    cfg = QUERY_CONFIGS['demand']
    ns = {'ns': cfg['namespace']}
    records = []

    for ts in root.findall('ns:TimeSeries', ns):
        for period in ts.findall('ns:Period', ns):  # loop all periods
            resolution = period.find('ns:resolution', ns).text
            start = datetime.fromisoformat(period.find('ns:timeInterval/ns:start', ns).text.replace('Z', '+00:00'))
            interval = 15 if resolution == 'PT15M' else 60

            for point in period.findall('ns:Point', ns):
                pos = int(point.find('ns:position', ns).text)
                quantity = float(point.find('ns:quantity', ns).text)
                timestamp = start + timedelta(minutes=interval * (pos - 1))

                records.append(Demand(
                    zone=zone,
                    timestamp=timestamp,
                    resolution=resolution,
                    quantity=quantity,
                    unit=cfg['unit']
                ))

    return records