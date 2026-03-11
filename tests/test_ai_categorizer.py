"""
Tests for AICategorizer - keyword matching, corrections, and Ollama checks.
"""
import json
from unittest.mock import MagicMock, patch

import pytest


SAMPLE_CONFIG = {
    "categories": {
        "מזון": ["מסעדה", "סופר", "קפה"],
        "תחבורה": ["דלק", "חניה", "gett"],
        "בריאות": ["קופת חולים", "בית מרקחת"],
    },
    "ai": {
        "model": "llama3",
        "confidence_threshold": 0.7,
        "enable_learning": True,
        "user_corrections_file": "smart_categories.json",
    },
}


@pytest.fixture
def categorizer(tmp_path):
    """AICategorizer with temp config and corrections files."""
    config_file = tmp_path / "config_ai.json"
    config_file.write_text(json.dumps(SAMPLE_CONFIG), encoding="utf-8")

    corrections_file = tmp_path / "smart_categories.json"
    corrections_file.write_text("{}", encoding="utf-8")

    from ai_categorizer import AICategorizer

    cat = AICategorizer(str(config_file))
    cat.corrections_file = corrections_file
    cat.user_corrections = {}
    return cat


class TestKeywordMatchWithReason:
    def test_exact_keyword_match(self, categorizer):
        category, keyword = categorizer._keyword_match_with_reason("מסעדה אורה")
        assert category == "מזון"
        assert keyword == "מסעדה"

    def test_english_keyword_case_insensitive(self, categorizer):
        category, keyword = categorizer._keyword_match_with_reason("GETT ride")
        assert category == "תחבורה"
        assert keyword == "gett"

    def test_no_match_returns_none(self, categorizer):
        category, keyword = categorizer._keyword_match_with_reason("חנות לא מוכרת")
        assert category is None
        assert keyword is None

    def test_short_keyword_requires_whole_word(self, categorizer):
        category, _ = categorizer._keyword_match_with_reason("תחנת דלק")
        assert category == "תחבורה"


class TestCategorize:
    def test_user_correction_takes_priority(self, categorizer):
        categorizer.user_corrections["רחבי גז"] = "תחבורה"
        category, confidence, method, _ = categorizer.categorize("רחבי גז")
        assert category == "תחבורה"
        assert method == "user_correction"
        assert confidence == 1.0

    def test_keyword_match_fallback(self, categorizer):
        category, confidence, method, _ = categorizer.categorize("סופרמרקט מגה")
        assert category == "מזון"
        assert method == "keyword"
        assert confidence > 0

    def test_unknown_falls_back_to_other(self, categorizer):
        category, _, method, _ = categorizer.categorize("חנות לא מוכרת")
        assert category == "אחר"
        assert method == "default"


class TestSaveCorrection:
    def test_correction_is_persisted(self, categorizer):
        categorizer._save_correction("קפה נמרוד", "מזון")
        assert categorizer.user_corrections["קפה נמרוד"] == "מזון"

    def test_correction_affects_future_categorization(self, categorizer):
        categorizer._save_correction("ביפר חנות", "אחר")
        category, _, method, _ = categorizer.categorize("ביפר חנות")
        assert category == "אחר"
        assert method == "user_correction"


class TestCheckOllamaAvailable:
    def test_returns_false_on_connection_error(self, categorizer):
        import requests

        with patch("requests.get", side_effect=requests.ConnectionError()):
            assert categorizer.check_ollama_available() is False

    def test_returns_false_on_timeout(self, categorizer):
        import requests

        with patch("requests.get", side_effect=requests.Timeout()):
            assert categorizer.check_ollama_available() is False

    def test_returns_true_when_model_found(self, categorizer):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3"}]}
        with patch("requests.get", return_value=mock_resp):
            assert categorizer.check_ollama_available() is True

    def test_returns_false_when_model_not_in_list(self, categorizer):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "mistral"}]}
        with patch("requests.get", return_value=mock_resp):
            assert categorizer.check_ollama_available() is False
