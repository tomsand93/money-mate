"""
Upload blueprint — handles credit card Excel file uploads.
"""
import os
import tempfile
import shutil
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash

from auth import login_required
from db_utils import get_db
from extensions import allowed_file, ai_categorizer, processor

logger = logging.getLogger(__name__)

bp = Blueprint('uploads', __name__)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Process uploaded credit card Excel files."""
    db = get_db()

    if request.method == 'POST':
        if 'files' not in request.files:
            flash('לא נבחרו קבצים', 'error')
            return redirect(request.url)

        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('לא נבחרו קבצים', 'error')
            return redirect(request.url)

        temp_dir = tempfile.mkdtemp()
        try:
            use_ai = ai_categorizer.check_ollama_available()
            processed_count = skipped_count = error_count = total_transactions = 0

            for file in files:
                if not file or not allowed_file(file.filename):
                    flash(f'סוג קובץ לא נתמך: {file.filename}', 'warning')
                    continue

                filename = file.filename

                if db.is_file_processed(filename):
                    skipped_count += 1
                    continue

                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)

                try:
                    df = processor.process_file(filepath)

                    if use_ai:
                        for idx in df.index:
                            business_name = df.at[idx, 'business_name']
                            amount = df.at[idx, 'billing_amount']
                            category, confidence, method, reason = ai_categorizer.categorize(
                                business_name, amount
                            )
                            df.at[idx, 'category'] = category
                            df.at[idx, 'classification_method'] = method
                            df.at[idx, 'classification_confidence'] = confidence
                            df.at[idx, 'classification_reason'] = reason

                    new_records = db.add_expenses(df)
                    db.mark_file_processed(filename, len(df))
                    processed_count += 1
                    total_transactions += new_records

                except Exception as e:
                    error_count += 1
                    logger.error(f'Error processing file {filename}: {e}')
                    flash(f'שגיאה בקובץ {filename}: {e}', 'error')
                finally:
                    if os.path.exists(filepath):
                        os.remove(filepath)

            if processed_count > 0:
                flash(f'עובדו בהצלחה {processed_count} קבצים עם {total_transactions} עסקאות', 'success')
                if use_ai:
                    flash('סיווג AI הופעל', 'info')
            if skipped_count > 0:
                flash(f'דולגו {skipped_count} קבצים שכבר עובדו', 'warning')
            if error_count > 0:
                flash(f'{error_count} קבצים נכשלו', 'error')
            if processed_count == 0 and skipped_count == 0 and error_count == 0:
                flash('לא נמצאו קבצי Excel תקינים', 'warning')

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        return redirect(url_for('index'))

    ollama_available = ai_categorizer.check_ollama_available()
    return render_template('upload.html', ollama_available=ollama_available)
