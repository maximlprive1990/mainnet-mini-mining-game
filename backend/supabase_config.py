"""
Supabase Configuration and Database Schema Setup
Complete replacement for MongoDB with Supabase PostgreSQL
"""

import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") 
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Database Schema Creation SQL
DATABASE_SCHEMA = """
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
    rig_type text NOT NULL CHECK (rig_type IN ('basic_cpu', 'entry_gpu', 'dual_core', 'quad_core', 'gtx_miner', 'asic_basic', 'rtx_3080', 'asic_s19', 'custom_rig', 'rtx_4090', 'asic_s21', 'quantum_chip', 'ai_processor', 'fusion_reactor', 'black_hole', 'mainet_core')),
    mining_power decimal(8,2) NOT NULL DEFAULT 0.5,
    efficiency_rating decimal(3,2) NOT NULL DEFAULT 1.00,
    power_consumption integer NOT NULL DEFAULT 65,
    upgrade_level integer NOT NULL DEFAULT 1,
    is_active boolean DEFAULT true,
    rarity text NOT NULL DEFAULT 'common' CHECK (rarity IN ('common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic')),
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
    transaction_type text NOT NULL CHECK (transaction_type IN ('mining_reward', 'purchase', 'upgrade', 'transfer_in', 'transfer_out', 'daily_bonus', 'achievement_reward', 'deposit_bonus', 'verification_bonus')),
    amount decimal(15,2) NOT NULL,
    balance_before decimal(15,2) NOT NULL,
    balance_after decimal(15,2) NOT NULL,
    description text NOT NULL,
    related_rig_id uuid REFERENCES public.mining_rigs(id),
    status text DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
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
    payment_method text NOT NULL CHECK (payment_method IN ('payeer', 'faucetpay')),
    status text DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'failed', 'not_found')),
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
    upgrade_type text NOT NULL CHECK (upgrade_type IN ('ENERGY_REGEN', 'CLICK_POWER', 'AUTO_MINING', 'MAX_ENERGY')),
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
    rack_id integer NOT NULL CHECK (rack_id IN (1, 2, 3, 4)),
    rack_type text NOT NULL CHECK (rack_type IN ('compact', 'standard', 'pro', 'elite')),
    owned boolean DEFAULT false,
    slots_configuration jsonb DEFAULT '{}',
    total_hashrate decimal(8,2) DEFAULT 0.00,
    total_power_consumption integer DEFAULT 0,
    purchase_date timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(user_id, rack_id)
);

-- Achievements tracking table
CREATE TABLE IF NOT EXISTS public.user_achievements (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    achievement_id text NOT NULL,
    achievement_name text NOT NULL,
    achievement_description text,
    unlocked_at timestamptz DEFAULT now(),
    reward_amount decimal(10,2) DEFAULT 0.00,
    metadata jsonb,
    UNIQUE(user_id, achievement_id)
);

-- User devices table (for multi-device sync)
CREATE TABLE IF NOT EXISTS public.user_devices (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    device_id text NOT NULL,
    device_name text NOT NULL,
    device_type text NOT NULL,
    os_version text,
    app_version text,
    first_seen_at timestamptz DEFAULT now(),
    last_seen_at timestamptz DEFAULT now(),
    deactivated_at timestamptz,
    is_active boolean DEFAULT true,
    UNIQUE(user_id, device_id)
);

-- Admin logs table
CREATE TABLE IF NOT EXISTS public.admin_logs (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    admin_user_id uuid REFERENCES auth.users(id),
    action_type text NOT NULL,
    target_user_id uuid REFERENCES public.profiles(id),
    description text NOT NULL,
    metadata jsonb,
    created_at timestamptz DEFAULT now()
);

-- State events table (for analytics and monitoring)
CREATE TABLE IF NOT EXISTS public.state_events (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    metadata jsonb,
    created_at timestamptz DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_username ON public.profiles(username);
CREATE INDEX IF NOT EXISTS idx_mining_rigs_user_active ON public.mining_rigs(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON public.transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type_created ON public.transactions(transaction_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_verifications_user_status ON public.transaction_verifications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_installations_user_rack ON public.mining_installations(user_id, rack_id);
CREATE INDEX IF NOT EXISTS idx_devices_user_active ON public.user_devices(user_id, is_active);

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mining_rigs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transaction_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upgrades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mining_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.state_events ENABLE ROW LEVEL SECURITY;

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

-- User achievements policies
CREATE POLICY "Users can view own achievements" ON public.user_achievements
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "System can insert achievements" ON public.user_achievements
    FOR INSERT WITH CHECK (true);

-- User devices policies
CREATE POLICY "Users can manage own devices" ON public.user_devices
    FOR ALL USING (user_id = auth.uid());

-- Admin logs policies (admin only)
CREATE POLICY "Admin users only" ON public.admin_logs
    FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- State events policies
CREATE POLICY "Users can view own state events" ON public.state_events
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "System can insert state events" ON public.state_events
    FOR INSERT WITH CHECK (true);

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

-- Function to process mining rewards
CREATE OR REPLACE FUNCTION public.process_mining_reward(p_user_id uuid, p_rig_id uuid, p_amount decimal)
RETURNS integer
LANGUAGE 'plpgsql'
AS $$
DECLARE
    current_balance decimal(15,2);
BEGIN
    -- Get current balance
    SELECT current_coins INTO current_balance
    FROM public.game_states 
    WHERE user_id = p_user_id;
    
    -- Update user's balance
    UPDATE public.game_states 
    SET current_coins = current_coins + p_amount,
        main_balance = main_balance + p_amount,
        updated_at = now()
    WHERE user_id = p_user_id;
    
    -- Update rig's total mined
    UPDATE public.mining_rigs 
    SET total_coins_mined = total_coins_mined + p_amount,
        updated_at = now()
    WHERE id = p_rig_id AND user_id = p_user_id;
    
    -- Record transaction
    INSERT INTO public.transactions (user_id, transaction_type, amount, balance_before, balance_after, description, related_rig_id)
    VALUES (p_user_id, 'mining_reward', p_amount, current_balance, current_balance + p_amount, 'Mining reward', p_rig_id);
    
    RETURN 1;
END
$$;

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
"""

async def initialize_database():
    """Initialize Supabase database with complete schema"""
    try:
        print("🚀 Initializing Supabase database schema...")
        
        # Execute schema creation using admin client
        result = supabase_admin.rpc('execute_raw_sql', {'sql': DATABASE_SCHEMA}).execute()
        
        print("✅ Database schema initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

def get_supabase_client():
    """Get standard Supabase client for normal operations"""
    return supabase

def get_supabase_admin_client():
    """Get admin Supabase client for administrative operations"""
    return supabase_admin

if __name__ == "__main__":
    # Run database initialization
    asyncio.run(initialize_database())