# MoneyMate

MoneyMate is a Flask web app for importing credit card statements, categorizing expenses, and reviewing monthly spending with a bilingual Hebrew/English interface.

## Preview

[![MoneyMate demo preview](docs/preview.png)](https://tomsand93.github.io/money-mate/marketing-demo.html)

[View live demo →](https://tomsand93.github.io/money-mate/marketing-demo.html)

## What It Does

- Imports `.xlsx` and `.xls` expense statements
- Categorizes transactions with keyword rules and optional AI assistance
- Stores data in Supabase, with local SQLite fallback for development
- Provides dashboards, reports, category views, and transaction review flows
- Supports user authentication with Supabase Auth

## Repository Layout

```text
money-mate/
  app.py                   Flask entry point and top-level routes
  auth.py                  Authentication helpers and route guards
  extensions.py            Shared singleton initialization
  db_utils.py              Request-scoped database selection
  database.py              Local SQLite implementation
  supabase_db.py           Supabase-backed database implementation
  expense_processor.py     Statement parsing and normalization
  ai_categorizer.py        Rule-based and AI-assisted categorization
  financial_analyzer.py    Spending analysis and recommendation logic
  report_generator.py      Monthly report generation
  i18n.py                  Hebrew/English UI strings
  blueprints/              Feature routes
  templates/               Jinja templates
  static/                  CSS assets
  scripts/                 Small maintenance/demo scripts
  tests/                   Pytest suite
  config.json              Base category configuration
  config_ai.json           Base AI and analysis configuration
  smart_categories.json    Base smart-rule examples
  supabase_migration.sql   Database schema for Supabase
  .env.example             Environment variable template
  Dockerfile               Container deployment
  Procfile                 Render/Gunicorn entry
```

## Setup

### Prerequisites

- Python 3.10+
- A Supabase project for production-style auth and storage

### Install

```bash
pip install -r requirements.txt
```

### Environment

Copy `.env.example` to `.env` and provide real values:

```bash
cp .env.example .env
```

Required variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=replace-with-a-random-secret
```

### Optional Local Overrides

The app prefers local override files when they exist:

- `config.local.json`
- `config_ai.local.json`
- `smart_categories.local.json`

Create them by copying the committed base files:

```bash
cp config.json config.local.json
cp config_ai.json config_ai.local.json
cp smart_categories.json smart_categories.local.json
```

These local override files are gitignored so personal categories and learned rules stay out of the repository.

### Database

For Supabase, apply `supabase_migration.sql` to your project.

For local development fallback, the app will create `expenses.db` as needed.

## Run

```bash
python app.py
```

Open `http://localhost:5000`.

## Tests

```bash
pytest tests/ -v
```

The test suite uses mocked Supabase clients and does not require a live Supabase project.

## Utility Scripts

- `python scripts/seed_demo.py`: create a small demo SQLite database
- `python scripts/check_db.py`: inspect the local SQLite database contents

## Runtime Directories

These directories are intentionally present but should not be committed with user data:

- `input_files/`
- `reports/`

They are kept in the repo only as placeholders via `.gitkeep`.

## Deployment

The repository includes `Dockerfile`, `Procfile`, and a GitHub Actions workflow for linting and tests.
