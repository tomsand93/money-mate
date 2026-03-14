# MoneyMate — Personal Expense Tracker

A full-stack web application for managing and analyzing personal credit card expenses. Upload monthly Excel statements, automatically categorize transactions with AI, and visualize spending through interactive dashboards.

![MoneyMate Demo](assets/demo.gif)

## Live Demo

**[→ View the live demo](https://tomsand93.github.io/money-mate/marketing-demo_new.html)**

> Hosted via GitHub Pages. If the link isn't live yet, go to **Settings → Pages** and set the source to `master` branch, `/ (root)`.

## Features

- **Excel Import** — Auto-detects and parses Israeli credit card statement formats (multiple card support)
- **AI Categorization** — Classifies transactions by merchant name with smart keyword matching
- **Interactive Dashboard** — Monthly spending breakdown, savings rate, category charts
- **Savings Dashboard** — Track savings goals and monthly income vs. expenses
- **Transaction Review** — Manually correct categories, bulk-update, or re-run AI classification
- **Category View** — Drill down into any spending category across months
- **Installment Tracking** — Detects and groups installment payments
- **Multi-language** — Full Hebrew / English UI
- **Authentication** — Supabase-based user auth with signup, login, and password reset
- **Reports** — Per-month HTML and Excel reports

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3, Blueprints |
| Database | Supabase (PostgreSQL) + local SQLite fallback |
| Auth | Supabase Auth |
| Frontend | Jinja2 templates, vanilla JS, Chart.js |
| i18n | Flask-Babel (Hebrew + English) |
| Testing | pytest, mocked Supabase |
| CI/CD | GitHub Actions (flake8 + pytest) |

## Project Structure

```
money-mate/
├── app.py                  # Flask app factory — auth routes + dashboard
├── auth.py                 # Supabase auth decorators (@login_required, @guest_only)
├── extensions.py           # Shared singletons (config, processor, AI, analyzer)
├── db_utils.py             # Request-scoped DB helper (get_db())
├── blueprints/             # Modular route blueprints
│   ├── admin.py            # Settings, onboarding, AI API
│   ├── expenses.py         # Expense CRUD, review, bulk actions
│   ├── reports.py          # Reports, savings dashboard, category view
│   └── uploads.py          # File upload & parsing
├── supabase_db.py          # Supabase database layer
├── database.py             # Local SQLite database layer
├── expense_processor.py    # Excel parsing & transaction normalization
├── ai_categorizer.py       # Smart keyword categorization + learning loop
├── financial_analyzer.py   # Spending analytics & statistics
├── report_generator.py     # Report generation (HTML/Excel)
├── i18n.py                 # Bilingual string definitions (HE/EN)
├── config.json             # Category keywords (generic, committed)
├── config.local.json       # Your personal categories (gitignored) ← USE THIS
├── config_ai.json          # AI config (generic, committed)
├── config_ai.local.json    # Your personal AI config (gitignored) ← USE THIS
├── smart_categories.json   # Learned rules (generic, committed)
├── smart_categories.local.json # Your personal rules (gitignored) ← USE THIS
├── supabase_migration.sql  # Database schema
├── marketing-demo_new.html # Standalone marketing page (open in browser)
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS & JS assets
├── tests/                  # Pytest tests (53 tests)
│   ├── conftest.py         # Test fixtures (Supabase mock)
│   ├── test_upload_parsing.py
│   ├── test_ai_categorizer.py
│   ├── test_expense_crud.py
│   └── test_api_endpoints.py
├── .github/workflows/      # CI/CD
│   └── ci.yml              # flake8 + pytest
└── scripts/                # Utility scripts
```

## Getting Started

### Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com) project (free tier works)

### 1. Clone & Install

```bash
git clone https://github.com/tomsand93/money-mate.git
cd money-mate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=any-random-string
```

### 3. Set Up the Database

Run the migration on your Supabase project:

```bash
# Paste the contents of supabase_migration.sql into the Supabase SQL editor
```

### 4. Configure Your Categories (Optional)

The app comes with generic category examples. To add your personal merchants and keywords:

```bash
cp config.json config.local.json
cp config_ai.json config_ai.local.json
```

Edit `config.local.json` to add your personal keywords:

```json
{
  "categories": {
    "ספורט וכושר": ["טיפוס", "climbing", "my_gym_name"],
    "אוכל בחוץ": ["my_favorite_cafe", "restaurant_name"]
  }
}
```

**Important:** `.local.json` files are gitignored — your personal data stays local.

### 5. Run

```bash
python app.py
```

Visit `http://localhost:5000`. Sign up for an account, then upload your first Excel statement from the Upload page.

### 6. Run Tests

```bash
pytest
```

## Usage

1. **Upload** — Go to `/upload` and drop in your credit card Excel file (`.xlsx`)
2. **Review** — Check `/review_transactions` to correct any misclassified transactions
3. **Dashboard** — View `/` for the monthly spending overview with charts
4. **Reports** — Browse past months at `/reports`

## Configuration

### Local Config Overrides

The app automatically prefers `*.local.json` files over the base configs:

| File | Git Status | Purpose |
|------|------------|---------|
| `config.json` | ✅ Committed | Generic example categories |
| `config.local.json` | ❌ Gitignored | Your personal categories |
| `config_ai.json` | ✅ Committed | Generic AI settings |
| `config_ai.local.json` | ❌ Gitignored | Your personal AI settings |
| `smart_categories.json` | ✅ Committed | Generic learned rules |
| `smart_categories.local.json` | ❌ Gitignored | Your personal learned rules |

## Deployment

The app is Render-ready. Set environment variables in your Render dashboard and deploy directly from this repository. The `Procfile` and `Dockerfile` are included.

## License

MIT
