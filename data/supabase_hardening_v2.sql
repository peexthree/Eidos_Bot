-- ==============================================================================
-- 🛡️ EIDOS: ZERO LAYER - SUPABASE HARDENING PATCH v2 (POST-AUDIT FIX)
-- ==============================================================================
-- SELF-CONTAINED: paste the WHOLE file into Supabase Dashboard -> SQL Editor
-- and run once. Works on a fresh project (creates tables, seed, indexes,
-- policies, RPCs) and on an existing database (idempotent, safe to re-run).
-- No other SQL file is required.
--
-- OPTIONAL FULL DEV RESET (game not in production): if you want to rebuild
-- from zero, run this block FIRST in the same SQL Editor window:
--   DROP TABLE IF EXISTS public.app_rpc_rate_limits CASCADE;
--   DROP TABLE IF EXISTS public.app_purchases CASCADE;
--   DROP TABLE IF EXISTS public.app_raid_logs CASCADE;
--   DROP TABLE IF EXISTS public.app_inventory CASCADE;
--   DROP TABLE IF EXISTS public.app_players CASCADE;
--   DROP TABLE IF EXISTS public.app_catalog_prices CASCADE;
-- (This wipes all player/inventory/log data - dev only!)
--
-- Fixes (audit 2026-11):
--   [C1] RLS UPDATE allowed owner to write arbitrary biocoins/exp/level/max_depth
--        -> economy guard trigger with per-update caps + rolling rate budget.
--   [C2] INSERT policy allowed role 'anon'/'authenticated' to create profiles
--        with arbitrary values -> strict owner match + INSERT value clamp.
--   [C3] sync_player_inventory skipped owner check under anon JWT
--        -> hard REQUIRE auth.uid() + strict owner match.
--   [C4] verify_and_record_purchase granted biocoins from client parameter
--        and was callable by any user -> reserved for service_role only
--        (must be called by an Edge Function after Google Play API verification).
--   [C5] process_raid_reward trusted client depth -> clamp to server
--        max_depth + 25, absolute cap, 10s cooldown.
--   [C6] resolve_pvp_match had no cooldown, deterministic NOW()-based defense
--        programs, allowed self-farming -> rate limit + random defense +
--        self-match block.
--   [I1] No CREATE TABLE for core tables in repo -> reproducible schema added.
--   [I2] No indexes -> leaderboard/inventory/lookup indexes added.
--
-- NOTE: cloud sync from an UNAUTHENTICATED client (Bearer anon key fallback)
-- is now intentionally rejected by RLS. The app treats sync failure as
-- non-fatal (offline mode). Normal authenticated flow (session.userId =
-- device_id = auth.uid()) is unaffected.
-- ==============================================================================

-- ==============================================================================
-- 0. CORE TABLES (reproducible schema for fresh projects)
-- Existing databases are unaffected (IF NOT EXISTS).
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.app_players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id TEXT NOT NULL,
    username TEXT NOT NULL,
    level INT DEFAULT 1,
    exp BIGINT DEFAULT 0,
    biocoins BIGINT DEFAULT 0,
    hp INT DEFAULT 100,
    energy INT DEFAULT 100,
    rank TEXT DEFAULT 'Оператор',
    max_depth INT DEFAULT 0,
    kills INT DEFAULT 0,
    defense_program_1 TEXT DEFAULT 'SHIELD',
    defense_program_2 TEXT DEFAULT 'BRUTEFORCE',
    defense_program_3 TEXT DEFAULT 'STEALTH',
    installed_hardware TEXT,
    pvp_proxy_until BIGINT DEFAULT 0,
    state_version BIGINT DEFAULT 1,
    updated_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
);

CREATE TABLE IF NOT EXISTS public.app_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES public.app_players(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    is_equipped BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS public.app_raid_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES public.app_players(id) ON DELETE CASCADE,
    log_text TEXT NOT NULL,
    log_type TEXT DEFAULT 'info',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Stats columns (audit compliance, both fresh and legacy databases)
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS raids_done INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS perfect_raids INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS wins_pvp INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS losses_pvp INT DEFAULT 0;

-- Economy guard bookkeeping (client never writes these: unknown to its DTO)
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS econ_window_start BIGINT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS econ_coin_budget BIGINT DEFAULT 60000;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS econ_exp_budget BIGINT DEFAULT 120000;

-- ==============================================================================
-- 0b. CATALOG PRICES + PURCHASES LEDGER (self-contained: fresh projects too)
-- ==============================================================================

-- Server-side price truth (client cannot buy at a forged price)
CREATE TABLE IF NOT EXISTS public.app_catalog_prices (
    item_id TEXT PRIMARY KEY,
    price BIGINT NOT NULL CHECK (price >= 0),
    created_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
);

ALTER TABLE public.app_catalog_prices ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public read catalog prices" ON public.app_catalog_prices;
CREATE POLICY "Public read catalog prices"
    ON public.app_catalog_prices
    FOR SELECT
    USING (true);

INSERT INTO public.app_catalog_prices (item_id, price) VALUES
    ('scavenger_mask', 250),
    ('nomad_goggles', 450),
    ('aegis', 1200),
    ('shock_baton', 150),
    ('plasma_blade', 500),
    ('pulse_rifle', 800),
    ('nano_vest', 350),
    ('exoskeleton', 1100),
    ('combat_helmet', 300),
    ('cyber_visor', 600),
    ('medkit', 100),
    ('repair_kit', 150),
    ('energy_cell', 80),
    ('data_chip_alpha', 300),
    ('data_chip_beta', 650),
    ('data_chip_gamma', 1200),
    ('reality_silencer', 2500),
    ('karma_inversion', 3000),
    ('death_mask', 5000)
ON CONFLICT (item_id) DO UPDATE SET price = EXCLUDED.price;

-- Purchase token ledger (filled ONLY by service_role via Edge Function,
-- see section 9; direct client INSERT is blocked by RLS)
CREATE TABLE IF NOT EXISTS public.app_purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id TEXT NOT NULL,
    order_id TEXT,
    token_hash TEXT NOT NULL UNIQUE,
    product_id TEXT NOT NULL,
    biocoins_granted BIGINT DEFAULT 0,
    created_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
);

ALTER TABLE public.app_purchases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Players can view their own purchases" ON public.app_purchases;
CREATE POLICY "Players can view their own purchases"
    ON public.app_purchases
    FOR SELECT
    USING ((auth.uid())::text = (player_id)::text);

-- ==============================================================================
-- 1. INDEXES (leaderboard, inventory lookups, log pruning)
-- ==============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_app_players_device_id ON public.app_players(device_id);
CREATE INDEX IF NOT EXISTS idx_app_players_leaderboard ON public.app_players(max_depth DESC, level DESC, exp DESC);
CREATE INDEX IF NOT EXISTS idx_app_inventory_player ON public.app_inventory(player_id);
CREATE INDEX IF NOT EXISTS idx_app_inventory_player_item ON public.app_inventory(player_id, item_id);
CREATE INDEX IF NOT EXISTS idx_app_raid_logs_player ON public.app_raid_logs(player_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_app_purchases_player ON public.app_purchases(player_id);

-- ==============================================================================
-- 2. TRUSTED SERVER CONTEXT
-- SECURITY DEFINER RPCs mark their own writes as trusted so the economy guard
-- applies only to direct client writes. Client JWT requests can never set this
-- custom GUC (customized options require superuser to SET when absent from
-- config, and PostgREST runs as non-superuser postgres role 'authenticated').
-- ==============================================================================

CREATE OR REPLACE FUNCTION public.eidos_is_trusted()
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN COALESCE(current_setting('eidos.server_ctx', true), '') = 'trusted';
END;
$$;

-- ==============================================================================
-- 3. ECONOMY GUARD TRIGGER (app_players)
-- Blocks: economy inflation via direct PATCH, device_id hijack, absurd jumps.
-- ==============================================================================

CREATE OR REPLACE FUNCTION public.enforce_economy_limits()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_now BIGINT := (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000);
    v_window_ms CONSTANT BIGINT := 60000;      -- rolling budget window
    v_max_coin_gain CONSTANT BIGINT := 25000;  -- per single client update
    v_max_exp_gain  CONSTANT BIGINT := 50000;
    v_window_coins  CONSTANT BIGINT := 60000;  -- per minute
    v_window_exp    CONSTANT BIGINT := 120000;
    v_coin_gain BIGINT;
    v_exp_gain  BIGINT;
BEGIN
    IF public.eidos_is_trusted() THEN
        NEW.updated_at := v_now;
        RETURN NEW;
    END IF;

    IF TG_OP = 'INSERT' THEN
        -- [C2] New profiles cannot start with inflated values (leaderboard poisoning).
        -- A returning player on a fresh account recovers over 1-2 syncs (gains allowed).
        NEW.biocoins := LEAST(COALESCE(NEW.biocoins, 0), 25000);
        NEW.exp      := LEAST(COALESCE(NEW.exp, 0), 50000);
        NEW.level    := LEAST(COALESCE(NEW.level, 1), 10);
        NEW.max_depth := LEAST(COALESCE(NEW.max_depth, 0), 25);
        NEW.kills    := LEAST(COALESCE(NEW.kills, 0), 200);
        NEW.econ_window_start := v_now;
        NEW.econ_coin_budget  := v_window_coins;
        NEW.econ_exp_budget   := v_window_exp;
        NEW.updated_at := v_now;
        RETURN NEW;
    END IF;

    -- Identity stability: device_id is the upsert conflict key
    IF NEW.device_id IS DISTINCT FROM OLD.device_id THEN
        RAISE EXCEPTION 'Forbidden: device_id cannot be changed';
    END IF;

    v_coin_gain := COALESCE(NEW.biocoins, 0) - COALESCE(OLD.biocoins, 0);
    v_exp_gain  := COALESCE(NEW.exp, 0) - COALESCE(OLD.exp, 0);

    -- [C1] Decreases are always allowed (purchases, penalties); gains are capped.
    IF v_coin_gain > 0 OR v_exp_gain > 0 THEN
        IF v_now - COALESCE(OLD.econ_window_start, 0) >= v_window_ms THEN
            NEW.econ_window_start := v_now;
            NEW.econ_coin_budget := v_window_coins;
            NEW.econ_exp_budget  := v_window_exp;
        ELSE
            NEW.econ_coin_budget := COALESCE(OLD.econ_coin_budget, v_window_coins);
            NEW.econ_exp_budget  := COALESCE(OLD.econ_exp_budget, v_window_exp);
        END IF;

        IF v_coin_gain > v_max_coin_gain THEN
            RAISE EXCEPTION 'Economy guard: biocoins gain % exceeds per-update limit %', v_coin_gain, v_max_coin_gain;
        END IF;
        IF v_exp_gain > v_max_exp_gain THEN
            RAISE EXCEPTION 'Economy guard: exp gain % exceeds per-update limit %', v_exp_gain, v_max_exp_gain;
        END IF;
        IF v_coin_gain > NEW.econ_coin_budget THEN
            RAISE EXCEPTION 'Economy guard: biocoins rate budget exhausted (%)', NEW.econ_coin_budget;
        END IF;
        IF v_exp_gain > NEW.econ_exp_budget THEN
            RAISE EXCEPTION 'Economy guard: exp rate budget exhausted (%)', NEW.econ_exp_budget;
        END IF;

        NEW.econ_coin_budget := NEW.econ_coin_budget - GREATEST(v_coin_gain, 0);
        NEW.econ_exp_budget  := NEW.econ_exp_budget - GREATEST(v_exp_gain, 0);
    END IF;

    IF COALESCE(NEW.level, 1) > COALESCE(OLD.level, 1) + 5 THEN
        RAISE EXCEPTION 'Economy guard: level jump % -> % rejected', OLD.level, NEW.level;
    END IF;
    IF COALESCE(NEW.max_depth, 0) > COALESCE(OLD.max_depth, 0) + 50 THEN
        RAISE EXCEPTION 'Economy guard: max_depth jump % -> % rejected', OLD.max_depth, NEW.max_depth;
    END IF;
    IF COALESCE(NEW.kills, 0) > COALESCE(OLD.kills, 0) + 500 THEN
        RAISE EXCEPTION 'Economy guard: kills jump % -> % rejected', OLD.kills, NEW.kills;
    END IF;

    NEW.updated_at := v_now;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_economy_limits ON public.app_players;
CREATE TRIGGER trg_economy_limits
    BEFORE INSERT OR UPDATE ON public.app_players
    FOR EACH ROW EXECUTE FUNCTION public.enforce_economy_limits();

-- ==============================================================================
-- 4. RPC RATE LIMITER (atomic)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.app_rpc_rate_limits (
    player_key TEXT NOT NULL,
    action TEXT NOT NULL,
    last_call BIGINT NOT NULL,
    PRIMARY KEY (player_key, action)
);

REVOKE ALL ON public.app_rpc_rate_limits FROM anon, authenticated;

CREATE OR REPLACE FUNCTION public.assert_rpc_rate_limit(
    p_action TEXT,
    p_min_interval_ms BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user TEXT := (auth.uid())::text;
    v_now BIGINT := (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000);
BEGIN
    IF v_user IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    INSERT INTO public.app_rpc_rate_limits AS r (player_key, action, last_call)
    VALUES (v_user, p_action, v_now)
    ON CONFLICT (player_key, action) DO UPDATE
        SET last_call = EXCLUDED.last_call
        WHERE r.last_call IS NULL OR v_now - r.last_call >= p_min_interval_ms;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Rate limit: action % requires % ms between calls', p_action, p_min_interval_ms;
    END IF;
    RETURN true;
END;
$$;

-- ==============================================================================
-- 5. RLS POLICIES (hardened, drop legacy first)
-- ==============================================================================

ALTER TABLE IF EXISTS public.app_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_raid_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public access" ON public.app_players;
DROP POLICY IF EXISTS "Players can read and update their own profile" ON public.app_players;
DROP POLICY IF EXISTS "Anyone can view player profiles" ON public.app_players;
DROP POLICY IF EXISTS "Players can update their own profile" ON public.app_players;
DROP POLICY IF EXISTS "Players can insert their own profile" ON public.app_players;
DROP POLICY IF EXISTS "Players can delete their own profile" ON public.app_players;

DROP POLICY IF EXISTS "Public access" ON public.app_inventory;
DROP POLICY IF EXISTS "Allow public update app_inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can update their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can insert their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can delete their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can select their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can read and manage their own inventory" ON public.app_inventory;

DROP POLICY IF EXISTS "Public access" ON public.app_raid_logs;
DROP POLICY IF EXISTS "Players can manage their own raid logs" ON public.app_raid_logs;

-- A) app_players
-- SELECT stays public by design: leaderboard + PvP rival generation.
-- Public exposure of full rows is a documented trade-off; restrict to a
-- narrow view later if profile fields become sensitive.
CREATE POLICY "Anyone can view player profiles"
    ON public.app_players
    FOR SELECT
    USING (true);

-- Public full-row SELECT is a deliberate trade-off:
-- it is required by the leaderboard and PvP rival generation.
-- Client-side leaderboard queries use an explicit column projection
-- (not select=*) via PostgREST, so they pull only the public fields
-- (id, device_id, username, level, exp, biocoins, max_depth, rank,
-- kills, state_version); PvP phantom fetch projects profile fields
-- plus defense_program_1..3 and installed_hardware for battle simulation.
-- If sensitive columns are ever added to app_players, migrate reads
-- to a narrow view instead of widening this policy.

-- INSERT: [C2] strict owner match, no anon/authenticated bypass.
CREATE POLICY "Players can insert their own profile"
    ON public.app_players
    FOR INSERT
    WITH CHECK (
        (auth.uid())::text = (device_id)::text
        OR (auth.uid())::text = (id)::text
    );

-- UPDATE: [C1] strict owner match + economy guard trigger (section 3).
CREATE POLICY "Players can update their own profile"
    ON public.app_players
    FOR UPDATE
    USING ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text)
    WITH CHECK ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text);

CREATE POLICY "Players can delete their own profile"
    ON public.app_players
    FOR DELETE
    USING ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text);

-- B) app_inventory: owner-only
CREATE POLICY "Players can read and manage their own inventory"
    ON public.app_inventory
    FOR ALL
    USING (
        (auth.uid())::text = (player_id)::text
        OR (player_id)::text IN (
            SELECT (id)::text FROM public.app_players
            WHERE (id)::text = (auth.uid())::text OR (device_id)::text = (auth.uid())::text
        )
    )
    WITH CHECK (
        (auth.uid())::text = (player_id)::text
        OR (player_id)::text IN (
            SELECT (id)::text FROM public.app_players
            WHERE (id)::text = (auth.uid())::text OR (device_id)::text = (auth.uid())::text
        )
    );

-- C) app_raid_logs: owner-only
CREATE POLICY "Players can manage their own raid logs"
    ON public.app_raid_logs
    FOR ALL
    USING (
        (auth.uid())::text = (player_id)::text
        OR (player_id)::text IN (
            SELECT (id)::text FROM public.app_players
            WHERE (id)::text = (auth.uid())::text OR (device_id)::text = (auth.uid())::text
        )
    )
    WITH CHECK (
        (auth.uid())::text = (player_id)::text
        OR (player_id)::text IN (
            SELECT (id)::text FROM public.app_players
            WHERE (id)::text = (auth.uid())::text OR (device_id)::text = (auth.uid())::text
        )
    );

-- ==============================================================================
-- 6. RPC: process_raid_reward (hardened)
-- [C5] depth clamped against SERVER-side max_depth; cooldown 10s.
-- ==============================================================================

CREATE OR REPLACE FUNCTION public.process_raid_reward(
    p_exp BIGINT,
    p_biocoins BIGINT,
    p_depth INT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user_id TEXT;
    v_player RECORD;
    v_server_depth INT;
    v_effective_depth INT;
    v_max_allowed_coins BIGINT;
    v_max_allowed_exp BIGINT;
    v_new_exp BIGINT;
    v_new_coins BIGINT;
    v_new_depth INT;
BEGIN
    PERFORM public.assert_rpc_rate_limit('raid_reward', 10000);
    SET LOCAL eidos.server_ctx = 'trusted';

    v_user_id := (auth.uid())::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    IF p_depth < 0 OR p_biocoins < 0 OR p_exp < 0 THEN
        RAISE EXCEPTION 'Invalid parameters: Bounds check failed (depth %, coins %, exp %)', p_depth, p_biocoins, p_exp;
    END IF;

    SELECT * INTO v_player FROM public.app_players
    WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Player profile not found for user %', v_user_id;
    END IF;

    -- [C5] Clamp depth against server-known progress, not the client claim.
    v_server_depth := COALESCE(v_player.max_depth, 0);
    v_effective_depth := LEAST(GREATEST(p_depth, 0), v_server_depth + 25, 10000);

    v_max_allowed_coins := (v_effective_depth * 50 + 1000);
    v_max_allowed_exp := (v_effective_depth * 30 + 500);

    IF p_biocoins > v_max_allowed_coins THEN
        RAISE EXCEPTION 'Reward exceeds allowed BioCoins limit for depth %: % > %', v_effective_depth, p_biocoins, v_max_allowed_coins;
    END IF;

    IF p_exp > v_max_allowed_exp THEN
        RAISE EXCEPTION 'Reward exceeds allowed EXP limit for depth %: % > %', v_effective_depth, p_exp, v_max_allowed_exp;
    END IF;

    v_new_exp := COALESCE(v_player.exp, 0) + p_exp;
    v_new_coins := COALESCE(v_player.biocoins, 0) + p_biocoins;
    v_new_depth := GREATEST(COALESCE(v_player.max_depth, 0), v_effective_depth);

    UPDATE public.app_players
    SET
        exp = v_new_exp,
        biocoins = v_new_coins,
        max_depth = v_new_depth,
        updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
    WHERE id = v_player.id;

    RETURN jsonb_build_object(
        'success', true,
        'exp', v_new_exp,
        'biocoins', v_new_coins,
        'max_depth', v_new_depth
    );
END;
$$;

-- ==============================================================================
-- 7. RPC: black_market_purchase (server-side price truth kept; rate limited)
-- ==============================================================================

CREATE OR REPLACE FUNCTION public.black_market_purchase(
    p_item_id TEXT,
    p_cost BIGINT,
    p_quantity INT DEFAULT 1
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user_id TEXT;
    v_player RECORD;
    v_server_cost BIGINT;
    v_total_cost BIGINT;
    v_new_coins BIGINT;
    v_existing_item RECORD;
    v_is_uuid BOOLEAN := false;
BEGIN
    PERFORM public.assert_rpc_rate_limit('black_market', 500);
    SET LOCAL eidos.server_ctx = 'trusted';

    v_user_id := (auth.uid())::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    IF p_quantity <= 0 OR p_quantity > 100 THEN
        RAISE EXCEPTION 'Invalid transaction parameters: quantity must be 1..100 (% provided)', p_quantity;
    END IF;

    -- Lookup server-side price from catalog table
    SELECT price INTO v_server_cost FROM public.app_catalog_prices
    WHERE item_id = p_item_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Item % not found in server price catalog', p_item_id;
    END IF;

    v_total_cost := v_server_cost * p_quantity;

    SELECT * INTO v_player FROM public.app_players
    WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Player profile not found for user %', v_user_id;
    END IF;

    IF COALESCE(v_player.biocoins, 0) < v_total_cost THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', 'Недостаточно BioCoins для покупки',
            'biocoins', v_player.biocoins
        );
    END IF;

    v_new_coins := v_player.biocoins - v_total_cost;

    UPDATE public.app_players
    SET
        biocoins = v_new_coins,
        updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
    WHERE id = v_player.id;

    SELECT * INTO v_existing_item FROM public.app_inventory
    WHERE (player_id)::text = (v_player.id)::text AND item_id = p_item_id
    LIMIT 1;

    IF FOUND THEN
        UPDATE public.app_inventory
        SET quantity = quantity + p_quantity
        WHERE id = v_existing_item.id;
    ELSE
        SELECT (data_type = 'uuid') INTO v_is_uuid
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'app_inventory'
          AND column_name = 'player_id';

        IF COALESCE(v_is_uuid, false) THEN
            INSERT INTO public.app_inventory (player_id, item_id, quantity, is_equipped)
            VALUES ((v_player.id)::text::uuid, p_item_id, p_quantity, false);
        ELSE
            INSERT INTO public.app_inventory (player_id, item_id, quantity, is_equipped)
            VALUES ((v_player.id)::text, p_item_id, p_quantity, false);
        END IF;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'item_id', p_item_id,
        'biocoins', v_new_coins,
        'quantity', p_quantity
    );
END;
$$;

-- ==============================================================================
-- 8. RPC: sync_player_inventory (hardened)
-- [C3] Unauthorized (anon key fallback) requests are rejected outright.
-- ==============================================================================

CREATE OR REPLACE FUNCTION public.sync_player_inventory(
    p_player_id TEXT,
    p_items JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user_id TEXT;
    v_is_uuid BOOLEAN := false;
    v_target_id TEXT;
BEGIN
    SET LOCAL eidos.server_ctx = 'trusted';

    v_user_id := (auth.uid())::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    SELECT (id)::text INTO v_target_id
    FROM public.app_players
    WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id;

    IF v_user_id <> p_player_id AND (v_target_id IS NULL OR v_target_id <> p_player_id) THEN
        RAISE EXCEPTION 'Access Denied: Cannot sync inventory for player % with auth %', p_player_id, v_user_id;
    END IF;

    IF p_player_id IS NULL OR trim(p_player_id) = '' THEN
        RAISE EXCEPTION 'Invalid player_id provided';
    END IF;

    SELECT (data_type = 'uuid') INTO v_is_uuid
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'app_inventory'
      AND column_name = 'player_id';

    DELETE FROM public.app_inventory WHERE (player_id)::text = p_player_id;

    IF p_items IS NOT NULL AND jsonb_array_length(p_items) > 0 THEN
        IF COALESCE(v_is_uuid, false) THEN
            INSERT INTO public.app_inventory (player_id, item_id, quantity, is_equipped)
            SELECT
                p_player_id::uuid,
                elem->>'item_id',
                COALESCE((elem->>'quantity')::INT, 1),
                COALESCE((elem->>'is_equipped')::BOOLEAN, false)
            FROM jsonb_array_elements(p_items) AS elem;
        ELSE
            INSERT INTO public.app_inventory (player_id, item_id, quantity, is_equipped)
            SELECT
                p_player_id,
                elem->>'item_id',
                COALESCE((elem->>'quantity')::INT, 1),
                COALESCE((elem->>'is_equipped')::BOOLEAN, false)
            FROM jsonb_array_elements(p_items) AS elem;
        END IF;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'player_id', p_player_id,
        'count', COALESCE(jsonb_array_length(p_items), 0)
    );
END;
$$;

-- ==============================================================================
-- 9. RPC: verify_and_record_purchase (service-role only)
-- [C4] This ledger MUST be filled by a Supabase Edge Function that first
-- verifies the purchase token against Google Play Developer API
-- (purchases.products.get) and derives biocoins from the product_id.
-- Direct client calls are revoked; biocoins_granted is capped.
--
-- Two caller modes:
--   * authenticated user JWT -> writes only to their own player row;
--   * service_role (Edge Function) -> must pass p_player_id explicitly and
--     the function verifies that player exists (auth.uid() is NULL for
--     service_role JWTs, so the uid path cannot apply).
-- ==============================================================================

-- The signature gained p_player_id; drop the legacy 4-arg version to avoid
-- an unhardened leftover.
DROP FUNCTION IF EXISTS public.verify_and_record_purchase(TEXT, TEXT, TEXT, BIGINT);

CREATE OR REPLACE FUNCTION public.verify_and_record_purchase(
    p_order_id TEXT,
    p_token_hash TEXT,
    p_product_id TEXT,
    p_biocoins BIGINT,
    p_player_id TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user_id TEXT;
    v_target_player_id TEXT;
BEGIN
    SET LOCAL eidos.server_ctx = 'trusted';

    -- Even a trusted caller cannot grant an absurd amount
    IF p_biocoins IS NULL OR p_biocoins < 0 OR p_biocoins > 1000000 THEN
        RAISE EXCEPTION 'Invalid biocoins grant: %', p_biocoins;
    END IF;

    v_user_id := (auth.uid())::text;

    IF v_user_id IS NOT NULL THEN
        -- Authenticated caller: only their own player row can be credited
        IF NOT EXISTS (
            SELECT 1 FROM public.app_players
            WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id
        ) THEN
            RAISE EXCEPTION 'Player profile not found for user %', v_user_id;
        END IF;
        SELECT (id)::text INTO v_target_player_id
        FROM public.app_players
        WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id
        LIMIT 1;
    ELSE
        -- Service-role caller (Edge Function after Google Play verification):
        -- explicit target player is mandatory.
        IF (auth.role())::text <> 'service_role' THEN
            RAISE EXCEPTION 'Unauthorized: User session missing';
        END IF;
        IF p_player_id IS NULL OR trim(p_player_id) = '' THEN
            RAISE EXCEPTION 'p_player_id is required for service-role calls';
        END IF;
        v_target_player_id := trim(p_player_id);
        IF NOT EXISTS (
            SELECT 1 FROM public.app_players WHERE (id)::text = v_target_player_id
        ) THEN
            RAISE EXCEPTION 'Player profile not found for player_id %', v_target_player_id;
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM public.app_purchases WHERE token_hash = p_token_hash) THEN
        RETURN jsonb_build_object('success', false, 'error', 'Purchase token already consumed');
    END IF;

    INSERT INTO public.app_purchases (player_id, order_id, token_hash, product_id, biocoins_granted)
    VALUES (v_target_player_id, p_order_id, p_token_hash, p_product_id, p_biocoins);

    UPDATE public.app_players
    SET biocoins = COALESCE(biocoins, 0) + p_biocoins,
        updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
    WHERE (id)::text = v_target_player_id;

    RETURN jsonb_build_object('success', true, 'biocoins_granted', p_biocoins);
END;
$$;

-- Reserve for Edge Function (service_role). PostgREST clients are locked out.
REVOKE EXECUTE ON FUNCTION public.verify_and_record_purchase(TEXT, TEXT, TEXT, BIGINT, TEXT) FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.verify_and_record_purchase(TEXT, TEXT, TEXT, BIGINT, TEXT) FROM anon;
REVOKE EXECUTE ON FUNCTION public.verify_and_record_purchase(TEXT, TEXT, TEXT, BIGINT, TEXT) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.verify_and_record_purchase(TEXT, TEXT, TEXT, BIGINT, TEXT) TO service_role;

-- ==============================================================================
-- 10. RPC: resolve_pvp_match (hardened)
-- [C6] 30s cooldown, self-match block, randomized defense programs,
-- validated attack programs. Attacker context is trusted for its own writes.
-- ==============================================================================

CREATE OR REPLACE FUNCTION public.resolve_pvp_match(
    p_defender_id TEXT,
    p_attacker_programs TEXT[],
    p_has_firewall BOOLEAN DEFAULT false
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_attacker_id TEXT;
    v_attacker RECORD;
    v_defender RECORD;
    v_player_wins INT := 0;
    v_defender_wins INT := 0;
    v_firewall_left BOOLEAN := p_has_firewall;
    v_firewall_triggered BOOLEAN := false;
    v_round_res INT;
    v_atk_prog TEXT;
    v_def_prog TEXT;
    v_stolen_coins BIGINT := 0;
    v_lost_coins BIGINT := 0;
    v_xp_gained BIGINT := 0;
    v_is_win BOOLEAN := false;
    v_def_programs TEXT[] := ARRAY['BRUTEFORCE', 'SHIELD', 'STEALTH'];
BEGIN
    PERFORM public.assert_rpc_rate_limit('pvp_match', 30000);
    SET LOCAL eidos.server_ctx = 'trusted';

    v_attacker_id := (auth.uid())::text;
    IF v_attacker_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    IF array_length(COALESCE(p_attacker_programs, '{}'::TEXT[]), 1) IS NULL
       OR array_length(p_attacker_programs, 1) <> 3 THEN
        RAISE EXCEPTION 'Invalid attack programs: exactly 3 required';
    END IF;

    SELECT * INTO v_attacker FROM public.app_players
    WHERE (id)::text = v_attacker_id OR (device_id)::text = v_attacker_id
    LIMIT 1;

    IF v_attacker.id IS NULL THEN
        RAISE EXCEPTION 'Attacker profile not found';
    END IF;

    SELECT * INTO v_defender FROM public.app_players
    WHERE (id)::text = p_defender_id OR (device_id)::text = p_defender_id
    LIMIT 1;

    IF v_defender.id IS NULL THEN
        RAISE EXCEPTION 'Defender profile not found';
    END IF;

    -- Self-matching would be a closed XP loop
    IF v_attacker.id = v_defender.id THEN
        RAISE EXCEPTION 'Invalid match: attacker and defender are the same player';
    END IF;

    -- Defense programs are randomized server-side (was: predictable NOW() second)
    v_def_programs := ARRAY(
        SELECT (ARRAY['BRUTEFORCE', 'SHIELD', 'STEALTH'])[1 + FLOOR(RANDOM() * 3)::INT]
        FROM generate_series(1, 3)
    );

    FOR i IN 1..3 LOOP
        v_atk_prog := COALESCE(p_attacker_programs[i], 'BRUTEFORCE');
        IF v_atk_prog NOT IN ('BRUTEFORCE', 'SHIELD', 'STEALTH') THEN
            RAISE EXCEPTION 'Invalid attack program: %', v_atk_prog;
        END IF;
        v_def_prog := v_def_programs[i];

        IF v_atk_prog = v_def_prog THEN
            v_round_res := 0;
        ELSIF (v_atk_prog = 'BRUTEFORCE' AND v_def_prog = 'STEALTH')
           OR (v_atk_prog = 'STEALTH' AND v_def_prog = 'SHIELD')
           OR (v_atk_prog = 'SHIELD' AND v_def_prog = 'BRUTEFORCE') THEN
            v_round_res := 1;
        ELSE
            v_round_res := 2;
        END IF;

        IF v_round_res = 2 AND v_firewall_left THEN
            v_round_res := 0;
            v_firewall_left := false;
            v_firewall_triggered := true;
        END IF;

        IF v_round_res = 1 THEN
            v_player_wins := v_player_wins + 1;
        ELSIF v_round_res = 2 THEN
            v_defender_wins := v_defender_wins + 1;
        END IF;
    END LOOP;

    v_is_win := v_player_wins > v_defender_wins;

    IF v_is_win THEN
        v_stolen_coins := LEAST(GREATEST(COALESCE(v_defender.biocoins, 0) / 10, 50), 2000);
        v_xp_gained := 150 + (v_player_wins * 50);

        UPDATE public.app_players
        SET biocoins = GREATEST(COALESCE(biocoins, 0) - v_stolen_coins, 0),
            updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
        WHERE id = v_defender.id;

        UPDATE public.app_players
        SET biocoins = COALESCE(biocoins, 0) + v_stolen_coins,
            exp = COALESCE(exp, 0) + v_xp_gained,
            updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
        WHERE id = v_attacker.id;
    ELSE
        v_lost_coins := 50;
        UPDATE public.app_players
        SET biocoins = GREATEST(COALESCE(biocoins, 0) - v_lost_coins, 0),
            updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
        WHERE id = v_attacker.id;
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'is_win', v_is_win,
        'player_wins', v_player_wins,
        'defender_wins', v_defender_wins,
        'stolen_coins', v_stolen_coins,
        'coins_lost', v_lost_coins,
        'xp_gained', v_xp_gained,
        'firewall_triggered', v_firewall_triggered
    );
END;
$$;
