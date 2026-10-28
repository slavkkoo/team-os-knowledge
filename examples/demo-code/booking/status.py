"""Демо-код выдуманного сервиса онлайн-записи Acme.

Нужен только для того, чтобы drift-чекер (brain/scripts/check_drift.py)
работал из коробки. Подключив свой код, удалите каталог examples/.

Красное демо: переименуйте значение ниже (например, "no_show" -> "missed")
и попробуйте закоммитить — pre-commit хук упадёт, потому что
brain/product/object-model.md не знает нового статуса.
"""


class BookingStatus:
    """Статус записи клиента к мастеру."""

    STATUS_PENDING = "pending"        # создана, ждёт подтверждения мастера
    STATUS_CONFIRMED = "confirmed"    # мастер подтвердил
    STATUS_CANCELLED = "cancelled"    # отменена клиентом или мастером
    STATUS_COMPLETED = "completed"    # визит состоялся
    STATUS_NO_SHOW = "no_show"        # клиент не пришёл

    ALL = (STATUS_PENDING, STATUS_CONFIRMED, STATUS_CANCELLED,
           STATUS_COMPLETED, STATUS_NO_SHOW)
