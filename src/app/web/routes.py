from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from datetime import datetime, timezone
import threading
from pathlib import Path

from app.db.connection import get_session
from app.db.queries import fetch_features
from app.config import EIC_CODES
from app.ingestion.feature_sync import sync_feature


BASE = Path(__file__).resolve().parent
templates = BASE / "templates"

fetch_lock = threading.Lock()
fetch_status_map: dict[str, dict] = {
    "entsoe_price": {"status": "idle"},
    "entsoe_demand": {"status": "idle"},
    "copernicus": {"status": "idle"},
    "all": {"status": "idle"},
}

router = APIRouter()
templates = Jinja2Templates(directory=templates)
MAX_RANGE_DAYS = 90

WEATHER_COLUMNS = ['fdir', 'ssrd', 'temperature_2m', 'wind_u_10m', 'wind_v_10m']


def validate_range(start: datetime, end: datetime):
    if (end - start).days > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Date range cannot exceed {MAX_RANGE_DAYS} days"
        )


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"zones": list(EIC_CODES.keys()), "weather_columns": WEATHER_COLUMNS}
    )


@router.get("/api/price")
def get_price(zone: str, start: datetime, end: datetime, session: Session = Depends(get_session)):
    validate_range(start, end)
    records = fetch_features(session, zone, start, end)
    return [
        {"timestamp": r.timestamp.isoformat(), "price": r.price}
        for r in records if r.price is not None
    ]


@router.get("/api/demand")
def get_demand(zone: str, start: datetime, end: datetime, session: Session = Depends(get_session)):
    validate_range(start, end)
    records = fetch_features(session, zone, start, end)
    return [
        {"timestamp": r.timestamp.isoformat(), "quantity": r.quantity}
        for r in records if r.quantity is not None
    ]


@router.get("/api/weather")
def get_weather(zone: str, start: datetime, end: datetime, column: str, session: Session = Depends(get_session)):
    if column not in WEATHER_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Invalid column: {column}")
    validate_range(start, end)
    records = fetch_features(session, zone, start, end)
    return [
        {"timestamp": r.timestamp.isoformat(), "value": getattr(r, column)}
        for r in records if getattr(r, column) is not None
    ]


def _run_in_background(source: str | None, start: datetime | None = None, end: datetime | None = None):
    key = source or 'all'

    with fetch_lock:
        if fetch_status_map[key]["status"] == "running":
            return False
        fetch_status_map[key]["status"] = "queued"

    def run():
        fetch_status_map[key]["status"] = "running"

        try:
            sync_feature(source=source, start=start, end=end)
            fetch_status_map[key]["status"] = "done"
        except Exception as e:
            fetch_status_map[key]["status"] = "failed"
            fetch_status_map[key]["error"] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return True

@router.post("/api/fetch")
def trigger_fetch(source: str | None = None, start: datetime | None = None, end: datetime | None = None):
    valid_sources = list(fetch_status_map.keys())
    if source and source not in valid_sources:
        raise HTTPException(status_code=400, detail=f"Invalid source. Must be one of {valid_sources}")
    started = _run_in_background(source, start, end)
    if not started:
        raise HTTPException(status_code=409, detail="Fetch already running for this source")
    return {"status": "started", "source": source or "all"}

@router.get("/api/fetch/status")
def fetch_status():
    return fetch_status_map