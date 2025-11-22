"""
Financial analyzer for 50/30/20 rule and recommendations
"""
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

import json
from typing import Dict, List, Tuple
from collections import defaultdict


class FinancialAnalyzer:
    def __init__(self, config_path: str = 'config_ai.json'):
        """Initialize financial analyzer"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.need_want_config = self.config['need_want_invest']
        self.needs_categories = set(self.need_want_config['needs'])
        self.wants_categories = set(self.need_want_config['wants'])
        self.target_percentages = self.need_want_config['target_percentages']

    def analyze_spending(self, category_summary: Dict[str, Dict], total_income: float = None) -> Dict:
        """
        Analyze spending according to 50/30/20 rule

        Args:
            category_summary: Dict with category names as keys and data dicts as values
                             (must include 'סכום' key for amount)
            total_income: Total income to calculate percentages against

        Returns:
            Dict with analysis results
        """
        needs_total = 0
        wants_total = 0
        uncategorized_total = 0

        needs_breakdown = {}
        wants_breakdown = {}
        uncategorized_breakdown = {}

        for category, data in category_summary.items():
            amount = data.get('סכום', 0)

            if category in self.needs_categories:
                needs_total += amount
                needs_breakdown[category] = amount
            elif category in self.wants_categories:
                wants_total += amount
                wants_breakdown[category] = amount
            else:
                # Track uncategorized items (like "אחר")
                uncategorized_total += amount
                uncategorized_breakdown[category] = amount

        total_expenses = needs_total + wants_total + uncategorized_total

        # Calculate percentages based on INCOME (not expenses!)
        # If no income provided, fall back to expenses (for backward compatibility)
        base_amount = total_income if total_income and total_income > 0 else total_expenses

        needs_percentage = (needs_total / base_amount * 100) if base_amount > 0 else 0
        wants_percentage = (wants_total / base_amount * 100) if base_amount > 0 else 0
        uncategorized_percentage = (uncategorized_total / base_amount * 100) if base_amount > 0 else 0

        return {
            'needs': {
                'amount': needs_total,
                'percentage': needs_percentage,
                'target': self.target_percentages['needs'],
                'breakdown': needs_breakdown,
                'status': 'good' if needs_percentage <= self.target_percentages['needs'] else 'over'
            },
            'wants': {
                'amount': wants_total,
                'percentage': wants_percentage,
                'target': self.target_percentages['wants'],
                'breakdown': wants_breakdown,
                'status': 'good' if wants_percentage <= self.target_percentages['wants'] else 'over'
            },
            'uncategorized': {
                'amount': uncategorized_total,
                'percentage': uncategorized_percentage,
                'breakdown': uncategorized_breakdown
            },
            'total_expenses': total_expenses
        }

    def calculate_investment_potential(self, income: float, needs: float, wants: float) -> Dict:
        """
        Calculate investment potential and actual savings rate

        Args:
            income: Total income
            needs: Total needs spending
            wants: Total wants spending

        Returns:
            Dict with investment analysis
        """
        total_expenses = needs + wants
        actual_savings = income - total_expenses
        actual_savings_percentage = (actual_savings / income * 100) if income > 0 else 0

        # Calculate ideal amounts based on 50/30/20
        ideal_needs = income * (self.target_percentages['needs'] / 100)
        ideal_wants = income * (self.target_percentages['wants'] / 100)
        ideal_invest = income * (self.target_percentages['invest'] / 100)

        return {
            'actual_savings': actual_savings,
            'actual_percentage': actual_savings_percentage,
            'target_percentage': self.target_percentages['invest'],
            'ideal_amount': ideal_invest,
            'difference': actual_savings - ideal_invest,
            'status': 'excellent' if actual_savings_percentage >= self.target_percentages['invest'] else 'needs_improvement'
        }

    def generate_recommendations(self, analysis: Dict, category_summary: Dict[str, Dict],
                                income: float) -> List[str]:
        """
        Generate personalized savings recommendations

        Args:
            analysis: Output from analyze_spending()
            category_summary: Full category breakdown
            income: Total income

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check needs spending
        if analysis['needs']['status'] == 'over':
            overspend = analysis['needs']['percentage'] - analysis['needs']['target']
            recommendations.append(
                f"🔴 הוצאות הצרכים שלך ({analysis['needs']['percentage']:.1f}%) גבוהות מהמומלץ ({analysis['needs']['target']}%). "
                f"נסה לחפש דרכים לחסוך ב: {', '.join(sorted(analysis['needs']['breakdown'].keys(), key=lambda x: analysis['needs']['breakdown'][x], reverse=True)[:2])}"
            )

        # Check wants spending
        if analysis['wants']['status'] == 'over':
            overspend = analysis['wants']['percentage'] - analysis['wants']['target']
            # Find top want categories
            top_wants = sorted(analysis['wants']['breakdown'].items(),
                             key=lambda x: x[1], reverse=True)[:3]

            recommendations.append(
                f"⚠️ הוצאות הרצונות שלך ({analysis['wants']['percentage']:.1f}%) גבוהות מהמומלץ ({analysis['wants']['target']}%). "
                f"אולי כדאי לצמצם הוצאות ב{top_wants[0][0]} (₪{top_wants[0][1]:,.0f})"
            )

        # Specific category recommendations
        for category, data in sorted(category_summary.items(),
                                     key=lambda x: x[1].get('סכום', 0), reverse=True)[:5]:
            amount = data.get('סכום', 0)
            percentage_of_income = (amount / income * 100) if income > 0 else 0

            # Eating out recommendations
            if category == 'אוכל בחוץ' and percentage_of_income > 10:
                potential_savings = amount * 0.3  # 30% reduction
                recommendations.append(
                    f"🍽️ הוצאות על אוכל בחוץ: ₪{amount:,.0f} ({percentage_of_income:.1f}% מההכנסה). "
                    f"הפחתה של 30% תחסוך לך ₪{potential_savings:,.0f} בחודש!"
                )

            # Subscription recommendations
            if category == 'חשבונות ומנויים' and percentage_of_income > 8:
                recommendations.append(
                    f"📱 בדוק את המנויים שלך - יכול להיות שיש מנויים שאתה לא משתמש בהם. "
                    f"אתה מוציא ₪{amount:,.0f} על מנויים וחשבונות."
                )

            # Transportation recommendations
            if category == 'תחבורה' and percentage_of_income > 12:
                recommendations.append(
                    f"🚗 הוצאות תחבורה גבוהות: ₪{amount:,.0f}. "
                    f"שקול שימוש בתחבורה ציבורית או שיתוף נסיעות לחיסכון."
                )

        # Positive reinforcement
        if analysis['needs']['status'] == 'good' and analysis['wants']['status'] == 'good':
            recommendations.insert(0,
                "✅ כל הכבוד! אתה שומר על איזון טוב בין צרכים ורצונות!"
            )

        # If no recommendations yet, add general one
        if not recommendations:
            recommendations.append(
                "💡 המשך לעקוב אחר ההוצאות שלך ותמיד חפש הזדמנויות לחסוך."
            )

        return recommendations[:5]  # Return top 5 recommendations

    def compare_to_targets(self, actual_needs_pct: float, actual_wants_pct: float,
                          actual_invest_pct: float) -> Dict:
        """
        Compare actual percentages to 50/30/20 targets

        Returns:
            Dict with comparison data for visualization
        """
        return {
            'needs': {
                'actual': actual_needs_pct,
                'target': self.target_percentages['needs'],
                'diff': actual_needs_pct - self.target_percentages['needs']
            },
            'wants': {
                'actual': actual_wants_pct,
                'target': self.target_percentages['wants'],
                'diff': actual_wants_pct - self.target_percentages['wants']
            },
            'invest': {
                'actual': actual_invest_pct,
                'target': self.target_percentages['invest'],
                'diff': actual_invest_pct - self.target_percentages['invest']
            }
        }
