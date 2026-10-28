---
owner: dev-lead
tier: evolving
last_reviewed: 2026-10-28
---

# Объектная модель (из кода)

> Что сюда писать: главные сущности продукта, связи между ними и **реальные**
> статусы/перечисления из кода. Частый провал агента — выдумать статус, которого
> нет. Здесь фиксируем настоящие и защищаем их drift-чекером.
>
> Как устроены claim-секции: текст между `<!-- claim:ID -->` и `<!-- /claim:ID -->`
> сверяется с кодом по правилу из `brain/claims.yaml`. Внутри секции — только
> список значений через запятую (или по одному на строку); пояснения пишите
> снаружи. Код ушёл вперёд — коммит в этот репо падает.
>
> Ниже — пример на демо-коде Acme (`examples/demo-code`). Замените своим.

Источник: `examples/demo-code` (срез 2026-10-28). Код главнее этого файла.

## Главные сущности

| Сущность | Класс | Файл |
|---|---|---|
| Запись | `Booking` | `booking/models.py` |
| Статус записи | `BookingStatus` | `booking/status.py` |
| Канал уведомлений | модуль на канал | `notifications/channels/` |

<!-- claim:booking-model-pointer -->
Модель записи — `Booking` в `booking/models.py`: клиент, мастер, услуга, слот, статус.
<!-- /claim:booking-model-pointer -->

## Статусы записи (BookingStatus)

Константы `STATUS_*` в `booking/status.py`. Полный список:

<!-- claim:booking-status-values -->
pending, confirmed, cancelled, completed, no_show
<!-- /claim:booking-status-values -->

Смысл: `pending` — ждёт подтверждения мастера; `confirmed` — подтверждена;
`cancelled` — отменена; `completed` — визит состоялся; `no_show` — клиент не пришёл.

## Каналы уведомлений

Один файл в `notifications/channels/` = один канал:

<!-- claim:notification-channels -->
email, push, sms
<!-- /claim:notification-channels -->
