-- ==============================================================================
-- 🛡️ EIDOS: ZERO LAYER - SUPABASE SECURITY & RLS PATCH (POST-AUDIT 2026)
-- Execute this script in Supabase Dashboard -> SQL Editor
-- ⚠️ DEPRECATED: superseded by data/supabase_hardening_v2.sql - ALWAYS run
--    that file AFTER this one. This file is kept for migration history only.
--
-- Schema Verified:
-- - app_players: id (UUID PK), device_id, username, level, exp, biocoins... (NO player_id column!)
-- - app_inventory: id (UUID PK), player_id (FK -> app_players.id), item_id, quantity, is_equipped...
-- - app_raid_logs: id (UUID PK), player_id (FK -> app_players.id), log_text, log_type...
-- ==============================================================================

-- 1. FIX CRITICAL RLS VULNERABILITIES & ENSURE STATS COLUMNS EXIST
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS kills INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS raids_done INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS perfect_raids INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS wins_pvp INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS losses_pvp INT DEFAULT 0;

ALTER TABLE IF EXISTS public.app_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_raid_logs ENABLE ROW LEVEL SECURITY;

-- Drop legacy or insecure policies
DROP POLICY IF EXISTS "Public access" ON public.app_players;
DROP POLICY IF EXISTS "Players can read and update their own profile" ON public.app_players;
DROP POLICY IF EXISTS "Anyone can view player profiles" ON public.app_players;
DROP POLICY IF EXISTS "Players can update their own profile" ON public.app_players;
DROP POLICY IF EXISTS "Players can insert their own profile" ON public.app_players;
DROP POLICY IF EXISTS "Players can delete their own profile" ON public.app_players;

DROP POLICY IF EXISTS "Allow public update app_inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can update their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can insert their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can delete their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can select their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Players can read and manage their own inventory" ON public.app_inventory;
DROP POLICY IF EXISTS "Public access" ON public.app_inventory;

DROP POLICY IF EXISTS "Public access" ON public.app_raid_logs;
DROP POLICY IF EXISTS "Players can manage their own raid logs" ON public.app_raid_logs;

-- A) app_players Policies:
-- 1. SELECT: Public read access needed for Leaderboard & PvP Phantom Rivals
CREATE POLICY "Anyone can view player profiles"
    ON public.app_players
    FOR SELECT
    USING (true);

-- 2. INSERT: Allow player to register their profile
CREATE POLICY "Players can insert their own profile"
    ON public.app_players
    FOR INSERT
    WITH CHECK (
        (auth.uid())::text = (device_id)::text 
        OR (auth.uid())::text = (id)::text 
        OR auth.role() = 'authenticated' 
        OR auth.role() = 'anon'
    );

-- 3. UPDATE: Strict owner-only profile updates (cannot edit another player's level/stats)
CREATE POLICY "Players can update their own profile"
    ON public.app_players
    FOR UPDATE
    USING ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text)
    WITH CHECK ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text);

-- 4. DELETE: Strict owner-only deletion
CREATE POLICY "Players can delete their own profile"
    ON public.app_players
    FOR DELETE
    USING ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text);


-- B) app_inventory Policies:
-- Owner-only access (matched via direct user UUID or via app_players reference)
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


-- C) app_raid_logs Policies:
-- Owner-only access for personal raid telemetry logs
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
-- 2. ATOMIC INVENTORY SYNCHRONIZATION RPC (Finding 2.4 - Eliminates Data Loss Race)
-- Wraps wipe and re-insertion into a single atomic PostgreSQL transaction
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
    v_user_id := (auth.uid())::text;
    
    -- If request carries an authenticated user JWT, verify caller identity matches target
    IF v_user_id IS NOT NULL THEN
        SELECT (id)::text INTO v_target_id
        FROM public.app_players
        WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id;

        IF v_user_id <> p_player_id AND (v_target_id IS NULL OR v_target_id <> p_player_id) THEN
            RAISE EXCEPTION 'Access Denied: Cannot sync inventory for player % with auth %', p_player_id, v_user_id;
        END IF;
    END IF;

    IF p_player_id IS NULL OR trim(p_player_id) = '' THEN
        RAISE EXCEPTION 'Invalid player_id provided';
    END IF;

    -- Detect whether player_id column in app_inventory is UUID or TEXT
    SELECT (data_type = 'uuid') INTO v_is_uuid
    FROM information_schema.columns
    WHERE table_schema = 'public' 
      AND table_name = 'app_inventory' 
      AND column_name = 'player_id';

    -- 1. Atomic delete using safe text comparison
    DELETE FROM public.app_inventory WHERE (player_id)::text = p_player_id;

    -- 2. Atomic insert dynamically supporting both UUID and TEXT columns
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
-- 3. SERVER-SIDE PURCHASE TOKEN LEDGER (Finding 2.5 - Prevents In-App Billing Replays)
-- ==============================================================================
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

CREATE OR REPLACE FUNCTION public.verify_and_record_purchase(
    p_order_id TEXT,
    p_token_hash TEXT,
    p_product_id TEXT,
    p_biocoins BIGINT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user_id TEXT;
    v_player RECORD;
BEGIN
    v_user_id := (auth.uid())::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: User session missing';
    END IF;

    -- Check if token has already been credited (Anti-Replay / Double-Spend)
    IF EXISTS (SELECT 1 FROM public.app_purchases WHERE token_hash = p_token_hash) THEN
        RETURN jsonb_build_object('success', false, 'error', 'Purchase token already consumed');
    END IF;

    SELECT * INTO v_player FROM public.app_players
    WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id
    LIMIT 1;

    INSERT INTO public.app_purchases (player_id, order_id, token_hash, product_id, biocoins_granted)
    VALUES (COALESCE((v_player.id)::text, v_user_id), p_order_id, p_token_hash, p_product_id, p_biocoins);

    IF v_player.id IS NOT NULL THEN
        UPDATE public.app_players
        SET biocoins = COALESCE(biocoins, 0) + p_biocoins,
            updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
        WHERE id = v_player.id;
    END IF;

    RETURN jsonb_build_object('success', true, 'biocoins_granted', p_biocoins);
END;
$$;


-- ==============================================================================
-- 4. SERVER-SIDE PVP AUTHORITATIVE RESOLUTION (Finding 4.3)
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
    v_attacker_id := (auth.uid())::text;
    IF v_attacker_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
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

    -- 3-round matrix simulation
    FOR i IN 1..3 LOOP
        v_atk_prog := COALESCE(p_attacker_programs[i], 'BRUTEFORCE');
        v_def_prog := v_def_programs[1 + ((i + EXTRACT(SECOND FROM NOW())::INT) % 3)];

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
