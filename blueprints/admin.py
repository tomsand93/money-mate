"""
Admin blueprint — settings, onboarding, AI categorisation API.
"""
import json
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from auth import login_required
from db_utils import get_db
import extensions

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__)


@bp.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    """Onboarding page for new users."""
    db = get_db()

    if db.is_onboarding_complete() and request.method == 'GET':
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            monthly_income = float(request.form.get('monthly_income', 0))
            db.set_setting('monthly_income', str(monthly_income))

            descriptions = request.form.getlist('expense_description[]')
            amounts = request.form.getlist('expense_amount[]')
            categories = request.form.getlist('expense_category[]')
            expense_types = request.form.getlist('expense_type[]')

            for i in range(len(descriptions)):
                desc = descriptions[i].strip()
                if desc and amounts[i]:
                    amount = float(amounts[i])
                    if amount > 0:
                        db.add_fixed_expense(desc, amount, categories[i], expense_types[i])

            db.mark_onboarding_complete()
            flash('ברוך הבא ל-MoneyMate! ההגדרות נשמרו בהצלחה', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            logger.error(f'Onboarding error: {e}')
            flash(f'שגיאה בשמירת ההגדרות: {e}', 'error')
            return redirect(request.url)

    return render_template('onboarding.html')


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Application settings page."""
    db = get_db()
    config = extensions.config  # mutable module-level dict

    if request.method == 'POST':

        if 'monthly_income' in request.form:
            try:
                monthly_income = float(request.form['monthly_income'])
                db.set_setting('monthly_income', str(monthly_income))
                flash('הכנסה חודשית עודכנה בהצלחה', 'success')
            except Exception as e:
                logger.warning(f'monthly_income update failed: {e}')
                flash('שגיאה בעדכון הכנסה חודשית', 'error')

        if 'billing_cycle_day' in request.form:
            try:
                billing_cycle_day = int(request.form['billing_cycle_day'])
                if 1 <= billing_cycle_day <= 28:
                    db.set_setting('billing_cycle_day', str(billing_cycle_day))
                    flash('יום מחזור חיוב עודכן בהצלחה', 'success')
                else:
                    flash('יום מחזור חיוב חייב להיות בין 1 ל-28', 'error')
            except Exception as e:
                logger.warning(f'billing_cycle_day update failed: {e}')
                flash('שגיאה בעדכון יום מחזור חיוב', 'error')

        if 'delete_expense_id' in request.form:
            try:
                expense_id = request.form['delete_expense_id']
                db.delete_fixed_expense(expense_id)
                flash('הוצאה נמחקה בהצלחה', 'success')
            except Exception as e:
                logger.error(f'Error deleting fixed expense: {e}')
                flash(f'שגיאה במחיקת הוצאה: {e}', 'error')

        if 'new_expense_description' in request.form:
            try:
                desc = request.form['new_expense_description'].strip()
                amount = float(request.form['new_expense_amount'])
                category = request.form['new_expense_category']
                exp_type = request.form['new_expense_type']
                if desc and amount > 0:
                    db.add_fixed_expense(desc, amount, category, exp_type)
                    flash('הוצאה נוספה בהצלחה', 'success')
            except Exception as e:
                logger.warning(f'Add fixed expense failed: {e}')
                flash('שגיאה בהוספת הוצאה', 'error')

        if 'ai_enabled' in request.form:
            try:
                ai_enabled = request.form.get('ai_enabled') == 'on'
                db.set_setting('ai_classification_enabled', str(ai_enabled).lower())
                flash('הגדרות AI עודכנו בהצלחה', 'success')
            except Exception as e:
                logger.warning(f'AI settings update failed: {e}')
                flash('שגיאה בעדכון הגדרות AI', 'error')

        if 'confidence_threshold' in request.form:
            try:
                threshold = float(request.form['confidence_threshold'])
                if 0 <= threshold <= 1:
                    db.set_setting('confidence_threshold', str(threshold))
                    config['ai']['confidence_threshold'] = threshold
                    with open('config_ai.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    flash('רף ביטחון עודכן בהצלחה', 'success')
            except Exception as e:
                logger.warning(f'Confidence threshold update failed: {e}')
                flash('שגיאה בעדכון רף ביטחון', 'error')

        if 'category_for_keywords' in request.form:
            try:
                category = request.form['category_for_keywords']
                keywords_str = request.form.get('keywords', '')
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                config['categories'][category] = keywords
                with open('config_ai.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                flash(f'מילות מפתח לקטגוריה "{category}" עודכנו בהצלחה', 'success')
            except Exception as e:
                logger.warning(f'Keyword update failed: {e}')
                flash('שגיאה בעדכון מילות מפתח', 'error')

        if 'new_category_name' in request.form:
            try:
                category_name = request.form['new_category_name'].strip()
                keywords_str = request.form.get('new_category_keywords', '')
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                if category_name:
                    if category_name in config['categories']:
                        flash(f'הקטגוריה "{category_name}" כבר קיימת', 'error')
                    else:
                        config['categories'][category_name] = keywords
                        with open('config_ai.json', 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=2)
                        from ai_categorizer import AICategorizer
                        extensions.ai_categorizer = AICategorizer('config_ai.json')
                        flash(f'קטגוריה "{category_name}" נוספה בהצלחה', 'success')
            except Exception as e:
                logger.error(f'Add category failed: {e}')
                flash(f'שגיאה בהוספת קטגוריה: {e}', 'error')

        if 'delete_category' in request.form:
            try:
                category_to_delete = request.form['delete_category']
                if category_to_delete == 'אחר':
                    flash('לא ניתן למחוק את הקטגוריה "אחר"', 'error')
                elif category_to_delete in config['categories']:
                    # Reassign affected expenses via Supabase
                    user_id = db.get_user_id()
                    result = db.client.table('expenses') \
                        .update({'category': 'אחר'}) \
                        .eq('category', category_to_delete) \
                        .eq('user_id', user_id) \
                        .execute()
                    affected_rows = len(result.data) if result.data else 0

                    del config['categories'][category_to_delete]
                    with open('config_ai.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)

                    from ai_categorizer import AICategorizer
                    extensions.ai_categorizer = AICategorizer('config_ai.json')

                    flash(f'קטגוריה "{category_to_delete}" נמחקה. '
                          f'{affected_rows} הוצאות עודכנו ל"אחר"', 'success')
            except Exception as e:
                logger.error(f'Delete category failed: {e}')
                flash(f'שגיאה במחיקת קטגוריה: {e}', 'error')

        if 'clear_all_data' in request.form:
            confirmation = request.form.get('clear_data_confirmation', '').strip()
            if confirmation == 'DELETE':
                try:
                    db.delete_all_user_data()
                    flash('כל הנתונים נמחקו בהצלחה. תוכל להעלות קבצים מחדש כעת.', 'success')
                except Exception as e:
                    logger.error(f'Delete all data failed: {e}')
                    flash(f'שגיאה במחיקת נתונים: {e}', 'error')
            else:
                flash('אישור שגוי - הקלד DELETE בדיוק כדי למחוק', 'error')

        return redirect(url_for('admin.settings'))

    monthly_income = float(db.get_setting('monthly_income', '0'))
    billing_cycle_day = int(db.get_setting('billing_cycle_day', '9'))
    fixed_expenses = db.get_all_fixed_expenses()
    ai_enabled = db.get_setting('ai_classification_enabled', 'true') == 'true'
    confidence_threshold = float(db.get_setting(
        'confidence_threshold', str(config['ai']['confidence_threshold'])
    ))

    return render_template('settings.html',
                           config=config,
                           monthly_income=monthly_income,
                           billing_cycle_day=billing_cycle_day,
                           fixed_expenses=fixed_expenses,
                           ai_enabled=ai_enabled,
                           confidence_threshold=confidence_threshold,
                           ollama_available=extensions.ai_categorizer.check_ollama_available())


@bp.route('/api/categorize', methods=['POST'])
@login_required
def api_categorize():
    """Save a manual categorisation correction."""
    data = request.json or {}
    business_name = data.get('business_name')
    category = data.get('category')

    if business_name and category:
        extensions.ai_categorizer._save_correction(business_name, category)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Missing parameters'}), 400
