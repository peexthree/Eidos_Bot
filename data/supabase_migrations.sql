-- ==============================================================================
-- 🛡️ EIDOS: ZERO LAYER - SUPABASE MIGRATIONS & RLS POLICIES (SAAS SECURITY)
-- ==============================================================================

-- 1. Enable Row Level Security (RLS) on all production tables
ALTER TABLE IF EXISTS public.app_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.app_raid_logs ENABLE ROW LEVEL SECURITY;

-- 2. Drop legacy open policies if present
DROP POLICY IF EXISTS "Public access" ON public.app_players;
DROP POLICY IF EXISTS "Public access" ON public.app_inventory;
DROP POLICY IF EXISTS "Public access" ON public.app_raid_logs;

-- 3. RLS Policies linked to auth.uid()
CREATE POLICY "Players can read and update their own profile"
    ON public.app_players
    FOR ALL
    USING (auth.uid()::text = device_id OR auth.uid()::text = player_id)
    WITH CHECK (auth.uid()::text = device_id OR auth.uid()::text = player_id);

CREATE POLICY "Players can read and manage their own inventory"
    ON public.app_inventory
    FOR ALL
    USING (auth.uid()::text = player_id)
    WITH CHECK (auth.uid()::text = player_id);

CREATE POLICY "Players can manage their own raid logs"
    ON public.app_raid_logs
    FOR ALL
    USING (auth.uid()::text = player_id)
    WITH CHECK (auth.uid()::text = player_id);

-- ==============================================================================
-- 🏷️ CATALOG PRICES TABLE (SERVER-SIDE PRICE TRUTH)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.app_catalog_prices (
    item_id TEXT PRIMARY KEY,
    price BIGINT NOT NULL CHECK (price >= 0),
    created_at BIGINT DEFAULT (EXTRACT(EPOCH FROM NOW())::BIGINT * 1000)
);

ALTER TABLE public.app_catalog_prices ENABLE ROW LEVEL SECURITY;

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
-- Securely awards EXP, BioCoins, and updates max depth with server-side limits
CREATE OR REPLACE FUNCTION public.process_raid_reward(
    p_exp BIGINT,
    p_biocoins BIGINT,
    p_depth INT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
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
    v_user_id := auth.uid()::text;
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
    WHERE player_id = v_user_id OR device_id = v_user_id
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
        updated_at = EXTRACT(EPOCH FROM NOW())::BIGINT * 1000
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
-- Securely verifies balance and awards items using server-side catalog prices
CREATE OR REPLACE FUNCTION public.black_market_purchase(
    p_item_id TEXT,
    p_cost BIGINT,
    p_quantity INT DEFAULT 1
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_user_id TEXT;
    v_player RECORD;
    v_server_cost BIGINT;
    v_total_cost BIGINT;
    v_new_coins BIGINT;
    v_existing_item RECORD;
BEGIN
    v_user_id := auth.uid()::text;
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
    WHERE player_id = v_user_id OR device_id = v_user_id
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
        updated_at = EXTRACT(EPOCH FROM NOW())::BIGINT * 1000
    WHERE id = v_player.id;

    -- Add or increment item in inventory
    SELECT * INTO v_existing_item FROM public.app_inventory
    WHERE player_id = v_user_id AND item_id = p_item_id
    LIMIT 1;

    IF FOUND THEN
        UPDATE public.app_inventory
        SET quantity = quantity + p_quantity
        WHERE id = v_existing_item.id;
    ELSE
        INSERT INTO public.app_inventory (player_id, item_id, quantity, is_equipped)
        VALUES (v_user_id, p_item_id, p_quantity, false);
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'item_id', p_item_id,
        'biocoins', v_new_coins,
        'quantity', p_quantity
    );
END;
$$;
