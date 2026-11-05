# Supabase Edge Function: verify-purchase

Серверная верификация покупок Google Play. Функция проверяет покупку через Google Play Developer API
и записывает её в серверный ledger через RPC `verify_and_record_purchase` (таблица `app_purchases`).

## Как это работает

1. Клиент после успешной покупки (fire-and-forget) отправляет POST на
   `{SUPABASE_URL}/functions/v1/verify-purchase` с телом `{ purchaseToken, productId, orderId }`
   и заголовком `Authorization: Bearer <пользовательский JWT>`.
2. Функция проверяет JWT пользователя через Supabase Auth (иначе 401).
3. Функция получает access token Google service account (RS256 JWT, подписанный через crypto.subtle,
   scope `https://www.googleapis.com/auth/androidpublisher`) и вызывает
   Google Play Developer API (`purchases.products.get`).
4. Проверяется `purchaseState === 0` (purchased); `acknowledgementState` допускается 0 или 1.
5. Сумма биомонет берётся ТОЛЬКО из серверного каталога `PRODUCT_CATALOG` внутри `index.ts`
   (никогда из тела запроса). Неизвестный `productId` - 400.
6. Токен покупки хешируется (SHA-256) и запись уходит в RPC `verify_and_record_purchase`
   от имени `service_role` с явным `p_player_id` (под service_role `auth.uid()` равен NULL,
   поэтому RPC требует явную цель и сам проверяет её существование).
   RPC сам защищён от повторной записи по уникальному `token_hash`.
7. Ответ: `{ success: true, biocoins_granted }` либо `{ success: false, error }`.

Требуемая версия схемы: `data/supabase_hardening_v2.sql` с RPC
`verify_and_record_purchase` в 5-аргументной сигнатуре (с `p_player_id TEXT DEFAULT NULL`).
Если файл применялся до появления этого параметра - просто выполни обновлённый
файл ещё раз (он идемпотентный, старая 4-аргументная версия удаляется через DROP FUNCTION).

## Шаг 1. Service Account в Google Cloud Console

1. Открой [Google Cloud Console](https://console.cloud.google.com) и создай (или выбери) проект,
   привязанный к твоему приложению Google Play.
2. Включи **Google Play Android Developer API** (Android Publisher API):
   APIs & Services -> Library -> "Google Play Android Developer API" -> Enable.
3. Создай service account: IAM & Admin -> Service Accounts -> Create Service Account.
   Роль на этом шаге: **Service Account User**.
4. Создай для него ключ: Keys -> Add Key -> JSON. Скачается JSON-файл приватного ключа.
5. Открой [Google Play Console](https://play.google.com/console) -> Users and Permissions ->
   Invite new users -> укажи e-mail service account
   (`<id>@<project>.iam.gserviceaccount.com`) -> предоставь право
   **View financial data** (доступ к финансовым данным) и, при необходимости,
   право на управление заказами. Приглашение нужно принять.

## Шаг 2. Задать секреты Supabase

Из корня проекта (нужен установленный [Supabase CLI](https://supabase.com/docs/guides/cli) и выполненный `supabase login`):

```bash
supabase secrets set GOOGLE_SERVICE_ACCOUNT_JSON="$(cat /path/to/service-account.json)" ANDROID_PACKAGE_NAME=io.eidos.zerolayer
```

На Windows (PowerShell) удобно передать содержимое JSON как одну строку:

```powershell
supabase secrets set GOOGLE_SERVICE_ACCOUNT_JSON="$(Get-Content -Raw path\to\service-account.json)" ANDROID_PACKAGE_NAME=io.eidos.zerolayer
```

`GOOGLE_SERVICE_ACCOUNT_JSON` - это весь JSON service account одной строкой.
`ANDROID_PACKAGE_NAME` - applicationId приложения (сейчас `io.eidos.zerolayer`).

`SUPABASE_URL`, `SUPABASE_ANON_KEY` и `SUPABASE_SERVICE_ROLE_KEY` в runtime Edge Functions
присутствуют автоматически, задавать их не нужно.

## Шаг 3. Деплой

```bash
supabase functions deploy verify-purchase --project-ref XXXXXXXX
```

Где `XXXXXXXX` - project ref из Settings -> General в панели Supabase
(или `supabase link --project-ref XXXXXXXX` один раз, потом просто
`supabase functions deploy verify-purchase`).

Проверка (JWT можно взять из логина клиента, иначе функция вернёт 401):

```bash
curl -X POST "https://<project-ref>.supabase.co/functions/v1/verify-purchase" \
  -H "Authorization: Bearer <USER_JWT>" \
  -H "Content-Type: application/json" \
  -d '{"purchaseToken":"TOKEN","productId":"biocoins_small","orderId":"GPA.1234-5678-9012"}'
```

## Важно: PRODUCT_CATALOG должен совпадать с Play Console

Каталог продуктов в `supabase/functions/verify-purchase/index.ts`:

| productId         | biocoins |
|-------------------|----------|
| biocoins_small    | 1000     |
| biocoins_medium   | 5500     |
| biocoins_large    | 12000    |
| biocoins_mega     | 30000    |

Идентификаторы продуктов и суммы ОБЯЗАНЫ совпадать с in-app продуктами, созданными в
Google Play Console (Monetize -> Products -> In-app products). Если добавляешь новый пакет
монет - сначала создай его в Play Console, затем добавь в `PRODUCT_CATALOG` и передеплой
функцию. Покупка с неизвестным функции `productId` будет отклонена с ошибкой 400,
начисление по сумме из клиентского запроса невозможно по построению.

## Безопасность

- RPC `verify_and_record_purchase` доступен только `service_role` (EXECUTE у anon/authenticated отозван),
  вызов идёт из Edge Function с серверным ключом.
- Повторная отправка того же токена блокируется RPC по уникальному `token_hash` (защита от replay).
- Токены покупок в логах не светятся: клиент логирует только префикс хеша, сервер не логирует тело запроса.
- Мок-биллинг (токены `simulated_token...`) клиентом на сервер не отправляется.

---

# Supabase Edge Function: gemini-proxy

Серверный прокси к Gemini API. В release-сборках приложения ключ Gemini НЕ встроен в APK -
все вызовы идут через эту функцию, ключ хранится только в секретах Supabase.

## Как это работает

1. Клиент отправляет POST на `{SUPABASE_URL}/functions/v1/gemini-proxy` с телом
   `{ prompt, systemPrompt? }` и заголовком `Authorization: Bearer <пользовательский JWT>`
   (плюс `apikey`).
2. Функция валидирует JWT пользователя через Supabase Auth
   (`createClient(SUPABASE_URL, SUPABASE_ANON_KEY).auth.getUser(jwt)`), иначе 401.
3. Простая защита от злоупотреблений: in-memory счётчик на пользователя -
   максимум 20 запросов в минуту, превышение - 429 (счётчик локален для инстанса функции).
4. Секрет `GEMINI_API_KEY` берётся из `Deno.env`; если не задан - 503.
5. Запрос форвардится в `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
   с заголовком `x-goog-api-key` (ключ НИКОГДА не передаётся в query-параметре),
   тело `{ contents, systemInstruction }` - как в клиентском запросе.
6. Из ответа достаётся `candidates[0].content.parts[*].text` (все parts склеиваются) и
   возвращается `{ success: true, text }`. Ошибка Google - 502 с `{ success: false, error }`.
7. В логи не пишутся ни ключи, ни промпты - только коды статусов и общие сообщения.

## Деплой

```bash
supabase functions deploy gemini-proxy --project-ref XXXXXXXX
```

(или `supabase link --project-ref XXXXXXXX` один раз, потом просто
`supabase functions deploy gemini-proxy`.)

## Секреты

```bash
supabase secrets set GEMINI_API_KEY=AIza...
```

Ключ берётся из Google AI Studio. `SUPABASE_URL` и `SUPABASE_ANON_KEY` в runtime
Edge Functions присутствуют автоматически, задавать их не нужно.

Проверка (JWT можно взять из логина клиента, без него функция вернёт 401):

```bash
curl -X POST "https://<project-ref>.supabase.co/functions/v1/gemini-proxy" \
  -H "Authorization: Bearer <USER_JWT>" \
  -H "apikey: <SUPABASE_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Привет"}'
```

## Режимы клиента (GeminiService)

Цепочка фолбэков в `app/src/main/java/io/eidos/zerolayer/data/GeminiService.kt`:

1. **Debug-сборка со своим ключом**: если `BuildConfig.DEBUG` и `GEMINI_API_KEY`
   не пуст - прямой вызов Gemini API с локальным ключом (удобство разработки,
   ключ остаётся только в локальной debug-сборке).
2. **Release (и debug без ключа)**: вызов через Edge Function `gemini-proxy` -
   ключ Gemini только на сервере, аутентификация пользовательским JWT Supabase.
3. **Локальная симуляция**: если прокси недоступен (нет сессии, сетевая ошибка,
   не-200 ответ) - полностью автономная локальная генерация ответов ЕВА-09 без сети.

То есть: debug-сборки могут ходить напрямую со своим ключом, release - только через
прокси, и оба пути падают обратно в локальную симуляцию, так что приложение работает
и без ключей, и без сети.

