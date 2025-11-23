"""
AI-powered expense categorizer using Ollama
"""
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

import json
import requests
from typing import Dict, Tuple, Optional
from pathlib import Path


class AICategorizer:
    def __init__(self, config_path: str = 'config_ai.json'):
        """Initialize AI categorizer with config"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.categories = list(self.config['categories'].keys())
        self.ai_config = self.config['ai']
        self.ollama_url = "http://localhost:11434/api/generate"

        # Load user corrections (learning database)
        self.corrections_file = Path(self.ai_config['user_corrections_file'])
        self.user_corrections = self._load_corrections()

    def _load_corrections(self) -> Dict[str, str]:
        """Load user corrections from file"""
        if self.corrections_file.exists():
            with open(self.corrections_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_correction(self, business_name: str, category: str):
        """Save user correction for future learning and update keywords dynamically"""
        # Save to user corrections
        self.user_corrections[business_name.lower()] = category
        with open(self.corrections_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_corrections, f, ensure_ascii=False, indent=2)

        # Extract meaningful keywords from business name and add to category
        if self.ai_config.get('enable_learning', True):
            self._learn_from_correction(business_name, category)

    def _learn_from_correction(self, business_name: str, category: str):
        """Extract keywords from business name and add to category keywords"""
        # Split business name into words
        words = business_name.lower().split()

        # Filter out common non-meaningful words
        stop_words = {'בע"מ', 'בעמ', 'ltd', 'inc', 'ש.ע', 'שע', 'חנות', 'סניף', 'מס', 'מספר'}

        # Get current keywords for this category
        current_keywords = set(k.lower() for k in self.config['categories'].get(category, []))

        # Find new meaningful keywords (words that aren't already keywords)
        new_keywords = []
        for word in words:
            # Clean the word
            word = word.strip('.,;:!?()"\'')

            # Skip if too short, is a stop word, or already exists
            if len(word) < 3 or word in stop_words or word in current_keywords:
                continue

            # Check if this word appears in the business name of other expenses with same category
            # For now, we'll add it if it's a substantial word
            if len(word) >= 4:  # Only add words with 4+ characters
                new_keywords.append(word)

        # Add new keywords to config if any found
        if new_keywords:
            config_path = Path('config_ai.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Add new keywords to the category
            if category not in config['categories']:
                config['categories'][category] = []

            # Add only unique new keywords
            for keyword in new_keywords:
                if keyword not in [k.lower() for k in config['categories'][category]]:
                    config['categories'][category].append(keyword)
                    print(f"🎓 למדתי מילת מפתח חדשה: '{keyword}' -> {category}")

            # Save updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # Reload config in memory
            self.config = config

    def categorize(self, business_name: str, amount: float = None,
                   ask_user_callback=None) -> Tuple[str, float, str, str]:
        """
        Categorize expense using smart keyword matching (no Ollama/AI needed!)

        Returns:
            Tuple[str, float, str, str]: (category, confidence, method, reason)
        """
        # First check if we have a user correction for this exact business
        if business_name.lower() in self.user_corrections:
            category = self.user_corrections[business_name.lower()]
            return category, 1.0, "user_correction", f"סווג ידנית ע\"י המשתמש כ-'{category}'"

        # Use enhanced keyword matching - works offline!
        keyword_category, matched_keyword = self._keyword_match_with_reason(business_name)
        if keyword_category:
            return keyword_category, 0.95, "keyword", f"זוהה לפי מילת המפתח: '{matched_keyword}'"

        # Fallback to "אחר" if nothing matches
        return "אחר", 0.5, "default", "לא נמצאה התאמה - סווג כ'אחר'"

    def _keyword_match(self, business_name: str) -> Optional[str]:
        """Traditional keyword matching as fallback"""
        business_lower = business_name.lower()

        for category, keywords in self.config['categories'].items():
            for keyword in keywords:
                if keyword.lower() in business_lower:
                    return category
        return None

    def _keyword_match_with_reason(self, business_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Keyword matching that returns the matched keyword"""
        business_lower = business_name.lower()

        for category, keywords in self.config['categories'].items():
            for keyword in keywords:
                if keyword.lower() in business_lower:
                    return category, keyword
        return None, None

    def _ai_categorize(self, business_name: str, amount: float = None) -> Tuple[str, float]:
        """Use Ollama AI to categorize expense"""

        # Build prompt
        prompt = f"""You are a financial expense categorizer for Israeli expenses.

Business name: {business_name}
{f"Amount: ₪{amount:.2f}" if amount else ""}

Available categories (in Hebrew):
{', '.join(self.categories)}

Respond ONLY with a JSON object in this exact format:
{{"category": "category_name", "confidence": 0.85}}

The category must be one of the available categories listed above.
Confidence should be between 0 and 1.

Response:"""

        # Call Ollama API
        response = requests.post(
            self.ollama_url,
            json={
                "model": self.ai_config['model'],
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
                "format": "json"
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")

        result = response.json()
        ai_response = result.get('response', '{}')

        try:
            parsed = json.loads(ai_response)
            category = parsed.get('category', 'אחר')
            confidence = float(parsed.get('confidence', 0.5))

            # Validate category
            if category not in self.categories:
                # Try to find closest match
                category = self._find_closest_category(category)

            return category, confidence

        except json.JSONDecodeError:
            # If AI response is not valid JSON, fall back
            return "אחר", 0.3

    def _find_closest_category(self, invalid_category: str) -> str:
        """Find closest valid category if AI returns invalid one"""
        invalid_lower = invalid_category.lower()

        # Simple matching
        for category in self.categories:
            if category.lower() in invalid_lower or invalid_lower in category.lower():
                return category

        return "אחר"

    def check_ollama_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                return any(self.ai_config['model'] in name for name in model_names)
            return False
        except:
            return False
