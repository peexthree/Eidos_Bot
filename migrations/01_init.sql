-- 01_init.sql
-- INITIAL SCHEMA & PERFORMANCE INDEXES
-- Designed for manual execution via Render deployment script or Supabase Dashboard.

-- =================================================================================
-- TABLES
-- =================================================================================

CREATE TABLE IF NOT EXISTS players (
    uid BIGINT PRIMARY KEY,
    username VARCHAR(100),
    first_name VARCHAR(100),
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    biocoin INTEGER DEFAULT 0,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    streak INTEGER DEFAULT 1,
    last_raid_date DATE DEFAULT CURRENT_DATE,
    max_depth INTEGER DEFAULT 0,
    raid_count_today INTEGER DEFAULT 0,
    inventory_cache TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    referrer BIGINT,
    path VARCHAR(20) DEFAULT 'general',
    notified BOOLEAN DEFAULT FALSE,
    last_protocol_time BIGINT DEFAULT 0,
    total_coins_earned INTEGER DEFAULT 0,
    encrypted_cache_unlock_time BIGINT DEFAULT 0,
    encrypted_cache_type VARCHAR(50),
    shadow_broker_expiry BIGINT DEFAULT 0,
    anomaly_buff_expiry BIGINT DEFAULT 0,
    anomaly_buff_type VARCHAR(50),
    quiz_history TEXT DEFAULT '',
    proxy_expiry BIGINT DEFAULT 0,
    bunker_expiry BIGINT DEFAULT 0,
    onboarding_stage INTEGER DEFAULT 0,
    onboarding_start_time BIGINT DEFAULT 0,
    is_quarantined BOOLEAN DEFAULT FALSE,
    quarantine_end_time BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_equipment (
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    slot VARCHAR(50) NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    durability INTEGER DEFAULT 100,
    custom_data TEXT,
    PRIMARY KEY (uid, slot)
);

CREATE TABLE IF NOT EXISTS user_knowledge (
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    category VARCHAR(50),
    unlocked_keys TEXT DEFAULT '',
    PRIMARY KEY (uid, category)
);

CREATE TABLE IF NOT EXISTS unlocked_protocols (
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    protocol_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (uid, protocol_id)
);

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    item_id VARCHAR(50),
    quantity INTEGER DEFAULT 1,
    durability INTEGER DEFAULT 100,
    aquired_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raid_sessions (
    uid BIGINT PRIMARY KEY REFERENCES players(uid) ON DELETE CASCADE,
    depth INTEGER DEFAULT 0,
    hp INTEGER DEFAULT 100,
    signal INTEGER DEFAULT 100,
    buffer_items TEXT DEFAULT '',
    buffer_xp INTEGER DEFAULT 0,
    buffer_coins INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    last_event VARCHAR(50),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consecutive_empty_rooms INTEGER DEFAULT 0,
    riddle_answer VARCHAR(255),
    combat_data TEXT,
    glitch_id VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS bot_states (
    uid BIGINT PRIMARY KEY REFERENCES players(uid) ON DELETE CASCADE,
    state VARCHAR(50),
    data TEXT
);

CREATE TABLE IF NOT EXISTS achievements (
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    achievement_id VARCHAR(50) NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid, achievement_id)
);

CREATE TABLE IF NOT EXISTS diary (
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    entry_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS history (
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    archived_data_json TEXT,
    reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_shadow_metrics (
    uid BIGINT PRIMARY KEY REFERENCES players(uid) ON DELETE CASCADE,
    raids_started INTEGER DEFAULT 0,
    raids_completed INTEGER DEFAULT 0,
    raids_died INTEGER DEFAULT 0,
    monsters_killed INTEGER DEFAULT 0,
    bosses_killed INTEGER DEFAULT 0,
    chests_opened INTEGER DEFAULT 0,
    traps_triggered INTEGER DEFAULT 0,
    anomalies_encountered INTEGER DEFAULT 0,
    items_crafted INTEGER DEFAULT 0,
    pvp_attacks INTEGER DEFAULT 0,
    pvp_defenses INTEGER DEFAULT 0,
    biocoins_spent INTEGER DEFAULT 0,
    items_bought INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    escapes_at_full_hp INTEGER DEFAULT 0,
    consecutive_deaths INTEGER DEFAULT 0,
    death_depth_avg REAL DEFAULT 0,
    glitch_activations INTEGER DEFAULT 0,
    last_hard_glitch_time BIGINT DEFAULT 0,
    dossier_requests INTEGER DEFAULT 0,
    last_dossier_time BIGINT DEFAULT 0,
    forecast_requests INTEGER DEFAULT 0,
    last_forecast_time BIGINT DEFAULT 0,
    total_coins_earned INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS raid_graves (
    id SERIAL PRIMARY KEY,
    depth INTEGER NOT NULL,
    loot_json TEXT,
    owner_name VARCHAR(100),
    message TEXT,
    created_at BIGINT
);

CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    uid BIGINT REFERENCES players(uid) ON DELETE CASCADE,
    action VARCHAR(50),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS villains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    stats_json TEXT NOT NULL,
    loot_json TEXT,
    lore TEXT,
    avatar_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT villains_name_key UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS content (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    path VARCHAR(20) DEFAULT 'general',
    level INTEGER DEFAULT 1,
    title VARCHAR(100),
    text TEXT NOT NULL,
    image_url VARCHAR(255),
    options_json TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pvp_logs (
    id SERIAL PRIMARY KEY,
    attacker_uid BIGINT NOT NULL,
    target_uid BIGINT NOT NULL,
    stolen_coins INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT FALSE,
    is_revenged BOOLEAN DEFAULT FALSE,
    is_anonymous BOOLEAN DEFAULT FALSE,
    timestamp BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS global_stats (
    stat_name VARCHAR(50) PRIMARY KEY,
    stat_value BIGINT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================================
-- INDEXES (CONCURRENTLY where applicable to avoid table locks)
-- Note: CONCURRENTLY cannot be used within a transaction block if executing as a single script via some runners,
-- but the script should be run with autocommit=True.
-- =================================================================================

-- Standard indexes (can block if table is small, but players is big)
CREATE INDEX IF NOT EXISTS idx_inventory_uid ON inventory(uid);
CREATE INDEX IF NOT EXISTS idx_content_lookup ON content(type, path, level);

-- Optimization indexes from v2 requirements
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_players_worker ON players (is_active, notified, last_protocol_time);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_players_leaderboard ON players (xp DESC, level DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_players_depth ON players (max_depth DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_players_referrer ON players (referrer);
