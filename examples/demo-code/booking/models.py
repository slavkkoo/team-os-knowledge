"""Демо-модель записи (Acme). См. booking/status.py."""
from dataclasses import dataclass
from datetime import datetime

from .status import BookingStatus


@dataclass
class Booking:
    """Запись клиента на услугу к мастеру в конкретный слот."""

    id: str
    master_id: str
    service_id: str
    starts_at: datetime
    status: str = BookingStatus.STATUS_PENDING
