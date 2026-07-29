# Как подключить Яндекс.Календарь (CalDAV)

## 1. Создайте пароль приложения

1. Перейдите в [Яндекс ID → Пароли приложений](https://id.yandex.ru/security/app-passwords)
2. Найдите раздел **«Календарь» (CalDAV)** и нажмите **«+»** напротив него
3. Яндекс покажет пароль — **скопируйте его сразу**, он показывается только один раз

## 2. Получите URL календаря

1. Откройте [Яндекс.Календарь](https://calendar.yandex.ru)
2. В боковом меню наведите на календарь, который хотите подключить, нажмите ⋮ → **«Настройки»**
3. Перейдите на вкладку **«Экспорт»**
4. В разделе **CalDAV** скопируйте ссылку — она выглядит так:
   `https://caldav.yandex.ru/calendars/user%40yandex.ru/events-xxxx/`
5. Ссылку нужно привести к такому формату:
   `https://<email>:<пароль>@caldav.yandex.ru/calendars/<логин>/events-<id>/`

   Например:
   `https://user@yandex.ru:abc123def@caldav.yandex.ru/calendars/user%40yandex.ru/events-xxxx/`

Подробнее: [официальная инструкция по синхронизации](https://yandex.ru/support/yandex-360/business/calendar/ru/data-exchange/synchronization/sync-desktop) | [синхронизация на мобильных](https://yandex.ru/support/yandex-360/business/calendar/ru/data-exchange/synchronization/sync-mobile)

## 3. Подключите в боте

```
/calendars add caldav https://user@yandex.ru:пароль@caldav.yandex.ru/calendars/user%40yandex.ru/events-xxxx/ Название_календаря
```

Бот сохранит календарь и будет автоматически писать о ближайщих событиях в нём, а так же добавлять новые события в календарь. Пароль приложения даёт доступ только к календарю, используется только для подключения к CalDAV.

## Итоговые данные для подключения

| Параметр | Значение |
|----------|----------|
| Сервер CalDAV | `https://caldav.yandex.ru` |
| Логин | Ваш Яндекс.Логин (email) |
| Пароль | Пароль приложения (из шага 1) |
| URL календаря | Из шага 2 (`https://caldav.yandex.ru/calendars/.../events-.../`) |

**Важно:** URL календаря нужно копировать целиком — он уже включает ваш идентификатор.