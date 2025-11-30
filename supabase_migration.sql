-- MoneyMate Database Migration for Supabase PostgreSQL
-- This script creates all tables with Row-Level Security (RLS) policies
-- Run this in Supabase SQL Editor: https://app.supabase.com → SQL Editor

-- Enable UUID extension (for generating UUIDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USER SETTINGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS user_settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  monthly_income DECIMAL(10,2) DEFAULT 0,
  onboarding_complete BOOLEAN DEFAULT false,
  default_language VARCHAR(2) DEFAULT 'he', -- 'he' or 'en'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Enable RLS
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_settings
CREATE POLICY "Users can view own settings"
  ON user_settings FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings"
  ON user_settings FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own settings"
  ON user_settings FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own settings"
  ON user_settings FOR DELETE
  USING (auth.uid() = user_id);

-- ============================================
-- EXPENSES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS expenses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  purchase_date DATE NOT NULL,
  business_name TEXT,
  transaction_amount DECIMAL(10,2),
  transaction_currency VARCHAR(3),
  billing_amount DECIMAL(10,2) NOT NULL,
  billing_currency VARCHAR(3),
  voucher_number TEXT,
  additional_details TEXT,
  category TEXT NOT NULL,
  source_file TEXT,
  processed_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  classification_method TEXT, -- 'keyword', 'manual', 'ai', 'default'
  classification_confidence REAL,
  classification_reason TEXT,
  manually_edited BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  -- Prevent duplicate expenses per user
  UNIQUE(user_id, purchase_date, business_name, billing_amount, voucher_number)
);

-- Create indexes for better query performance
CREATE INDEX idx_expenses_user_id ON expenses(user_id);
CREATE INDEX idx_expenses_purchase_date ON expenses(purchase_date);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_user_date ON expenses(user_id, purchase_date);

-- Enable RLS
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

-- RLS Policies for expenses
CREATE POLICY "Users can view own expenses"
  ON expenses FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own expenses"
  ON expenses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own expenses"
  ON expenses FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own expenses"
  ON expenses FOR DELETE
  USING (auth.uid() = user_id);

-- ============================================
-- FIXED EXPENSES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS fixed_expenses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  description TEXT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  category TEXT NOT NULL,
  expense_type TEXT, -- 'need' or 'want'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index
CREATE INDEX idx_fixed_expenses_user_id ON fixed_expenses(user_id);

-- Enable RLS
ALTER TABLE fixed_expenses ENABLE ROW LEVEL SECURITY;

-- RLS Policies for fixed_expenses
CREATE POLICY "Users can view own fixed expenses"
  ON fixed_expenses FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own fixed expenses"
  ON fixed_expenses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own fixed expenses"
  ON fixed_expenses FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own fixed expenses"
  ON fixed_expenses FOR DELETE
  USING (auth.uid() = user_id);

-- ============================================
-- PROCESSED FILES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS processed_files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  filename TEXT NOT NULL,
  processed_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  record_count INTEGER,
  file_hash TEXT, -- SHA256 hash to detect duplicates
  UNIQUE(user_id, filename)
);

-- Create index
CREATE INDEX idx_processed_files_user_id ON processed_files(user_id);

-- Enable RLS
ALTER TABLE processed_files ENABLE ROW LEVEL SECURITY;

-- RLS Policies for processed_files
CREATE POLICY "Users can view own processed files"
  ON processed_files FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own processed files"
  ON processed_files FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own processed files"
  ON processed_files FOR DELETE
  USING (auth.uid() = user_id);

-- ============================================
-- SHARED DASHBOARDS TABLE (for public sharing)
-- ============================================
CREATE TABLE IF NOT EXISTS shared_dashboards (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  share_token TEXT UNIQUE NOT NULL, -- Random token for sharing
  year INTEGER,
  month INTEGER,
  share_all_months BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiration
  view_count INTEGER DEFAULT 0,
  last_viewed_at TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN DEFAULT true
);

-- Create indexes
CREATE INDEX idx_shared_dashboards_user_id ON shared_dashboards(user_id);
CREATE INDEX idx_shared_dashboards_token ON shared_dashboards(share_token);

-- Enable RLS
ALTER TABLE shared_dashboards ENABLE ROW LEVEL SECURITY;

-- RLS Policies for shared_dashboards
CREATE POLICY "Users can view own shared dashboards"
  ON shared_dashboards FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create shared dashboards"
  ON shared_dashboards FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own shared dashboards"
  ON shared_dashboards FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own shared dashboards"
  ON shared_dashboards FOR DELETE
  USING (auth.uid() = user_id);

-- Public access policy (anyone with token can view)
CREATE POLICY "Anyone can view active shared dashboards"
  ON shared_dashboards FOR SELECT
  USING (
    is_active = true
    AND (expires_at IS NULL OR expires_at > NOW())
  );

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_user_settings_updated_at
  BEFORE UPDATE ON user_settings
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fixed_expenses_updated_at
  BEFORE UPDATE ON fixed_expenses
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View for monthly expense summary
CREATE OR REPLACE VIEW monthly_expense_summary AS
SELECT
  user_id,
  EXTRACT(YEAR FROM purchase_date) AS year,
  EXTRACT(MONTH FROM purchase_date) AS month,
  category,
  COUNT(*) AS transaction_count,
  SUM(billing_amount) AS total_amount
FROM expenses
GROUP BY user_id, year, month, category;

-- Enable RLS on view
ALTER VIEW monthly_expense_summary SET (security_invoker = true);

-- ============================================
-- HELPER RPC FUNCTIONS
-- ============================================

-- Function to get available months for a user
CREATE OR REPLACE FUNCTION get_user_expense_months(p_user_id UUID)
RETURNS TABLE (year INT, month INT) AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT
    EXTRACT(YEAR FROM purchase_date)::INT AS year,
    EXTRACT(MONTH FROM purchase_date)::INT AS month
  FROM expenses
  WHERE user_id = p_user_id
  ORDER BY year DESC, month DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- STORAGE BUCKET (if not created via UI)
-- ============================================
-- Note: You should create this in the Supabase Storage UI
-- Bucket name: expense-files
-- Public: false
-- Allowed file types: xlsx, xls
-- Max file size: 16 MB

-- ============================================
-- INITIAL SETUP COMPLETE
-- ============================================

-- Verify tables were created
SELECT
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('user_settings', 'expenses', 'fixed_expenses', 'processed_files', 'shared_dashboards')
ORDER BY tablename;

-- Output: You should see 5 tables, all with rls_enabled = true
