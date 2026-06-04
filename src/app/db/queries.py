from sqlmodel import Session, select
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.model import Feature, Price, Demand, Weather

BATCH_SIZE = 1000  # chunk size for bulk operations

# BASE MODELS > FEATURE
FEATURE_ROUTER = {
    Price: {
        'price': 'price',
        # 'currency': 'price_currency',
    },
    Demand: {
        'quantity': 'quantity',
        # 'unit': 'quantity_unit',
    },
    Weather: {
        'fdir': 'fdir',
        'ssrd': 'ssrd',
        'temperature_2m': 'temperature_2m',
        'wind_u_10m': 'wind_u_10m',
        'wind_v_10m': 'wind_v_10m',
    },
}


def _record_to_feature_row(record) -> dict:
    router = FEATURE_ROUTER.get(type(record))
    if router is None:
        raise ValueError(f"Unsupported record type for feature routing: {type(record).__name__}")

    row = {
        'zone': record.zone,
        'timestamp': record.timestamp,
    }
    for source_field, target_field in router.items():
        value = getattr(record, source_field)
        if value is not None:
            row[target_field] = value
    return row


def _merge_feature_rows(records: list) -> list[dict]:
    merged = {}
    for record in records:
        row = _record_to_feature_row(record)
        key = (row['zone'], row['timestamp'])
        if key not in merged:
            merged[key] = row
            continue

        existing = merged[key]
        # if existing.get('resolution') is None and row.get('resolution') is not None:
        #     existing['resolution'] = row['resolution']

        for column, value in row.items():
            if column in {'zone', 'timestamp'}:
                continue
            if value is not None:
                existing[column] = value

    return list(merged.values())


def _build_conflict_update(columns: set) -> dict:
    return {
        column: getattr(insert(Feature).excluded, column)
        for column in columns
        if column not in {'zone', 'timestamp'}
    }


def upsert_feature_rows(session: Session, records: list[Feature]) -> None:
    if not records:
        return

    rows = _merge_feature_rows(records)
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]
        all_columns = set().union(*(row.keys() for row in chunk))
        stmt = insert(Feature).values(chunk).on_conflict_do_update(
            constraint='uq_feature_zone_timestamp',
            set_=_build_conflict_update(all_columns)
        )
        session.exec(stmt)
    session.commit()


async def async_upsert_feature_rows(async_session: AsyncSession, records: list[Feature]) -> None:
    if not records:
        return

    rows = _merge_feature_rows(records)
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i:i + BATCH_SIZE]
        all_columns = set().union(*(row.keys() for row in chunk))
        stmt = insert(Feature).values(chunk).on_conflict_do_update(
            constraint='uq_feature_zone_timestamp',
            set_=_build_conflict_update(all_columns)
        )
        await async_session.execute(stmt)
    await async_session.commit()


def fetch_features(session: Session, zone: str, start: datetime, end: datetime) -> list[Feature]:
    statement = select(Feature).where(
        Feature.zone == zone,
        Feature.timestamp >= start,
        Feature.timestamp <= end,
    )

    return session.exec(statement.order_by(Feature.timestamp)).all()


def _build_missing_ranges(start: datetime, end: datetime, timestamps: list[datetime]) -> list[dict]:
    if not timestamps:
        return [{'start': start, 'end': end}]

    gaps = []
    prev = start
    for ts in sorted(set(timestamps)):
        if ts > prev:
            gaps.append({'start': prev, 'end': ts})
        prev = ts

    if prev < end:
        gaps.append({'start': prev, 'end': end})

    consecutive_gaps = []
    gap_start = gaps[0]['start']
    for i in range(len(gaps)-1):

        if gaps[i]['end'] == gaps[i+1]['start']:
            continue

        gap_end = gaps[i]['end']
        consecutive_gaps.append({'start': gap_start, 'end': gap_end})

        gap_start = gaps[i+1]['start']

    consecutive_gaps.append({'start': gap_start, 'end': gaps[-1]['end']})

    return consecutive_gaps


def get_timestamps(session: Session, zone: str, start: datetime, end: datetime):
    statement = select(Feature.timestamp).where(
        Feature.zone == zone,
        Feature.timestamp >= start,
        Feature.timestamp <= end,
    )

    timestamps = session.exec(statement.order_by(Feature.timestamp)).all()
    return {
        'zone': zone,
        'start': start,
        'end': end,
        'existing_timestamps': timestamps,
        'missing_ranges': _build_missing_ranges(start, end, timestamps),
    }


def get_source_timestamps(session: Session, zone: str, start: datetime, end: datetime, source: str):
    if source == 'entsoe_price':
        source_condition = Feature.price.is_not(None)
    elif source == 'entsoe_demand':
        source_condition = Feature.quantity.is_not(None)
    elif source == 'copernicus':
        source_condition = or_(
            Feature.fdir.is_not(None),
            Feature.ssrd.is_not(None),
            Feature.temperature_2m.is_not(None),
            Feature.wind_u_10m.is_not(None),
            Feature.wind_v_10m.is_not(None),
        )
    else:
        raise ValueError(f'Unsupported source: {source}')

    statement = select(Feature.timestamp).where(
        Feature.zone == zone,
        Feature.timestamp >= start,
        Feature.timestamp <= end,
        source_condition,
    )

    timestamps = session.exec(statement.order_by(Feature.timestamp)).all()
    return {
        'zone': zone,
        'source': source,
        'start': start,
        'end': end,
        'existing_timestamps': timestamps,
        'missing_ranges': _build_missing_ranges(start, end, timestamps),
    }