# Ex6 — Rasa structured half

## Your answer

В моём прогоне `make ex6` (session `sess_619fef744015`, tier 1 — stdlib
mock на `127.0.0.1:5905/webhooks/rest/webhook`) `RasaStructuredHalf`
собрала чистый бронь-payload и отдала его mock-серверу, который
вернул `Booking confirmed. Reference: BK-7D401E9E.` Итоговый объект
из лога: `committed=True`, `booking={venue_id: haymarket_tap,
date: 2026-04-25, time: 19:30, party_size: 6, deposit_gbp: 200,
duration_hours: 3, catering_tier: bar_snacks}`,
`booking_reference=BK-7D401E9E`.

Структурно `structured_half.py` делает три вещи. Первое — нормализация
ввода, который пришёл из `loop half`: `parse_currency_gbp` принимает
`"£540"`, `"540"`, `"540.00"`, но режет отрицательные значения через
`SA_VAL`; `parse_time_24h` приводит `"19:30"`, `"7:30 PM"`, `"19.30"`
к одной форме `HH:MM`; `parse_party_size` отбрасывает ноль и
отрицательные; `canonicalise_venue_id` сводит `"Haymarket Tap"` и
`"haymarket-tap"` к `haymarket_tap`. После этого
`normalise_booking_payload` собирает словарь ровно той формы, которую
ждёт Rasa-бот — это и проверяет публичный тест
`test_normalise_booking_payload_produces_rasa_shape`.

Второе — собственно вызов Rasa. POST на `/webhooks/rest/webhook` с
`{"sender": <session_id>, "message": "/start_booking" + payload}`,
обработка ответа, поиск `custom.action ∈ {committed, rejected,
needs_clarification}`, и возврат `committed=True/False` наверх.
Бот-сторона лежит в `rasa_project/`: `flows.yml` объявляет
`confirm_booking`-flow, а кастомный action `ActionValidateBooking`
делает финальную бизнес-валидацию — `party_size ≤ 8` (это
`maximum_party_size_for_auto_booking` из `catering.json`) и
`deposit_gbp ≤ 300`. Всё, что не проходит, возвращается как
`rejected` с понятной причиной — большие группы и дорогие сделки
эскалируются менеджеру, не подтверждаются автоматом.

Третье — разделение зон ответственности, которое мне здесь нравится
больше всего. Loop half (LLM) свободно «придумывает», что именно
бронировать; structured half (Rasa) аккуратно проверяет, что
бронь укладывается в правила, и только потом фиксирует. То есть
LLM генерирует, а детерминированный слой подтверждает — фабрикации
вроде `party=20` или `deposit=£900` отлетают на `validate_booking`
и не попадают в `committed=True`, как раз тот контракт, что
закрывает риски Ex5.
