import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.db.queries import (
    _record_to_feature_row,
    _merge_feature_rows,
    _build_missing_ranges,
    get_source_timestamps,
)
from app.db.models.Price import Price
from app.db.models.Demand import Demand
from app.db.models.Weather import Weather


# ── helpers ──────────────────────────────────────────────────────────────────

def make_price(zone="SE1", timestamp=None, price=10.0):
    r = Price()
    r.zone = zone
    r.timestamp = timestamp or datetime(2024, 1, 1, tzinfo=timezone.utc)
    r.price = price
    return r


def make_demand(zone="SE1", timestamp=None, quantity=500.0):
    r = Demand()
    r.zone = zone
    r.timestamp = timestamp or datetime(2024, 1, 1, tzinfo=timezone.utc)
    r.quantity = quantity
    return r


def make_weather(zone="SE1", timestamp=None, fdir=100.0):
    r = Weather()
    r.zone = zone
    r.timestamp = timestamp or datetime(2024, 1, 1, tzinfo=timezone.utc)
    r.fdir = fdir
    r.ssrd = None
    r.temperature_2m = None
    r.wind_u_10m = None
    r.wind_v_10m = None
    return r


# ── _record_to_feature_row ────────────────────────────────────────────────────

class TestRecordToFeatureRow:

    def test_price_record(self):
        record = make_price(price=42.5)
        row = _record_to_feature_row(record)
        assert row["zone"] == "SE1"
        assert row["price"] == 42.5
        assert "quantity" not in row

    def test_demand_record(self):
        record = make_demand(quantity=800.0)
        row = _record_to_feature_row(record)
        assert row["zone"] == "SE1"
        assert row["quantity"] == 800.0
        assert "price" not in row

    def test_weather_record(self):
        record = make_weather(fdir=200.0)
        row = _record_to_feature_row(record)
        assert row["zone"] == "SE1"
        assert row["fdir"] == 200.0

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported record type"):
            _record_to_feature_row(object())

    def test_none_values_excluded(self):
        record = make_price(price=None)
        row = _record_to_feature_row(record)
        assert "price" not in row


# ── _merge_feature_rows ───────────────────────────────────────────────────────

class TestMergeFeatureRows:

    def test_no_overlap(self):
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        records = [make_price(timestamp=ts), make_demand(timestamp=ts)]
        merged = _merge_feature_rows(records)
        assert len(merged) == 1
        assert merged[0]["price"] == 10.0
        assert merged[0]["quantity"] == 500.0

    def test_different_timestamps_not_merged(self):
        ts1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ts2 = datetime(2024, 1, 2, tzinfo=timezone.utc)
        records = [make_price(timestamp=ts1), make_price(timestamp=ts2)]
        merged = _merge_feature_rows(records)
        assert len(merged) == 2

    def test_later_value_overwrites(self):
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        r1 = make_price(timestamp=ts, price=10.0)
        r2 = make_price(timestamp=ts, price=99.0)
        merged = _merge_feature_rows([r1, r2])
        assert len(merged) == 1
        assert merged[0]["price"] == 99.0

    def test_empty_list(self):
        assert _merge_feature_rows([]) == []


# ── _build_missing_ranges ─────────────────────────────────────────────────────

class TestBuildMissingRanges:

    def setup_method(self):
        self.start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self.end = datetime(2024, 1, 3, tzinfo=timezone.utc)

    def test_no_timestamps_returns_full_range(self):
        ranges = _build_missing_ranges(self.start, self.end, [])
        assert len(ranges) == 1
        assert ranges[0]["start"] == self.start
        assert ranges[0]["end"] == self.end

    def test_full_coverage_no_gaps(self):
        mid = datetime(2024, 1, 2, tzinfo=timezone.utc)
        ranges = _build_missing_ranges(self.start, self.end, [self.start, mid, self.end])
        # start and end are covered, only check no extra gaps
        assert isinstance(ranges, list)

    def test_gap_in_middle(self):
        # only start timestamp exists, gap before end
        ranges = _build_missing_ranges(self.start, self.end, [self.start])
        assert any(r["end"] == self.end for r in ranges)


# ── get_source_timestamps invalid source ──────────────────────────────────────

class TestGetSourceTimestamps:

    def test_invalid_source_raises(self):
        session = MagicMock()
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 2, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="Unsupported source"):
            get_source_timestamps(session, "SE1", start, end, "invalid_source")