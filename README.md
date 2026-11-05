# Eidos RPG (Android)

A cyberpunk RPG adventure set in the virtual world of Eidos, rewritten as a native Android application using Kotlin and Jetpack Compose.

## Features
- **Neural Link (Hub)**: Navigate the core modules of Eidos.
- **Cache Management (Inventory)**: View and equip your cybernetic enhancements.
- **Zero Layer Raids**: Dive into the depths of the digital world, face villains, and collect loot.
- **Biome Scaling**: Experience increasing difficulty and rewards as you go deeper.
- **Forge & Crafting**: Chip matrix synergies, PoE-style affix crafting, 3-to-1 synthesis.
- **PvP & Leaderboard**: Supabase-backed operator ratings and phantom rivals.
- **Adaptive Design**: Optimized for mobile with a high-contrast cyberpunk aesthetic.

## Tech Stack
- **Language**: Kotlin 2.0
- **UI Framework**: Jetpack Compose (Material 3)
- **Database**: Room (SQLite)
- **Backend**: Supabase (Auth + PostgREST RPC + Edge Functions)
- **Billing**: Google Play Billing
- **Image Loading**: Coil (with SVG support)
- **Serialization**: Kotlinx Serialization

## Backend setup
- `data/supabase_hardening_v2.sql` - the single authoritative DB script
  (tables, indexes, RLS policies, economy guard trigger, RPCs, rate limiter).
  Paste the whole file into Supabase Dashboard -> SQL Editor. Idempotent.
- `supabase/functions/verify-purchase/` - server-side Google Play purchase
  verification (see `supabase/functions/README.md` for deployment).
- Secrets live in `local.properties` (gitignored): `SUPABASE_URL`,
  `SUPABASE_ANON_KEY`, optionally `GEMINI_API_KEY` (debug builds only).

## Building
```bash
./gradlew assembleDebug        # debug build
./gradlew testDebugUnitTest    # unit tests
```
For a signed release build create `keystore.properties` from
`keystore.properties.example`. CI runs compile + unit tests on push/PR
(`.github/workflows/android-ci.yml`).

## Development
This project was rewritten from a Telegram Bot + TWA frontend to a standalone
Android application. Game content lives in `app/src/main/assets/`
(source of truth; legacy Telegram-era copies in `data/legacy/`).
Post-audit status and the remaining backlog: `docs/AUDIT_2026-11-05.md`.
