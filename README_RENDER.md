# Deploying MoneyMate to Render (simple guide)

This guide helps you deploy your local MoneyMate Flask app to Render as a Web Service.

1. Create a Render account and connect your GitHub repository.

2. In Render, create a new **Web Service** and point it to your repo and branch.

3. Build & Start commands (Render's default build environment is fine):
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn -b 0.0.0.0:$PORT app:app

4. Environment variables (add these in Render dashboard -> Environment):
   - SECRET_KEY: (a long random string)
   - BASIC_AUTH_USERNAME: demo
   - BASIC_AUTH_PASSWORD: demo123
   - BASIC_AUTH_FORCE: true
   - FLASK_DEBUG: false

5. Database: SQLite works for simple testing, but it's ephemeral on cloud services; use Postgres for persistence.
   - If you need persistence: add a Postgres database (Render has an add-on) and switch to Postgres later.

6. Deploy: Render will build and start the app. You will get a public HTTPS endpoint.

Notes & Recommendations:
- For public or multi-user use, migrate to Postgres and add authentication.
- Sanitize or seed demo data before sharing publicly.
- Consider using a process manager (gunicorn is used here) and enable HTTPS.
