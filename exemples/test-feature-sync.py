from datetime import datetime, timezone, timedelta
from sqlmodel import Session
from db.connection import init_db, engine
from db.queries import get_source_timestamps, fetch_features
from scripts.feature_sync import fetch_zone_source, fetch_zone
from config import EIC_CODES

init_db()

# Test 1: Check what data is missing for one zone in one source
zone = list(EIC_CODES.keys())[0]
start = datetime(2024, 1, 1, 3, 0, tzinfo=timezone.utc)
end = datetime(2024, 1, 8, 0, 0, tzinfo=timezone.utc)

print(f"Testing {zone} for 2024-01-01 to 2024-01-08")
print("-" * 60)

with Session(engine) as session:
    # Check entsoe price gaps
    entsoe_status_price = get_source_timestamps(session, zone, start, end, 'entsoe_price')
    print(f"\nENTSOE Price:")
    print(f"  Existing timestamps: {len(entsoe_status_price['existing_timestamps'])}")
    print(f"  Missing ranges: {len(entsoe_status_price['missing_ranges'])}")
    for gap in entsoe_status_price['missing_ranges']:
        print(f"    - {gap['start']} to {gap['end']}")

    # Check entsoe demand gaps
    entsoe_status_demand = get_source_timestamps(session, zone, start, end, 'entsoe_demand')
    print(f"\nENTSOE Demand:")
    print(f"  Existing timestamps: {len(entsoe_status_demand['existing_timestamps'])}")
    print(f"  Missing ranges: {len(entsoe_status_demand['missing_ranges'])}")
    for gap in entsoe_status_demand['missing_ranges']:
        print(f"    - {gap['start']} to {gap['end']}")

    # Check copernicus gaps
    copernicus_status = get_source_timestamps(session, zone, start, end, 'copernicus')
    print(f"\nCOPERNICUS:")
    print(f"  Existing timestamps: {len(copernicus_status['existing_timestamps'])}")
    print(f"  Missing ranges: {len(copernicus_status['missing_ranges'])}")
    for gap in copernicus_status['missing_ranges']:
        print(f"    - {gap['start']} to {gap['end']}")

print("\n" + "=" * 60)
print("Test 2: Fetch entsoe for one zone in one gap")
print("-" * 60)

with Session(engine) as session:
    entsoe_status = get_source_timestamps(session, zone, start, end, 'entsoe_demand')

if entsoe_status['missing_ranges']:
    for gap in entsoe_status['missing_ranges']:
        print(f"\nFetching {zone} entsoe from {gap['start']} to {gap['end']}")
        print("This will attempt to fetch real data from ENTSO-E...")
        try:
            fetch_zone_source(zone, gap['start'], gap['end'], 'entsoe_demand', progress_callback=lambda msg, q: print(f"  [{q}] {msg}"))
            print("\n✓ Fetch completed successfully")
        except Exception as e:
            print(f"\n✗ Fetch failed: {e}")
else:
    print(f"\n✓ {zone} entsoe up-to-date")

print("\n" + "=" * 60)
print("Test 3: Verify data was inserted")
print("-" * 60)

with Session(engine) as session:
    entsoe_status = get_source_timestamps(session, zone, start, end, 'entsoe_demand')
    print(f"\nAfter sync:")
    print(f"  Existing ENTSOE timestamps: {len(entsoe_status['existing_timestamps'])}")
    print(f"  Remaining gaps: {len(entsoe_status['missing_ranges'])}")
