# Управление календарями

## Команды Telegram

### Добавить календарь
`/calendar <client_type> <url> [название]`
- `client_type` — тип календаря (например `caldav`)
- `url` — URL календаря
- `название` — опционально, имя календаря
- `chat_id` и `chat_type` заполняются автоматически

**Примеры:**
- `/calendar caldav /calendars/__uids__/abc123/calendar`
- `/calendar caldav /calendars/__uids__/abc123/calendar Мой календарь`

### Список календарей
`/calendars`
Показывает ID, имя, тип, URL и часовой пояс для каждого календаря.

### Удалить календарь
`/calendars del <id>`
Удаляет календарь по ID.

### Редактировать календарь
`/calendars edit <id> <field> <value>`
Доступные поля: `name`, `url`, `client_type`, `timezone`.

**Примеры:**
- `/calendars edit abc123 name Мой календарь`
- `/calendars edit abc123 timezone GMT+3`

### Создать событие
`/calendars event <id> <summary> [| start [| end]]`
- Если start не указан — событие на весь сегодняшний день (all_day=true)
- Параметры разделяются `|`
- Формат даты: ISO (например `2026-07-28T12:00:00+03:00`)

**Примеры:**
- `/calendars event abc123 Встреча в 15:00` — событие на сегодня
- `/calendars event abc123 Планёрка | 2026-07-28T10:00:00+03:00`
- `/calendars event abc123 Конференция | 2026-07-28T10:00:00+03:00 | 2026-07-28T12:00:00+03:00`

## API Endpoints (ICS сервис, доступен боту)

### POST /calendars — регистрация календаря
```json
{
  "chat_id": "12345",
  "chat_type": "tg",
  "client_type": "caldav",
  "url": "/calendars/__uids__/abc123/calendar"
}
```
Заголовок: `X-Auth-Token: <api_key>`

### GET /calendars — список календарей пользователя
Параметры запроса: `api_key=<key>&user_id=<chat_id>`
Ответ:
```json
{
  "calendars": [
    {
      "id": "55c988ffaa7f4ae7b0bcc8dc2f0c6486",
      "name": null,
      "client_type": "caldav",
      "url": "...",
      "timezone": "GMT+3",
      "chat_id": "208207344",
      "chat_type": "tg",
      "user_id": "208207344",
      "last_sync_at": null
    }
  ]
}
```

### DELETE /calendars/{id} — удаление календаря
Параметры запроса: `api_key=<key>&user_id=<chat_id>`

### PUT /calendars/{id} — редактирование календаря
Параметры запроса: `api_key=<key>&user_id=<chat_id>`
```json
{
  "name": "Новое имя",
  "url": "новый url",
  "client_type": "caldav",
  "timezone": "GMT+3"
}
```
Все поля опциональны — можно обновить только часть.

### POST /calendars/{id}/events — создание события
Параметры запроса: `api_key=<key>&user_id=<chat_id>`
```json
{
  "summary": "Встреча",
  "description": "",
  "location": "",
  "start": "2026-07-28T12:00:00+03:00",
  "end": "2026-07-28T14:00:00+03:00",
  "all_day": false
}
```
- `summary` — обязательное поле
- `start` — если не указан, событие на сегодня (all_day=true)
- `end` — опционально
- `all_day` — если true, `start` и `end` игнорируются

## Авторизация
- POST: заголовок `X-Auth-Token`
- GET/DELETE/PUT: query-параметр `api_key`