# Expance — Personal Expense Tracker

A full-stack web application for managing and analyzing personal credit card expenses. Upload monthly Excel statements, automatically categorize transactions with AI, and visualize spending through interactive dashboards.

## Features

- **Excel Import** — Auto-detects and parses Israeli credit card statement formats (multiple card support)
- **AI Categorization** — Classifies transactions by merchant name using a local Ollama model with a learning loop
- **Interactive Dashboard** — Monthly spending breakdown, savings rate, category charts
- **Savings Dashboard** — Track savings goals and monthly income vs. expenses
- **Transaction Review** — Manually correct categories, bulk-update, or re-run AI classification
- **Category View** — Drill down into any spending category across months
- **Installment Tracking** — Detects and groups installment payments
- **Multi-language** — Full Hebrew / English UI (Flask-Babel)
- **Authentication** — Supabase-based user auth with signup, login, and password reset
- **Reports** — Per-month HTML and Excel reports

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3 |
| Database | Supabase (PostgreSQL) + local SQLite fallback |
| Auth | Supabase Auth |
| AI | Ollama (local LLM) via REST API |
| Frontend | Jinja2 templates, vanilla JS, Chart.js |
| i18n | Flask-Babel (Hebrew + English) |
| Deployment | Gunicorn, Docker, Render-ready |

## Project Structure

```
expance/
├── app.py                  # Flask app — routes & request handling
├── auth.py                 # Authentication blueprint (Supabase)
├── supabase_db.py          # Supabase database layer
├── database.py             # Local SQLite database layer
├── expense_processor.py    # Excel parsing & transaction normalization
├── ai_categorizer.py       # Ollama AI categorization + learning loop
├── financial_analyzer.py   # Spending analytics & statistics
├── report_generator.py     # Report generation (HTML/Excel)
├── performance_utils.py    # Caching & request performance helpers
├── i18n.py                 # Bilingual string definitions (HE/EN)
├── config.json             # Category keywords configuration
├── config_ai.json          # AI model configuration
├── smart_categories.json   # Learned category mappings
├── supabase_migration.sql  # Database schema
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS & JS assets
├── scripts/                # Utility scripts (DB check, seed data)
├── input_files/            # Place Excel statements here (gitignored)
└── reports/                # Generated reports output (gitignored)
```

## Getting Started

### Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com) project (free tier works)
- [Ollama](https://ollama.ai) running locally for AI categorization (optional)

### 1. Clone & Install

```bash
git clone <repo-url>
cd expance
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=any-random-string
```

### 3. Set Up the Database

Run the migration on your Supabase project:

```bash
# Paste the contents of supabase_migration.sql into the Supabase SQL editor
# or use the Supabase CLI
```

### 4. Run

```bash
python app.py
```

Visit `http://localhost:5000`. Sign up for an account, then upload your first Excel statement from the Upload page.

### Docker

```bash
docker build -t expance .
docker run -p 5000:5000 --env-file .env expance
```

## Usage

1. **Upload** — Go to `/upload` and drop in your credit card Excel file (`.xlsx`)
2. **Review** — Check `/review_transactions` to correct any misclassified transactions
3. **Dashboard** — View `/` for the monthly spending overview with charts
4. **Reports** — Browse past months at `/reports`

## Configuration

Edit `config.json` to add keyword-to-category mappings:

```json
{
  "categories": {
    "Supermarket": ["shufersal", "rami levy", "victory"],
    "Restaurants": ["mcdonalds", "burger", "pizza"]
  }
}
```

The AI model learns from manual corrections and stores mappings in `smart_categories.json`.

## Deployment

The app is Render-ready. Set environment variables in your Render dashboard and deploy directly from this repository. The `Procfile` and `Dockerfile` are included.

## License

MIT
