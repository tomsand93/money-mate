# Supabase Setup Guide for MoneyMate

Follow these steps to set up your free Supabase project for MoneyMate.

## Step 1: Create Supabase Account

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (recommended) or email
4. Verify your email if needed

## Step 2: Create New Project

1. Click "New Project"
2. Fill in project details:
   - **Name:** MoneyMate
   - **Database Password:** Generate a strong password (SAVE THIS!)
   - **Region:** Choose closest to your users (Europe for Israel)
   - **Pricing Plan:** Free (500MB database, plenty for thousands of users)
3. Click "Create new project"
4. Wait 2-3 minutes for provisioning

## Step 3: Get Your Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy these values (you'll need them later):
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon public key:** `eyJhbGc...` (long string)
   - **service_role key:** `eyJhbGc...` (different long string - KEEP SECRET!)

## Step 4: Run Database Migration

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `supabase_migration.sql` from your project
4. Paste into the SQL editor
5. Click "Run" (bottom right)
6. Verify success: Check **Database** → **Tables** - you should see:
   - user_settings
   - expenses
   - fixed_expenses
   - processed_files
   - shared_dashboards

## Step 5: Set Up Storage for File Uploads

1. Go to **Storage** in Supabase dashboard
2. Click "Create a new bucket"
3. Name it: `expense-files`
4. **Public bucket:** NO (keep private)
5. Click "Create bucket"
6. Click on the bucket name
7. Go to **Policies** tab
8. Click "New Policy" → "Custom policy"
9. Add this policy:

```sql
-- Allow authenticated users to upload to their own folder
CREATE POLICY "Users can upload own files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'expense-files'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to read their own files
CREATE POLICY "Users can read own files"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'expense-files'
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to delete their own files
CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'expense-files'
  AND (storage.foldername(name))[1] = auth.uid()::text
);
```

## Step 6: Configure Authentication

1. Go to **Authentication** → **Providers**
2. Enable **Email** provider (should be enabled by default)
3. Configure email settings:
   - Scroll to **Email Templates**
   - Customize "Confirm Signup" email (optional, use default for now)
   - **Site URL:** Will be your Render URL later (e.g., `https://moneymate.onrender.com`)
   - **Redirect URLs:** Add your Render URL + `/auth/callback`

## Step 7: Update Environment Variables

Create a `.env` file in your project root (DO NOT COMMIT TO GIT!):

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Flask Configuration
SECRET_KEY=generate_a_random_256_bit_string_here
FLASK_ENV=production
FLASK_DEBUG=false

# Optional: Email notifications (later)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your_email@gmail.com
# SMTP_PASSWORD=your_app_password
```

To generate a secure SECRET_KEY, run in Python:
```python
import secrets
print(secrets.token_hex(32))
```

## Step 8: Update .gitignore

Make sure these are in your `.gitignore`:

```
.env
*.db
__pycache__/
*.pyc
*.log
input_files/*.xlsx
input_files/*.xls
!input_files/.gitkeep
```

## Step 9: Test Locally

1. Install new dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   python app.py
   ```

3. Open http://localhost:5000
4. Create a test account
5. Upload a test Excel file
6. Verify data appears correctly

## Step 10: Verify Row-Level Security

Test that users can't see each other's data:

1. Create User A account → Upload expenses
2. Log out
3. Create User B account → Upload different expenses
4. Verify User B can't see User A's data
5. Check in Supabase dashboard → **Table Editor** → Expenses
   - You should see ALL expenses (you're admin)
   - But users via app should only see their own

## Troubleshooting

### "Connection refused" error
- Check your `SUPABASE_URL` in `.env` is correct
- Verify project is running in Supabase dashboard

### "Invalid API key" error
- Double-check `SUPABASE_ANON_KEY` is copied correctly
- Make sure there are no extra spaces or line breaks

### "Row-level security policy violation"
- RLS policies might not be enabled
- Re-run the migration SQL
- Check **Database** → **Policies** for each table

### Files not uploading
- Check storage bucket is named `expense-files`
- Verify storage policies are created
- Check user is authenticated (session exists)

## Next Steps

Once Supabase is working locally:
1. Push code to GitHub
2. Deploy to Render (see DEPLOYMENT.md)
3. Update Supabase **Site URL** with your Render URL
4. Test production deployment

## Cost Monitoring

Free tier limits:
- **Database:** 500 MB (thousands of users)
- **Storage:** 1 GB (thousands of Excel files if cleaned up regularly)
- **Bandwidth:** 2 GB (plenty for this app)
- **MAU:** 50,000 monthly active users

Monitor usage in **Settings** → **Usage**. You'll get email warnings before hitting limits.
