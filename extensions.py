"""
Shared application extensions and singletons.
Imported by blueprints to avoid circular imports.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MONTH_NAMES_HE = {
    1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
    5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
    9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
}

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_config_path(base_path: str) -> str:
    """
    Return path to config file, preferring local override if it exists.
    For 'config.json' -> checks 'config.local.json' first.
    """
    local_path = base_path.replace('.json', '.local.json')
    if Path(local_path).exists():
        return local_path
    return base_path


def load_config(path: str = 'config_ai.json') -> dict:
    actual_path = get_config_path(path)
    with open(actual_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Lazily-initialised singletons — call init_extensions(app) from create_app()
config = None
processor = None
ai_categorizer = None
financial_analyzer = None


def init_extensions():
    """Initialise all shared singletons. Must be called once after create_app()."""
    global config, processor, ai_categorizer, financial_analyzer

    from expense_processor import ExpenseProcessor
    from ai_categorizer import AICategorizer
    from financial_analyzer import FinancialAnalyzer

    config = load_config()
    processor = ExpenseProcessor()
    ai_categorizer = AICategorizer()
    financial_analyzer = FinancialAnalyzer()

    logger.info("Extensions initialised")
