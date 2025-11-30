# Quick Testing Guide - MoneyMate Multi-User Version

This guide helps you test the newly integrated multi-user MoneyMate app locally before deploying.

---

## Prerequisites Checklist

Before you start, make sure you have:

- [x] Created a Supabase account at https://supabase.com
- [x] Created a new Supabase project
- [x] Ran the `supabase_migration.sql` in your Supabase SQL Editor
- [x] Created a `.env` file with your Supabase credentials
- [ ] Installed all Python dependencies

---

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- supabase (for database)
- python-dotenv (for environment variables)
- flask-babel (for i18n)
- All other production dependencies

---

## Step 2: Verify Your .env File

Make sure your `.env` file looks like this:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (different from ANON_KEY)

# Flask Configuration
SECRET_KEY=your_random_256_bit_string_here
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_RUN_HOST=127.0.0.1
FLASK_RUN_PORT=5000
```

**Generate a SECRET_KEY** if you haven't:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 3: Run the Application

```bash
python app.py
```

You should see:
```
[INFO] ... Starting MoneyMate on 127.0.0.1:5000 (debug=True)
[INFO] ... AI Categorization: Not available (keyword-only)
```

**Note:** The "AI not available" message is expected - we made AI optional!

---

## Step 4: Test User Registration

1. Open http://localhost:5000 in your browser
2. You'll be redirected to the **login page** (since you're not authenticated)
3. Click **"צור חשבון"** (Create Account) or **"Sign Up"**
4. Fill in the signup form:
   - Email: test@example.com
   - Password: test123
   - Confirm Password: test123
5. Click **"Create Account"**
6. You should see: **"Registration successful! Please check your email to confirm your account."**

**Important:** Supabase will send a confirmation email. In development, you can:
- Check your email and click the confirmation link, OR
- Go to your Supabase dashboard → Authentication → Users → Click the user → Click "Confirm Email"

---

## Step 5: Test Login

1. After confirming your email, go back to http://localhost:5000
2. Enter your credentials:
   - Email: test@example.com
   - Password: test123
3. Click **"התחבר"** (Login)
4. You should be redirected to the **onboarding page**

---

## Step 6: Complete Onboarding

1. Fill in your monthly income (e.g., 15000)
2. Add a fixed expense:
   - Description: "Rent"
   - Amount: 5000
   - Category: "חשבונות ומנויים"
   - Type: "צורך" (Need)
3. Click **"השלם הגדרה"** (Complete Setup)
4. You should see a success message and be redirected to the dashboard

---

## Step 7: Test File Upload

1. Click **"העלאת קובץ"** (Upload File) in the navigation
2. Enter the path to your Excel files folder (e.g., `C:\Users\Tom1\Desktop\expance\input_files`)
3. Click **"עבד קבצים"** (Process Files)
4. You should see:
   - "✅ עובדו בהצלחה X קבצים עם Y עסקאות" (X files processed successfully with Y transactions)
   - **No AI message** (since we made it optional)

---

## Step 8: Verify Multi-User Isolation

To test that users can't see each other's data:

1. **Logout** from the first account
2. **Create a second account** (test2@example.com / test123)
3. Confirm the email and login
4. Complete onboarding with **different data**
5. Upload **different files**
6. Verify that you **only see data from test2**, not test1

---

## Step 9: Test Language Switching

1. In any page, look for the language switcher:
   - **עברית** | **English**
2. Click **"English"**
3. The interface should switch to English
4. Click **"עברית"**
5. The interface should switch back to Hebrew

---

## Step 10: Test Data Export (GDPR)

1. Go to **Settings** (הגדרות)
2. Scroll to **"Data Management"** section
3. Click **"Export All Data"** (ייצוא כל הנתונים)
4. You should download a JSON file with all your data
5. Open the JSON file and verify it contains:
   - Your settings
   - Your expenses
   - Your fixed expenses

---

## Step 11: Test Account Deletion (GDPR)

**WARNING: This will delete all data!**

1. In Settings, scroll to **"Delete Account"**
2. Type **"DELETE"** in the confirmation field
3. Click **"Delete Account"**
4. You should be logged out
5. Try to login again - you should get an error (account doesn't exist)

---

## Common Issues & Solutions

### Issue: "Missing Supabase credentials!"

**Solution:** Make sure your `.env` file exists and has the correct `SUPABASE_URL` and `SUPABASE_ANON_KEY`.

```bash
# Verify .env file exists
ls .env

# Check contents
cat .env
```

---

### Issue: "Row-level security policy violation"

**Solution:** Make sure you ran the full `supabase_migration.sql` in your Supabase SQL Editor. Check:

1. Go to Supabase Dashboard → SQL Editor
2. Run this query to verify tables exist:
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

You should see: `user_settings`, `expenses`, `fixed_expenses`, `processed_files`, `shared_dashboards`

3. Check RLS policies exist:
```sql
SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';
```

You should see multiple policies for each table.

---

### Issue: "ModuleNotFoundError: No module named 'supabase'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

---

### Issue: "Invalid email or password" when logging in

**Solution:** Check if you confirmed your email:

1. Go to Supabase Dashboard → Authentication → Users
2. Find your user
3. Check if "Email Confirmed" is **true**
4. If not, click the user → Click "Confirm Email"

---

### Issue: "AI Categorizer not available" warning

**Solution:** This is **expected and correct**! We made AI optional. The app will use keyword-based categorization instead.

If you want to enable AI:
1. Install Ollama
2. Pull a model: `ollama pull llama2`
3. The app will automatically detect and use it

---

## Expected Behavior Summary

✅ **What SHOULD work:**
- User registration and email confirmation
- Login/logout
- Multi-user data isolation (users can't see each other's data)
- Onboarding flow
- File upload and processing (without AI)
- Dashboard with financial analysis
- Savings dashboard with charts
- Language switching (Hebrew ↔ English)
- Data export (download JSON)
- Account deletion

✅ **What's OPTIONAL:**
- AI categorization (requires Ollama)
- Shared dashboards (UI pending)

---

## Next Steps After Testing

Once everything works locally:

1. **Push to GitHub** (make sure .env is NOT committed!)
2. **Deploy to Render** (see deployment guide)
3. **Test in production**
4. **Share with beta users**

---

## Need Help?

If you encounter issues:

1. Check the terminal for error messages
2. Check browser console (F12) for JavaScript errors
3. Check Supabase logs (Dashboard → Logs)
4. Verify your .env file has correct credentials
5. Make sure all database migrations ran successfully

---

Happy testing! 🎉
