from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint, Column
from sqlalchemy.dialects.postgresql import TIMESTAMP

from app.db.models import Demand, Price, Irradiance, Weather

class Feature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    zone: str
    timestamp: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    # resolution: str

    price: Optional[float] = None
    # price_currency: Optional[str] = None

    quantity: Optional[float] = None
    # quantity_unit: Optional[str] = None

    # not included, data acquisition is too slow
    # sis: Optional[float] = None
    # sid: Optional[float] = None
    # irradiance_unit: Optional[str] = None

    fdir: Optional[float] = None
    ssrd: Optional[float] = None
    temperature_2m: Optional[float] = None
    wind_u_10m: Optional[float] = None
    wind_v_10m: Optional[float] = None

    __table_args__ = (
        UniqueConstraint('zone', 'timestamp', name='uq_feature_zone_timestamp'),
    )