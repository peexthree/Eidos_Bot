-- ==============================================================================
-- 🛡️ EIDOS: ZERO LAYER - SUPABASE MIGRATIONS & RLS POLICIES (SAAS SECURITY)
-- ⚠️ DEPRECATED: policies and RPCs below are superseded by
--    data/supabase_hardening_v2.sql - ALWAYS run that file AFTER this one.
--    This file is kept for migration history only.
-- ==============================================================================

-- 1. Enable Row Level Security (RLS) on all production tables
ALTER TABLE IF EXISTS public.app_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_raid_logs ENABLE ROW LEVEL SECURITY;

-- 2. Drop legacy open policies if present
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

-- 3. RLS Policies linked to auth.uid()
-- A) app_players:
CREATE POLICY "Anyone can view player profiles"
    ON public.app_players
    FOR SELECT
    USING (true);

CREATE POLICY "Players can insert their own profile"
    ON public.app_players
    FOR INSERT
    WITH CHECK (
        (auth.uid())::text = (device_id)::text 
        OR (auth.uid())::text = (id)::text 
        OR auth.role() = 'authenticated' 
        OR auth.role() = 'anon'
    );

CREATE POLICY "Players can update their own profile"
    ON public.app_players
    FOR UPDATE
    USING ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text)
    WITH CHECK ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text);

CREATE POLICY "Players can delete their own profile"
    ON public.app_players
    FOR DELETE
    USING ((auth.uid())::text = (device_id)::text OR (auth.uid())::text = (id)::text);

-- B) app_inventory:
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

-- C) app_raid_logs:
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
-- 🏷️ CATALOG PRICES TABLE (SERVER-SIDE PRICE TRUTH)
-- ==============================================================================

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

-- Seed catalog prices
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

-- ==============================================================================
-- ⚡ RPC STORED PROCEDURES (SERVER-SIDE BUSINESS LOGIC)
-- ==============================================================================

-- Procedure 1: process_raid_reward
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
    v_max_allowed_coins BIGINT;
    v_max_allowed_exp BIGINT;
    v_new_exp BIGINT;
    v_new_coins BIGINT;
    v_new_depth INT;
BEGIN
    v_user_id := (auth.uid())::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    -- Negative parameter bounds check
    IF p_depth < 0 OR p_biocoins < 0 OR p_exp < 0 THEN
        RAISE EXCEPTION 'Invalid parameters: Bounds check failed (depth %, coins %, exp %)', p_depth, p_biocoins, p_exp;
    END IF;

    -- Ceiling limits check
    v_max_allowed_coins := (p_depth * 50 + 1000);
    v_max_allowed_exp := (p_depth * 30 + 500);

    IF p_biocoins > v_max_allowed_coins THEN
        RAISE EXCEPTION 'Reward exceeds allowed BioCoins limit for depth %: % > %', p_depth, p_biocoins, v_max_allowed_coins;
    END IF;

    IF p_exp > v_max_allowed_exp THEN
        RAISE EXCEPTION 'Reward exceeds allowed EXP limit for depth %: % > %', p_depth, p_exp, v_max_allowed_exp;
    END IF;

    SELECT * INTO v_player FROM public.app_players
    WHERE (id)::text = v_user_id OR (device_id)::text = v_user_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Player profile not found for user %', v_user_id;
    END IF;

    v_new_exp := COALESCE(v_player.exp, 0) + p_exp;
    v_new_coins := COALESCE(v_player.biocoins, 0) + p_biocoins;
    v_new_depth := GREATEST(COALESCE(v_player.max_depth, 0), p_depth);

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

-- Procedure 2: black_market_purchase
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
    v_user_id := (auth.uid())::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Invalid transaction parameters: quantity must be positive (% provided)', p_quantity;
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

    -- Deduct currency
    UPDATE public.app_players
    SET
        biocoins = v_new_coins,
        updated_at = (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
    WHERE id = v_player.id;

    -- Add or increment item in inventory
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
-- 🛡️ SECURITY PATCH PROCEDURES (INVENTORY ATOMIC SYNC, IN-APP BILLING, PVP)
-- ==============================================================================

-- Procedure 3: sync_player_inventory
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

-- Table & Procedure 4: In-App Purchases Token Ledger & Verification
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

-- Procedure 5: Server-Side PvP Match Resolution
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

-- 12. ENSURE STATS COLUMNS (kills, raids_done, etc.) EXIST FOR AUDIT COMPLIANCE
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS kills INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS raids_done INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS perfect_raids INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS wins_pvp INT DEFAULT 0;
ALTER TABLE IF EXISTS public.app_players ADD COLUMN IF NOT EXISTS losses_pvp INT DEFAULT 0;
