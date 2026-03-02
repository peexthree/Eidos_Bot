# Database Performance Optimization Log - 2026-03-02

## Issues Addressed
1. **Raid Sessions Contention**: `UPDATE` and `DELETE` on `raid_sessions` were extremely slow (mean 3s) due to row-level lock contention and high-frequency updates within single transactions.
2. **Slow Startup**: `init_db` performed exhaustive per-table queries to `information_schema`, causing slow bot initialization.
3. **Redundant Indexes**: Over-indexing on `uid` columns in `players` and `raid_sessions`.
4. **Inefficient Queries**: Sequential scans on `players` for background notification tasks.

## Optimizations Applied

### 1. Database Indexing
- **Dropped redundant indexes**:
  - `idx_players_uid` (UID is already PK)
  - `idx_raid_sessions_uid` (UID is already PK)
  - `idx_raid_sessions_enemy` (Duplicate of `idx_raid_sessions_current_enemy_id`)
- **Added composite index**:
  - `idx_players_notification_query` on `(is_active, notified, last_protocol_time)` to optimize background worker queries.

### 2. Startup Optimization (`database.py`)
- Refactored `init_db` to fetch all column data for all tables in a **single query** to `information_schema.columns`.
- Modified `ensure_table_schema` to use pre-fetched column data, eliminating 20+ sequential metadata queries per startup.

### 3. Application Logic Batching
- **`modules/services/raid.py`**: Refactored `process_raid_step` to consolidate multiple `UPDATE raid_sessions` calls. Passive item effects and glitch mechanics now use a deferred update pattern, applying all state changes in a single query per section.
- **`modules/services/combat.py`**: Implemented deferred updates for signal and enemy HP in `process_combat_action`. State is synchronized once before returning, reducing the duration of row locks on the active raid session.

## Verification Results
- **Syntax**: Verified via `verify_syntax.py`.
- **Logic**: All relevant unit tests passed (`test_pvp_service.py`, `test_raid_cost.py`, `test_raid_loot.py`).
- **Telemetry Expected Impact**: Significant reduction in `mean_time` for `raid_sessions` updates and faster container startup on Render.
