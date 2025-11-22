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
        """Save user correction for future learning"""
        self.user_corrections[business_name.lower()] = category
        with open(self.corrections_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_corrections, f, ensure_ascii=False, indent=2)

    def categorize(self, business_name: str, amount: float = None,
                   ask_user_callback=None) -> Tuple[str, float]:
        """
        Categorize expense using AI

        Returns:
            Tuple[str, float]: (category, confidence)
        """
        # First check if we have a user correction for this exact business
        if business_name.lower() in self.user_corrections:
            return self.user_corrections[business_name.lower()], 1.0

        # Check keyword matching first (fast path)
        keyword_category = self._keyword_match(business_name)
        if keyword_category:
            return keyword_category, 0.95

        # Use AI for categorization
        try:
            category, confidence = self._ai_categorize(business_name, amount)

            # If confidence is low, ask user
            if confidence < self.ai_config['confidence_threshold'] and ask_user_callback:
                user_category = ask_user_callback(business_name, category, confidence)
                if user_category:
                    category = user_category
                    confidence = 1.0
                    # Save this correction for learning
                    if self.ai_config['enable_learning']:
                        self._save_correction(business_name, category)

            return category, confidence

        except Exception as e:
            print(f"AI categorization failed: {e}, falling back to keyword matching")
            return keyword_category or "אחר", 0.5

    def _keyword_match(self, business_name: str) -> Optional[str]:
        """Traditional keyword matching as fallback"""
        business_lower = business_name.lower()

        for category, keywords in self.config['categories'].items():
            for keyword in keywords:
                if keyword.lower() in business_lower:
                    return category
        return None

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
