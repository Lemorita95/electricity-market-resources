import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.web.app import create_app
app = create_app()

from app.web.routes import validate_range


# ── validate_range ────────────────────────────────────────────────────────────

class TestValidateRange:

    def test_valid_range_passes(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 30, tzinfo=timezone.utc)
        validate_range(start, end)  # should not raise

    def test_exactly_90_days_passes(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = start + timedelta(days=90)
        validate_range(start, end)  # should not raise

    def test_over_90_days_raises(self):
        from fastapi import HTTPException
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = start + timedelta(days=91)
        with pytest.raises(HTTPException) as exc_info:
            validate_range(start, end)
        assert exc_info.value.status_code == 400
        assert "90" in exc_info.value.detail


# ── API route tests ───────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_session():
    with patch("app.web.routes.get_session") as mock:
        session = MagicMock()
        mock.return_value = iter([session])
        yield session


class TestWeatherRoute:

    def test_invalid_column_returns_400(self, client, mock_session):
        response = client.get(
            "/api/weather",
            params={
                "zone": "SE1",
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-07T00:00:00Z",
                "column": "invalid_column"
            }
        )
        assert response.status_code == 400
        assert "Invalid column" in response.json()["detail"]

    def test_valid_column_accepted(self, client, mock_session):
        with patch("app.web.routes.fetch_features", return_value=[]):
            response = client.get(
                "/api/weather",
                params={
                    "zone": "SE1",
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-07T00:00:00Z",
                    "column": "fdir"
                }
            )
        assert response.status_code == 200


class TestFetchRoute:

    def test_invalid_source_returns_400(self, client):
        response = client.post(
            "/api/fetch",
            params={"source": "invalid_source"}
        )
        assert response.status_code == 400
        assert "Invalid source" in response.json()["detail"]

    def test_valid_source_starts_job(self, client):
        with patch("app.web.routes._run_in_background", return_value=True):
            response = client.post(
                "/api/fetch",
                params={"source": "entsoe_price"}
            )
        assert response.status_code == 200
        assert response.json()["status"] == "started"

    def test_already_running_returns_409(self, client):
        with patch("app.web.routes._run_in_background", return_value=False):
            response = client.post(
                "/api/fetch",
                params={"source": "entsoe_price"}
            )
        assert response.status_code == 409