# AVBot Project Knowledge

## Architecture
Telegram bot (python-telegram-bot) + FastAPI server for external integrations.

## Entry Point
`bot.py` — builds `Application`, registers handlers, starts background services via `app.post_init`.

## Key Files

### Handlers (in `handlers/`)
| File | Command/Trigger | Auth | Description |
|------|----------------|------|-------------|
| `start_handler.py` | `/start` | No | Sends welcome message |
| `topic_handler.py` | `/topic` | Yes | Topic management |
| `calendar_handler.py` | `/calendar <client_type> <url>` | Yes | Registers calendar via POST to ICS service |
| `calendars_handler.py` | `/calendars [del <id>]` `/calendars edit <id> <field> <value>` `/calendars event <id> <summary>` | Yes | List, delete, edit (name/url/client_type/timezone), or create events in calendars |
| `text_handler.py` | Any text (non-command) | Yes | GPT response |
| `document_handler.py` | Document upload | Yes | Document processing |
| `audio_handler.py` | Audio/voice | Yes | Speech processing |
| `callback_handler.py` | Callback queries | Yes | Inline button handling |

### Clients (in `clients/`)
| File | Description |
|------|-------------|
| `icsclient.py` | HTTP client for ICS/calendar service. POST `/calendars` for registration (`X-Auth-Token` header). GET `/calendars` to list, DELETE `/calendars/{id}` to delete (`api_key` query param). PUT `/calendars/{id}` to update fields (name/url/client_type/timezone). POST `/calendars/{id}/events` to create events. |

### Services (in `services/`)
| File | Description |
|------|-------------|
| `config_service.py` | YAML config loader, `Config.get(group, key, default)` |
| `api_server.py` | FastAPI server wrapping Telegram bot. Endpoints: `/send`, `/sendPhoto`, `/sendDocument`, `/sendAction`, `/forwardMessage`, `/calendar/event`, `/health`. Auth via `x-api-key` header |
| `yandexgpt_service.py` | YandexGPT integration |
| `dialog_service.py` | Dialog history management |
| `yandex_index_service.py` | Yandex search index |
| `auth.py` | Auth check (whitelist-based) |

### Config (`config/config.yml.template`)
```yaml
bot:
  token:
  whitelist: []
  welcome:

yandex:
  system_prompt:
  speech_api_key:
  model:
  index:
  bot_index:
  key:

ycloud:
  api_key:
  folder_id:

s3:
  access_key:
  secret_key:
  bucket_name:

mcp:
  b2b_inn_check_url:

api:
  api_key:
  port: 5200

data:
  ics:
    api_key:
    url: http://...
    pulling_interval: 10
    system_prompt:
  flights:
    url: http://...
    pulling_interval: 20
```

**NOTE:** Config keys are accessed at root level (e.g. `config.get('ics', 'api_key')`), but the template nests them under `data.ics`. At runtime the config must flatten these or the code won't find them.

## Background Services (started in `bot.py:start_background_services`)
1. **API Server** — FastAPI on configurable port, auth via `x-api-key` header

## Calendar Registration Flow
1. User sends: `/calendars add caldav https://user@yandex.ru:пароль@caldav.yandex.ru/calendars/login/events-123/`
2. `calendars_handler.py` extracts `client_type` and `url` from args, fills `chat_id` (from Telegram update) and `chat_type` ("tg")
3. POSTs to `{ics.url}/calendars` with `X-Auth-Token` header and JSON body `{chat_id, chat_type, client_type, url}`
4. Returns success/failure message to user

## Calendar List/Delete Flow
1. User sends `/calendars` — `calendars_handler.py` calls GET `{ics.url}/calendars?api_key=...&user_id=...`, returns list of calendars with id, name, type, url, timezone
2. User sends `/calendars del <id>` — calls DELETE `{ics.url}/calendars/{id}?api_key=...&user_id=...`, returns success/failure

## Calendar Edit/Event Flows
1. Edit: `/calendars edit <id> <field> <value>` — PUT `{ics.url}/calendars/{id}?api_key=...&user_id=...` с телом `{field: value}`. Поля: name, url, client_type, timezone.
2. Event: `/calendars event <id> <summary> [| start [| end]]` — POST `{ics.url}/calendars/{id}/events?api_key=...&user_id=...`. Если start не указан — all_day=true на сегодня.

## Calendar Event Endpoint (`POST /calendar/event`)
External services send calendar events to `/calendar/event`. Endpoint accepts `CalendarEventRequest` with `chat_id`, feeds event data + `ics.system_prompt` to YandexGPT via `asyncio.to_thread`, sends result to Telegram `chat_id`.

**Calendar event payload example:**
```json
{
  "chat_id": 12345,
  "summary": "Поработать",
  "description": "",
  "start": "2026-07-28T12:00:00+03:00",
  "end": "2026-07-28T14:00:00+03:00",
  "all_day": true,
  "calendar_id": "...",
  "calendar_url": "...",
  "calendar_name": ""
}
```

## Event Model (plain dicts)
```python
{
    "uid": str,
    "title": str,
    "start_datetime": str,  # ISO format
    "end_datetime": str,    # optional
    "description": str      # optional
}
```

## Testing
Tests in `tests/` directory. Run with: (check test framework in project)
- `test_ics_client.py` — ICSClient register_calendar tests
- `test_bot_handlers.py` — Integration handler tests

## Misc
- Config path: `CONFIG_PATH` env var or `./config/config.yml`
- Dialogs storage: `DIALOGS_PATH` env var or default in `storage/`
- API server auth header: `x-api-key`
- ICS service auth header: `X-Auth-Token` (POST), query param `api_key` (GET/DELETE)
- Calendar skill file: `skills/calendar.md` — справка по командам календаря для LLM и для команды `/calendars help`
- Help text для `/calendars` читается из `skills/calendar.md` через `Path(__file__).resolve()` (корректно в Docker)