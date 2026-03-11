"""
Tests for ExpenseProcessor parsing helpers and installment detection.
"""
import pandas as pd

from expense_processor import ExpenseProcessor


SAMPLE_CATEGORIES = {
    "מזון": ["מסעדה", "סופר", "קפה"],
    "תחבורה": ["דלק", "חניה", "gett"],
    "בריאות": ["קופת חולים", "בית מרקחת"],
}

COLUMN_VARIATIONS = {
    "purchase_date": ["תאריך רכישה", "תאריך עסקה", "purchase date", "date"],
    "business_name": ["שם בית עסק", "בית עסק", "business name", "merchant"],
    "billing_amount": ["סכום חיוב", "סכום לחיוב", "billing amount", "amount"],
    "transaction_amount": ["סכום עסקה", "transaction amount"],
    "transaction_currency": ["מטבע עסקה", "transaction currency", "currency"],
    "billing_currency": ["מטבע חיוב", "billing currency"],
    "voucher_number": ["מס' שובר", "voucher number", "reference number"],
    "additional_details": ["פירוט נוסף", "additional details", "details"],
}


def _make_processor(categories=None):
    ep = ExpenseProcessor.__new__(ExpenseProcessor)
    ep.config = {"categories": categories or SAMPLE_CATEGORIES}
    ep.categories = ep.config["categories"]
    ep.column_variations = COLUMN_VARIATIONS
    return ep


class TestDetectInstallment:
    def setup_method(self):
        self.ep = _make_processor()

    def test_hebrew_pattern(self):
        payment, total = self.ep._detect_installment("רכישה תשלום 3 מתוך 12")
        assert payment == 3
        assert total == 12

    def test_slash_pattern(self):
        payment, total = self.ep._detect_installment("AMAZON 4/10")
        assert payment == 4
        assert total == 10

    def test_english_of_pattern(self):
        payment, total = self.ep._detect_installment("payment 2 of 6 NETFLIX")
        assert payment == 2
        assert total == 6

    def test_no_pattern_returns_none(self):
        payment, total = self.ep._detect_installment("סופרמרקט שפע")
        assert payment is None
        assert total is None

    def test_nan_input_returns_none(self):
        payment, total = self.ep._detect_installment(float("nan"))
        assert payment is None
        assert total is None

    def test_implausible_slash_ignored(self):
        payment, total = self.ep._detect_installment("20/10/2023")
        if payment is not None:
            assert payment <= total
            assert total <= 60


class TestCategorizeExpense:
    def setup_method(self):
        self.ep = _make_processor()

    def test_keyword_substring_match(self):
        result = self.ep.categorize_expense("סופר-פארם")
        assert result["category"] == "מזון"
        assert result["confidence_score"] > 0

    def test_english_keyword_case_insensitive(self):
        result = self.ep.categorize_expense("GETT taxi")
        assert result["category"] == "תחבורה"

    def test_unknown_business_returns_other(self):
        result = self.ep.categorize_expense("חנות לא מוכרת XYZ")
        assert result["category"] == "אחר"
        assert result["confidence_score"] == 0.0

    def test_empty_string_returns_other(self):
        result = self.ep.categorize_expense("")
        assert result["category"] == "אחר"

    def test_nan_value_returns_other(self):
        result = self.ep.categorize_expense(float("nan"))
        assert result["category"] == "אחר"

    def test_result_has_required_keys(self):
        result = self.ep.categorize_expense("דלק פז")
        assert {"category", "confidence", "confidence_score", "matched_keywords"} <= result.keys()


class TestFindColumn:
    def setup_method(self):
        self.ep = _make_processor()

    def test_exact_hebrew_match(self):
        df = pd.DataFrame(columns=["תאריך רכישה", "שם בית עסק", "סכום חיוב"])
        assert self.ep._find_column(df, "purchase_date") == "תאריך רכישה"
        assert self.ep._find_column(df, "billing_amount") == "סכום חיוב"

    def test_exact_english_match(self):
        df = pd.DataFrame(columns=["date", "merchant", "amount"])
        assert self.ep._find_column(df, "purchase_date") == "date"

    def test_case_insensitive_match(self):
        df = pd.DataFrame(columns=["Purchase Date", "Business Name", "Amount"])
        assert self.ep._find_column(df, "purchase_date") == "Purchase Date"

    def test_no_matching_column_returns_none(self):
        df = pd.DataFrame(columns=["col_a", "col_b", "col_c"])
        assert self.ep._find_column(df, "purchase_date") is None

    def test_unknown_standard_name_returns_none(self):
        df = pd.DataFrame(columns=["date", "amount"])
        assert self.ep._find_column(df, "nonexistent_field") is None
