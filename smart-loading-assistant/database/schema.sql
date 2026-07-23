-- PostgreSQL Supabase Schema for Smart Loading Assistant

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Trucks Table
CREATE TABLE trucks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    length FLOAT NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,
    max_weight FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Cargo Manifests Table
CREATE TABLE cargo_manifests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Cargo Items Table
CREATE TABLE cargo_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manifest_id UUID NOT NULL REFERENCES cargo_manifests(id) ON DELETE CASCADE,
    label VARCHAR(255) NOT NULL,
    length FLOAT NOT NULL,
    width FLOAT NOT NULL,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    is_fragile BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Loading Plans Table
CREATE TABLE loading_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    truck_id UUID NOT NULL REFERENCES trucks(id) ON DELETE CASCADE,
    manifest_id UUID NOT NULL REFERENCES cargo_manifests(id) ON DELETE CASCADE,
    left_weight_kg FLOAT DEFAULT 0.0,
    right_weight_kg FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Loading Plan Steps Table (The calculated coordinates and sequence)
CREATE TABLE loading_plan_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES loading_plans(id) ON DELETE CASCADE,
    cargo_item_id UUID NOT NULL REFERENCES cargo_items(id) ON DELETE CASCADE,
    sequence_number INT NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL,
    z FLOAT NOT NULL,
    orientation_length FLOAT NOT NULL,
    orientation_width FLOAT NOT NULL,
    orientation_height FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Basic Row Level Security (RLS) setup (assuming simple authenticated access for MVP)
ALTER TABLE trucks ENABLE ROW LEVEL SECURITY;
ALTER TABLE cargo_manifests ENABLE ROW LEVEL SECURITY;
ALTER TABLE cargo_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE loading_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE loading_plan_steps ENABLE ROW LEVEL SECURITY;

-- Allow all authenticated users to read/write for MVP
CREATE POLICY "Allow authenticated read/write on trucks" ON trucks FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow authenticated read/write on manifests" ON cargo_manifests FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow authenticated read/write on cargo_items" ON cargo_items FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow authenticated read/write on plans" ON loading_plans FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow authenticated read/write on plan_steps" ON loading_plan_steps FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Allow anon read access for MVP testing (Frontend)
CREATE POLICY "Allow anon read on trucks" ON trucks FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read on manifests" ON cargo_manifests FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read on cargo_items" ON cargo_items FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read on plans" ON loading_plans FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon read on plan_steps" ON loading_plan_steps FOR SELECT TO anon USING (true);
