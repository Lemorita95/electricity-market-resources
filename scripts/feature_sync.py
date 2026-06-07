from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlmodel import Session
from db.connection import init_db, engine
from db.queries import upsert_feature_rows, get_source_timestamps
from api.endpoint import get_price, get_demand, entsoe_client, get_era5, copernicus_client
from config import EIC_CODES
from scripts.utils import TerminalMonitor

def get_fetch_start() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)

def get_fetch_end() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)


def fetch_zone_source(zone: str, start: datetime, end: datetime, source: str, progress_callback=None) -> None:
    with Session(engine) as session:
        records = []
        status = get_source_timestamps(session, zone, start, end, source)

        if status['missing_ranges']:
            for gap in status['missing_ranges']:
                def cb(msg, q=source):
                    if progress_callback:
                        progress_callback(msg, q)
                try:
                    if source == 'entsoe_price':
                        price_records = get_price(zone, gap['start'], gap['end'], progress_callback=cb)
                        records.extend(price_records)
                    elif source == 'entsoe_demand':
                        demand_records = get_demand(zone, gap['start'], gap['end'], progress_callback=cb)
                        records.extend(demand_records)
                    elif source == 'copernicus':
                        weather_records = get_era5(zone, gap['start'], gap['end'], progress_callback=cb)
                        records.extend(weather_records)
                    else:
                        raise ValueError(f"Unsupported source: {source}")
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"failed: {e}", source)
                    return  # skip upsert on failure
        else:
            if progress_callback:
                progress_callback("up-to-date", source)
            return  # nothing to upsert

        if records:
            upsert_feature_rows(session, records)
            if progress_callback:
                progress_callback("done", source)


def fetch_zone(zone: str, start: datetime, end: datetime, progress_callback=None) -> None:
    fetch_zone_source(zone, start, end, 'entsoe_price', progress_callback=progress_callback)
    fetch_zone_source(zone, start, end, 'entsoe_demand', progress_callback=progress_callback)
    fetch_zone_source(zone, start, end, 'copernicus', progress_callback=progress_callback)


def run_daily_fetch(start: datetime | None = None, end: datetime | None = None, source: str | None = None, progress_callback=None) -> dict:
    if end is None:
        end = get_fetch_end()
    if start is None:
        start = get_fetch_start()

    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for zone in EIC_CODES:
            callback = lambda msg, q='', z=zone: progress_callback(z, msg, q) if progress_callback else None
            if source:
                future = executor.submit(fetch_zone_source, zone, start, end, source, progress_callback=callback)
            else:
                future = executor.submit(fetch_zone, zone, start, end, progress_callback=callback)
            futures[future] = zone
        for future in as_completed(futures):
            zone = futures[future]
            try:
                future.result()
                results[zone] = 'done'
            except Exception as e:
                results[zone] = f"failed: {e}"

    return results


if __name__ == "__main__":
    init_db()

    START = datetime(2025, 5, 30, tzinfo=timezone.utc)
    END = START + timedelta(days=3)

    monitor = TerminalMonitor()
    monitor.init_display(EIC_CODES)
    entsoe_client._status_callback = monitor.make_monitor_callback("entso-e")
    copernicus_client._status_callback = monitor.make_monitor_callback("copernicus")
    results = run_daily_fetch(start=START, end=END, progress_callback=monitor.update)
    print("\ndaily fetch complete")
