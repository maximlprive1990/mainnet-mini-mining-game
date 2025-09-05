-- Supabase Database Schema for mAInet Crypto Mining Game
-- Execute this SQL in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id uuid REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    username text UNIQUE NOT NULL,
    full_name text,
    bio text,
    avatar_url text,
    experience_level integer DEFAULT 1,
    total_coins_mined bigint DEFAULT 0,
    current_mining_power integer DEFAULT 0,
    last_active_at timestamptz DEFAULT now(),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    privacy_settings jsonb DEFAULT '{"show_stats": true, "show_achievements": true, "allow_friend_requests": true}',
    notification_preferences jsonb DEFAULT '{"mining_rewards": true, "achievements": true, "friend_activities": true, "system_updates": true}'
);

-- Game states table
CREATE TABLE IF NOT EXISTS public.game_states (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
    current_level integer NOT NULL DEFAULT 1,
    experience_points bigint NOT NULL DEFAULT 0,
    current_coins bigint NOT NULL DEFAULT 1000,
    main_balance decimal(15,2) DEFAULT 1000.00,
    bonus_balance decimal(15,2) DEFAULT 0.00,
    energy integer DEFAULT 100,
    max_energy integer DEFAULT 100,
    energy_regen_rate decimal(3,1) DEFAULT 1.0,
    click_power integer DEFAULT 1,
    auto_mining_rate decimal(8,2) DEFAULT 0.00,
    total_clicks bigint DEFAULT 0,
    achievements jsonb DEFAULT '[]',
    game_settings jsonb DEFAULT '{"sound_enabled": true, "notifications_enabled": true, "auto_collect_rewards": false}',
    last_login_reward_at timestamptz,
    mining_session_start_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Mining rigs table
CREATE TABLE IF NOT EXISTS public.mining_rigs (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    rig_name text NOT NULL,
    rig_type text NOT NULL,
    mining_power decimal(8,2) NOT NULL DEFAULT 0.5,
    efficiency_rating decimal(3,2) NOT NULL DEFAULT 1.00,
    power_consumption integer NOT NULL DEFAULT 65,
    upgrade_level integer NOT NULL DEFAULT 1,
    is_active boolean DEFAULT true,
    rarity text NOT NULL DEFAULT 'common',
    bonus_effects jsonb DEFAULT '{}',
    last_maintenance_at timestamptz DEFAULT now(),
    total_coins_mined bigint DEFAULT 0,
    purchase_price integer NOT NULL DEFAULT 100,
    installed_slot jsonb,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Transactions table
CREATE TABLE IF NOT EXISTS public.transactions (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    transaction_type text NOT NULL,
    amount decimal(15,2) NOT NULL,
    balance_before decimal(15,2) NOT NULL,
    balance_after decimal(15,2) NOT NULL,
    description text NOT NULL,
    related_rig_id uuid REFERENCES public.mining_rigs(id),
    status text DEFAULT 'completed',
    metadata jsonb,
    created_at timestamptz DEFAULT now()
);

-- Transaction verifications table (for IDTX system)
CREATE TABLE IF NOT EXISTS public.transaction_verifications (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    transaction_id text NOT NULL,
    amount decimal(10,2) NOT NULL,
    currency text DEFAULT 'USD',
    payment_method text NOT NULL,
    status text DEFAULT 'pending',
    bonus_amount decimal(10,2) DEFAULT 0.00,
    bonus_credited boolean DEFAULT false,
    verification_data jsonb,
    created_at timestamptz DEFAULT now(),
    verified_at timestamptz
);

-- Upgrades table
CREATE TABLE IF NOT EXISTS public.upgrades (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    upgrade_type text NOT NULL,
    current_level integer DEFAULT 0,
    total_cost decimal(15,2) DEFAULT 0.00,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(user_id, upgrade_type)
);

-- Mining installations table (for rack system)
CREATE TABLE IF NOT EXISTS public.mining_installations (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    rack_id integer NOT NULL,
    rack_type text NOT NULL,
    owned boolean DEFAULT false,
    slots_configuration jsonb DEFAULT '{}',
    total_hashrate decimal(8,2) DEFAULT 0.00,
    total_power_consumption integer DEFAULT 0,
    purchase_date timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(user_id, rack_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_username ON public.profiles(username);
CREATE INDEX IF NOT EXISTS idx_mining_rigs_user_active ON public.mining_rigs(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON public.transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_verifications_user_status ON public.transaction_verifications(user_id, status);

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mining_rigs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transaction_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upgrades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mining_installations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Profiles policies
CREATE POLICY "Users can view and update own profile" ON public.profiles
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Public profiles are viewable by everyone" ON public.profiles
    FOR SELECT USING (true);

-- Game states policies
CREATE POLICY "Users can manage own game state" ON public.game_states
    FOR ALL USING (user_id = auth.uid());

-- Mining rigs policies
CREATE POLICY "Users can manage own mining rigs" ON public.mining_rigs
    FOR ALL USING (user_id = auth.uid());

-- Transactions policies
CREATE POLICY "Users can view own transactions" ON public.transactions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "System can insert transactions" ON public.transactions
    FOR INSERT WITH CHECK (true);

-- Transaction verifications policies
CREATE POLICY "Users can manage own verifications" ON public.transaction_verifications
    FOR ALL USING (user_id = auth.uid());

-- Upgrades policies
CREATE POLICY "Users can manage own upgrades" ON public.upgrades
    FOR ALL USING (user_id = auth.uid());

-- Mining installations policies
CREATE POLICY "Users can manage own installations" ON public.mining_installations
    FOR ALL USING (user_id = auth.uid());

-- Function to handle user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, username, full_name)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'username', 'user_' || substr(new.id::text, 1, 8)),
    new.raw_user_meta_data->>'full_name'
  );
  
  -- Create initial game state
  INSERT INTO public.game_states (user_id)
  VALUES (new.id);
  
  -- Initialize mining installations
  INSERT INTO public.mining_installations (user_id, rack_id, rack_type)
  VALUES 
    (new.id, 1, 'compact'),
    (new.id, 2, 'standard'),
    (new.id, 3, 'pro'),
    (new.id, 4, 'elite');
  
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user creation
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Function to calculate offline mining rewards
CREATE OR REPLACE FUNCTION public.calculate_offline_rewards(p_user_id uuid)
RETURNS decimal
LANGUAGE 'plpgsql'
AS $$
DECLARE
    total_hashrate decimal(8,2) := 0;
    offline_hours decimal(8,2) := 0;
    offline_rewards decimal(15,2) := 0;
    last_session timestamptz;
BEGIN
    -- Get last mining session start
    SELECT mining_session_start_at INTO last_session
    FROM public.game_states
    WHERE user_id = p_user_id;
    
    IF last_session IS NOT NULL THEN
        -- Calculate offline hours (max 24 hours)
        offline_hours := LEAST(EXTRACT(EPOCH FROM (now() - last_session)) / 3600, 24);
        
        -- Get total mining power from active rigs
        SELECT COALESCE(SUM(mining_power * efficiency_rating), 0) INTO total_hashrate
        FROM public.mining_rigs
        WHERE user_id = p_user_id AND is_active = true;
        
        -- Calculate offline rewards (base rate: 0.1 coins per hashrate per hour)
        offline_rewards := total_hashrate * offline_hours * 0.1;
        
        -- Update mining session start time
        UPDATE public.game_states
        SET mining_session_start_at = now()
        WHERE user_id = p_user_id;
    END IF;
    
    RETURN offline_rewards;
END
$$;