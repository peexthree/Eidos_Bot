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
-- ⚡ RPC STORED PROCEDURES (SERVER-SIDE BUSINESS LOGIC)
-- ==============================================================================

-- Procedure 1: process_raid_reward
-- Securely awards EXP, BioCoins, and updates max depth on server-side
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
    v_new_exp BIGINT;
    v_new_coins BIGINT;
    v_new_depth INT;
BEGIN
    v_user_id := auth.uid()::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    SELECT * INTO v_player FROM public.app_players
    WHERE player_id = v_user_id OR device_id = v_user_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Player profile not found for user %', v_user_id;
    END IF;

    v_new_exp := COALESCE(v_player.exp, 0) + GREATEST(0, p_exp);
    v_new_coins := COALESCE(v_player.biocoins, 0) + GREATEST(0, p_biocoins);
    v_new_depth := GREATEST(COALESCE(v_player.max_depth, 0), GREATEST(0, p_depth));

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
-- Securely verifies balance and awards items on server-side
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
    v_new_coins BIGINT;
    v_existing_item RECORD;
BEGIN
    v_user_id := auth.uid()::text;
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: Session missing';
    END IF;

    SELECT * INTO v_player FROM public.app_players
    WHERE player_id = v_user_id OR device_id = v_user_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Player profile not found for user %', v_user_id;
    END IF;

    IF COALESCE(v_player.biocoins, 0) < p_cost THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', 'Недостаточно BioCoins для покупки',
            'biocoins', v_player.biocoins
        );
    END IF;

    v_new_coins := v_player.biocoins - p_cost;

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
        SET quantity = quantity + GREATEST(1, p_quantity)
        WHERE id = v_existing_item.id;
    ELSE
        INSERT INTO public.app_inventory (player_id, item_id, quantity, is_equipped)
        VALUES (v_user_id, p_item_id, GREATEST(1, p_quantity), false);
    END IF;

    RETURN jsonb_build_object(
        'success', true,
        'item_id', p_item_id,
        'biocoins', v_new_coins
    );
END;
$$;
