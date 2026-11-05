# data/

SQL и вспомогательные данные Supabase-бэкенда.

## Активные файлы

- **supabase_hardening_v2.sql** - ЕДИНСТВЕННЫЙ актуальный скрипт БД. Самодостаточный
  (таблицы, каталог цен, индексы, RLS, триггер экономики, все RPC, rate-limiter).
  Вставляется целиком в Supabase Dashboard -> SQL Editor. Идемпотентный.
  В шапке есть закомментированный блок DROP для полного dev-сброса.
- supabase_migrations.sql, supabase_security_patch_2026.sql - УСТАРЕВШИЕ,
  помечены DEPRECATED. Хранятся как история миграций; повторный запуск вернёт
  уязвимые политики. Если запускались - hardening_v2 всегда запускается последним.

## legacy/

content.json и villains.json - старые версии игрового контента эпохи
Telegram-бота (Telegram file_id в image, устаревшие описания).

**Источник истины для контента - app/src/main/assets/** (content.json,
villains.json). Код читает контент только оттуда (`context.assets.open(...)`).
Файлы в legacy/ НЕ редактировать и в приложение не возвращать.

## Пайплайн артов

eidos_items_bulk_create.csv (в корне репо) - датасет промптов для массовой
генерации карточек предметов в Canva Pro. К сборке APK отношения не имеет.
