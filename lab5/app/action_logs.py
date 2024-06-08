from flask import Blueprint, render_template, request, send_file
from flask_login import current_user
from users import check_rights
import math, io

bp = Blueprint('action_logs', __name__, url_prefix='/action_logs')

def generate_report_file(records, fields):
    csv_content = '№, ' + ', '.join(fields) + '\n'
    for i, record in enumerate(records):
        values = list()
        for f in fields:
            if f == 'login' and str(getattr(record, f, '')) == 'None':
                values.append('Аноним')
            else:
                values.append(str(getattr(record, f, ''))) 
        csv_content += f'{i + 1}, ' + ', '.join(values) + '\n'
    f = io.BytesIO()
    f.write(csv_content.encode('utf-8'))
    f.seek(0)
    return f

@bp.route('/')
def index():
    from app import db
    count_notes_per_page = 10
    active_page = int(request.args.get('page', 1))
    
    cnx = db.connect()

    with cnx.cursor(named_tuple=True) as cursor:
        query_get_active_elements = (
            "SELECT action_logs.*, users.login FROM action_logs LEFT JOIN "
            "users ON action_logs.user_id = users.id %s"
            "ORDER BY created_at DESC "
            f"LIMIT {count_notes_per_page} "
            f"OFFSET {(active_page - 1) * count_notes_per_page}"
        )

        if current_user.get_id() is None:
            query_get_active_elements %= (f"WHERE user_id = {-1} ")
        else:
            if not current_user.can('show_statistics', current_user):
                query_get_active_elements %= (f"WHERE users.id = {current_user.id} ")
            else:
                query_get_active_elements %= ""

        cursor.execute(query_get_active_elements)
        logs = cursor.fetchall()

        query_get_counts_notes = (
            "SELECT COUNT(*) as count FROM action_logs %s"
        )

        if current_user.get_id() is None:
            query_get_counts_notes %= (f"WHERE user_id = {-1} ")
        else:
            if not current_user.can('show_statistics', current_user):
                query_get_counts_notes %= (f"WHERE user_id = {current_user.id} ")
            else:
                query_get_counts_notes %= ""

        cursor.execute(query_get_counts_notes)
        count_notes = cursor.fetchone().count

        start_page = max(active_page - 1, 1)
        next_page = min(active_page + 1, math.ceil(count_notes / count_notes_per_page))
        end_page = math.ceil(count_notes / count_notes_per_page)

    if request.args.get('download_csv'):
        query_get_full_notes = (
            "SELECT action_logs.*, users.login FROM action_logs LEFT JOIN "
            "users ON action_logs.user_id = users.id "
            "ORDER BY created_at DESC"
        )

        with cnx.cursor(named_tuple=True) as cursor:
            cursor.execute(query_get_full_notes)
            f = generate_report_file(cursor.fetchall(), ['path', 'created_at', 'login'])
            return send_file(f, mimetype='text/csv', as_attachment=True, download_name='stat_actions.csv')

    return render_template(
        "actions_logs/index.html", 
        count_notes=count_notes, 
        start_page=start_page, 
        next_page=next_page,
        end_page=end_page,
        logs=logs
    )

@bp.route('/stat/users')
@check_rights('show_statistics')
def stat_users():
    from app import db
    count_notes_per_page = 10
    active_page = int(request.args.get('page', 1))

    cnx = db.connect()

    with cnx.cursor(named_tuple=True) as cursor:
        query = (
            "SELECT action_logs.user_id, users.login, COUNT(*) AS count FROM action_logs LEFT JOIN "
            "users ON action_logs.user_id = users.id "
            "GROUP BY action_logs.user_id "
            f"LIMIT {count_notes_per_page} "
            f"OFFSET {(active_page - 1) * count_notes_per_page}"
        )

        cursor.execute(query)
        logs = cursor.fetchall()

        query_get_counts_notes = (
            "SELECT COUNT(*) AS count FROM (SELECT action_logs.user_id, users.login, COUNT(*) as count "
            "FROM action_logs LEFT JOIN users ON action_logs.user_id = users.id "
            "GROUP BY action_logs.user_id) AS SUBQUERY"
        )

        cursor.execute(query_get_counts_notes)
        count_notes = cursor.fetchone().count

        start_page = max(active_page - 1, 1)
        next_page = min(active_page + 1, math.ceil(count_notes / count_notes_per_page))
        end_page = math.ceil(count_notes / count_notes_per_page)

    if request.args.get('download_csv'):
        query_get_full_notes = (
            "SELECT action_logs.user_id, users.login, COUNT(*) AS count FROM action_logs LEFT JOIN "
            "users ON action_logs.user_id = users.id "
            "GROUP BY action_logs.user_id"
        )

        with cnx.cursor(named_tuple=True) as cursor:
            cursor.execute(query_get_full_notes)
            f = generate_report_file(cursor.fetchall(), ['login', 'count'])
            return send_file(f, mimetype='text/csv', as_attachment=True, download_name='stat_users.csv')

    return render_template(
        "actions_logs/stat_users.html", 
        count_notes=count_notes,
        start_page=start_page,
        next_page=next_page,
        end_page=end_page,
        logs=logs
    )

@bp.route('/stat/pages')
@check_rights('show_statistics')
def stat_pages():
    from app import db
    count_notes_per_page = 10
    active_page = int(request.args.get('page', 1))

    cnx = db.connect()

    with cnx.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT path, COUNT(*) AS count FROM action_logs GROUP BY path')
        logs = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) AS count FROM action_logs')
        count_notes = cursor.fetchone().count

        start_page = max(active_page - 1, 1)
        next_page = min(active_page + 1, math.ceil(count_notes / count_notes_per_page))
        end_page = math.ceil(count_notes / count_notes_per_page)
    
    if request.args.get('download_csv'):
        f = generate_report_file(logs, ['path', 'count'])
        return send_file(f, mimetype='text/csv', as_attachment=True, download_name='stat_pages.csv')

    return render_template(
        "actions_logs/stat_pages.html", 
        count_notes=count_notes,
        start_page=start_page,
        next_page=next_page,
        end_page=end_page,
        logs=logs
    )