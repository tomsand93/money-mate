"""
Expenses blueprint — viewing, reviewing, and updating expense records.
"""
import logging
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

from auth import login_required
from db_utils import get_db
from extensions import MONTH_NAMES_HE, config, ai_categorizer

logger = logging.getLogger(__name__)

bp = Blueprint('expenses', __name__)


@bp.route('/expenses/<int:year>/<int:month>')
@login_required
def view_expenses(year, month):
    """View all expenses for a specific billing-cycle month."""
    db = get_db()
    start_date, end_date = db.get_billing_cycle_dates(year, month)

    result = db.client.table('expenses') \
        .select('*') \
        .eq('user_id', session['user_id']) \
        .gte('purchase_date', start_date) \
        .lt('purchase_date', end_date) \
        .order('purchase_date', desc=True) \
        .execute()

    expenses = result.data or []
    if not expenses:
        flash('אין נתונים לחודש זה', 'warning')
        return redirect(url_for('reports.reports'))

    for expense in expenses:
        if expense.get('purchase_date'):
            date_str = expense['purchase_date']
            expense['purchase_date'] = datetime.fromisoformat(
                date_str.split('T')[0] if 'T' in date_str else date_str
            )

    categories = list(config['categories'].keys())
    month_name = MONTH_NAMES_HE.get(month, str(month))

    return render_template('expenses.html',
                           expenses=expenses,
                           categories=categories,
                           year=year,
                           month=month,
                           month_name=month_name)


@bp.route('/review_transactions')
@login_required
def review_transactions():
    """Review and manually edit transaction categories."""
    db = get_db()

    confidence_filter = request.args.get('confidence')
    category_filter = request.args.get('category')
    edited_filter = request.args.get('edited')
    month_filter = request.args.get('month')  # Format: "YYYY-MM"

    query = db.client.table('expenses') \
        .select('*') \
        .eq('user_id', session['user_id']) \
        .order('purchase_date', desc=True)

    if category_filter:
        query = query.eq('category', category_filter)
    if edited_filter == 'true':
        query = query.eq('manually_edited', True)
    elif edited_filter == 'false':
        query = query.eq('manually_edited', False)

    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            start_date, end_date = db.get_billing_cycle_dates(year, month)
            query = query.gte('purchase_date', start_date).lt('purchase_date', end_date)
        except (ValueError, AttributeError):
            pass  # Ignore malformed filter

    result = query.limit(500).execute()
    transactions = result.data or []

    for txn in transactions:
        score = txn.get('classification_confidence', 0)
        if score >= 0.8:
            txn['confidence_level'] = 'high'
        elif score >= 0.5:
            txn['confidence_level'] = 'medium'
        elif score >= 0.3:
            txn['confidence_level'] = 'low'
        else:
            txn['confidence_level'] = 'uncertain'

        txn['purchase_date'] = datetime.strptime(txn['purchase_date'], '%Y-%m-%d')
        txn['original_category'] = txn['category']
        txn['confidence_score'] = score

    if confidence_filter:
        transactions = [t for t in transactions if t['confidence_level'] == confidence_filter]

    categories = list(config['categories'].keys())
    available_months = db.get_available_months()

    stats = {
        'total': len(transactions),
        'high_confidence': sum(1 for t in transactions if t['confidence_level'] == 'high'),
        'medium_confidence': sum(1 for t in transactions if t['confidence_level'] == 'medium'),
        'low_confidence': sum(1 for t in transactions if t['confidence_level'] == 'low'),
        'uncertain': sum(1 for t in transactions if t['confidence_level'] == 'uncertain'),
    }

    return render_template('review_transactions.html',
                           transactions=transactions,
                           categories=categories,
                           stats=stats,
                           available_months=available_months,
                           current_month_filter=month_filter)


@bp.route('/update_transaction_category', methods=['POST'])
@login_required
def update_transaction_category():
    """Update a single transaction's category."""
    db = get_db()
    data = request.json or {}
    txn_id = data.get('id')
    new_category = data.get('category')

    if not txn_id or not new_category:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        user_id = db.get_user_id()
        txn_result = db.client.table('expenses') \
            .select('business_name') \
            .eq('id', txn_id) \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()

        if not txn_result.data:
            return jsonify({'error': 'Transaction not found'}), 404

        business_name = txn_result.data.get('business_name')

        db.client.table('expenses') \
            .update({'category': new_category, 'manually_edited': True,
                     'classification_method': 'manual'}) \
            .eq('id', txn_id) \
            .eq('user_id', user_id) \
            .execute()

        learned_keywords = []
        if business_name:
            learned_keywords = ai_categorizer._save_correction(business_name, new_category)
            logger.info(f'Saved correction: {business_name} -> {new_category}, '
                        f'learned: {learned_keywords}')

        msg = (f'Category updated! Learned {len(learned_keywords)} new keyword(s).'
               if learned_keywords else 'Category updated!')
        return jsonify({'success': True, 'learned_keywords': learned_keywords, 'message': msg})

    except Exception as e:
        logger.error(f'Error updating transaction category: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/bulk_update_categories', methods=['POST'])
@login_required
def bulk_update_categories():
    """Bulk update multiple transactions' categories."""
    db = get_db()
    data = request.json or {}
    txn_ids = data.get('ids', [])
    new_category = data.get('category')

    if not txn_ids or not new_category:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        user_id = db.get_user_id()
        all_learned: list = []

        for txn_id in txn_ids:
            txn_result = db.client.table('expenses') \
                .select('business_name') \
                .eq('id', txn_id) \
                .eq('user_id', user_id) \
                .maybe_single() \
                .execute()

            if txn_result.data:
                business_name = txn_result.data.get('business_name')
                db.client.table('expenses') \
                    .update({'category': new_category, 'manually_edited': True,
                             'classification_method': 'manual'}) \
                    .eq('id', txn_id) \
                    .eq('user_id', user_id) \
                    .execute()
                if business_name:
                    all_learned.extend(ai_categorizer._save_correction(business_name, new_category))

        msg = (f'Updated {len(txn_ids)} transactions! Learned {len(all_learned)} new keyword(s).'
               if all_learned else f'Updated {len(txn_ids)} transactions!')
        return jsonify({'success': True, 'updated': len(txn_ids),
                        'total_learned_keywords': len(all_learned), 'message': msg})

    except Exception as e:
        logger.error(f'Error in bulk update: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/recategorize_with_ai', methods=['POST'])
@login_required
def recategorize_with_ai():
    """Recategorize selected transactions using AI/keyword engine."""
    db = get_db()
    data = request.json or {}
    txn_ids = data.get('ids', [])

    if not txn_ids:
        return jsonify({'error': 'No transactions selected'}), 400

    result = db.client.table('expenses') \
        .select('id, business_name') \
        .in_('id', txn_ids) \
        .eq('user_id', session['user_id']) \
        .execute()
    transactions = result.data or []

    try:
        if not ai_categorizer.check_ollama_available():
            return jsonify({'error': 'Ollama is not running'}), 503

        updated = 0
        for txn in transactions:
            new_category, confidence, method, reason = ai_categorizer.categorize(
                txn['business_name'], 0
            )
            if new_category:
                db.client.table('expenses') \
                    .update({'category': new_category, 'classification_method': method,
                             'classification_confidence': confidence,
                             'classification_reason': reason, 'manually_edited': False}) \
                    .eq('id', txn['id']) \
                    .eq('user_id', session['user_id']) \
                    .execute()
                updated += 1

        return jsonify({'success': True, 'updated': updated})

    except Exception as e:
        logger.error(f'Error in recategorize_with_ai: {e}')
        return jsonify({'error': str(e)}), 500


@bp.route('/api/update_expense_category', methods=['POST'])
@login_required
def update_expense_category():
    """Update an expense's category (used from expense detail views)."""
    db = get_db()
    data = request.json or {}
    expense_id = data.get('expense_id')
    new_category = data.get('category')

    if not expense_id or not new_category:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400

    try:
        expense = db.get_expense_by_id(expense_id)
        if expense:
            db.update_expense_category(expense_id, new_category)
            ai_categorizer._save_correction(expense['business_name'], new_category)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Expense not found'}), 404
    except Exception as e:
        logger.error(f'Error updating expense category: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
