# Deployment Options - Share MoneyMate with Friends

You have two options to share your app:

## Option 1: Quick Share with ngrok (5 minutes)

**Best for:** Testing with a friend immediately, temporary sharing

**Pros:**
- Setup in 5 minutes
- Works immediately
- No account needed

**Cons:**
- URL changes every time you restart
- Your computer must stay on
- Limited to 1 free tunnel at a time

### Steps:

1. **Download ngrok**
   ```bash
   # Go to: https://ngrok.com/download
   # Or use winget:
   winget install ngrok
   ```

2. **Start your app locally**
   ```bash
   python app.py
   ```
   App should be running on http://localhost:5000

3. **In a NEW terminal, start ngrok**
   ```bash
   ngrok http 5000
   ```

4. **Copy the public URL**
   You'll see something like:
   ```
   Forwarding   https://abc123.ngrok-free.app -> http://localhost:5000
   ```

5. **Share the URL**
   Send `https://abc123.ngrok-free.app` to your friend!

**⚠️ Important:**
- Keep both terminals running (app + ngrok)
- Don't close your computer
- URL expires when you stop ngrok
- First-time visitors see an ngrok warning page (click "Visit Site")

---

## Option 2: Deploy to Render (Free, Permanent)

**Best for:** Permanent deployment, multiple users, always-on

**Pros:**
- Permanent URL (moneymate.onrender.com)
- Always available (24/7)
- Free tier available
- Automatic HTTPS
- Professional setup

**Cons:**
- Takes 15-20 minutes to set up
- Free tier sleeps after 15 minutes of inactivity (wakes up in ~30 seconds)
- Need to create account

### Prerequisites Checklist:

Before deploying, make sure you have:
- ✅ `.env` file with all required variables
- ✅ `supabase_migration.sql` executed in Supabase
- ✅ App tested locally and working
- ✅ Git repository initialized

### Steps:

#### 1. Create Required Files (Already Done!)

You already have these files in your project:
- `Procfile` - tells Render how to start your app
- `requirements.txt` - lists all dependencies
- `README_RENDER.md` - deployment documentation

#### 2. Prepare Your Repository

```bash
# Make sure all files are committed
git add .
git commit -m "Ready for Render deployment"

# Create a GitHub repository (if you haven't already)
# Go to https://github.com/new
# Name it: moneymate
# Make it PRIVATE (contains sensitive app logic)
# Don't initialize with README (you already have one)

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/moneymate.git
git branch -M main
git push -u origin main
```

#### 3. Create Render Account

1. Go to https://render.com
2. Click **Get Started**
3. Sign up with GitHub (easiest)
4. Authorize Render to access your repositories

#### 4. Create New Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repository `moneymate`
3. Click **Connect**

#### 5. Configure the Service

**Basic Settings:**
- **Name:** `moneymate` (or whatever you want)
- **Region:** Choose closest to you (e.g., Frankfurt for Israel)
- **Branch:** `main`
- **Root Directory:** (leave empty)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

**Advanced Settings - Environment Variables:**

Click **Add Environment Variable** and add each of these:

| Key | Value | Notes |
|-----|-------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | From your .env |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJI...` | From your .env |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJI...` | From your .env |
| `SECRET_KEY` | `your-secret-key` | From your .env |
| `FLASK_ENV` | `production` | Set this to production |
| `PYTHONUNBUFFERED` | `1` | Better logging |

**⚠️ IMPORTANT:**
- Keep `SUPABASE_SERVICE_KEY` secure
- Don't share these values publicly
- Render encrypts environment variables

**Plan Selection:**
- Choose **Free** tier
- 750 hours/month free
- Sleeps after 15 min inactivity
- Good for personal use and small groups

#### 6. Deploy!

1. Click **Create Web Service**
2. Wait 5-10 minutes for deployment
3. Watch the logs - you'll see:
   ```
   Building...
   Installing dependencies...
   Starting gunicorn...
   ✅ Deploy successful!
   ```

#### 7. Get Your URL

Once deployed, you'll get a URL like:
```
https://moneymate.onrender.com
```

**Share this with your friends!**

#### 8. Test Your Deployment

1. Visit your Render URL
2. Create a test account
3. Complete onboarding
4. Upload a file
5. Verify everything works

### Common Render Issues:

**Issue: App crashes on startup**
```bash
# Check logs in Render dashboard
# Common causes:
# 1. Missing environment variables
# 2. Wrong Supabase credentials
# 3. Database migration not run
```
**Fix:** Verify all environment variables are set correctly

**Issue: "Application failed to start"**
```bash
# Check the start command is exactly:
gunicorn app:app
```

**Issue: 502 Bad Gateway**
- App is starting up (wait 30 seconds)
- Or app crashed (check logs)

**Issue: Slow first load**
- Free tier sleeps after 15 min inactivity
- First request wakes it up (~30-60 seconds)
- Subsequent requests are fast

### Keep Your App Awake (Optional)

Free tier sleeps after inactivity. To keep it awake:

**Option A: Use UptimeRobot (Free)**
1. Go to https://uptimerobot.com
2. Create free account
3. Add monitor:
   - Type: HTTP(S)
   - URL: Your Render URL
   - Interval: 5 minutes
4. This pings your app every 5 minutes to keep it awake

**Option B: Upgrade to Paid Tier**
- $7/month for always-on instance
- No sleep delays
- Better for production use

---

## Comparison Table

| Feature | ngrok (Quick) | Render (Production) |
|---------|---------------|---------------------|
| Setup Time | 5 minutes | 15-20 minutes |
| Cost | Free | Free tier available |
| Availability | When your PC is on | 24/7 |
| URL | Changes each restart | Permanent |
| HTTPS | Yes | Yes |
| Custom Domain | No | Yes (paid) |
| Professional | No | Yes |
| Scalability | No | Yes |
| Best For | Quick testing | Real deployment |

---

## Recommended Approach

1. **First:** Test with ngrok to share with 1-2 friends immediately
2. **Then:** Deploy to Render for permanent access
3. **Later:** Consider custom domain if needed

---

## Security Checklist Before Sharing

Before you share your app publicly:

- ✅ All sensitive data in `.env` (not hardcoded)
- ✅ `.env` file in `.gitignore`
- ✅ Supabase RLS policies enabled
- ✅ No test/debug accounts with weak passwords
- ✅ Secret key is random and secure
- ✅ Repository is PRIVATE on GitHub
- ✅ AI categorization is optional (not required)

---

## Next Steps

**Choose your path:**

### Path A: Quick Test (ngrok)
1. Run `python app.py`
2. In new terminal: `ngrok http 5000`
3. Share the ngrok URL with your friend

### Path B: Production Deploy (Render)
1. Commit all changes to git
2. Push to GitHub (private repo)
3. Follow Render deployment steps above
4. Share your permanent URL

**Need help?** Check the logs:
- **Local:** Terminal output
- **Render:** Dashboard → Logs tab
- **Supabase:** Dashboard → Logs

---

**Ready to deploy?** Start with ngrok for immediate testing, then move to Render for permanent hosting!
