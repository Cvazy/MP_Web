from flask import render_template, request, redirect, url_for, flash, Blueprint
from mysql.connector.errors import DatabaseError
from flask_login import login_required, current_user
import functools

bp = Blueprint('users', __name__, url_prefix='/users')

def check_rights(action):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            record = None
            if "user_id" in kwargs:
                try:
                    from app import db
                    cnx = db.connect()
                    with cnx.cursor(named_tuple=True) as cursor:
                        query = ("SELECT * FROM users WHERE id = %s")
                        cursor.execute(query, (kwargs["user_id"],))
                        record = cursor.fetchone()
                except DatabaseError:
                        record = None
            if not current_user.can(action, record):
                flash('Недостаточно прав для доступа к странице', 'warning')
                return redirect(url_for('users.index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

@bp.route('/')
def index():
    from app import db
    cnx = db.connect()
    with cnx.cursor(named_tuple=True) as cursor:
        query = (
            "SELECT users.*, roles.name AS role_name FROM users "
            "LEFT JOIN roles ON users.role_id = roles.id"
        )

        cursor.execute(query)
        users_list = cursor.fetchall()

    return render_template('users.html', users_list=users_list)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
@check_rights('create')
def new():
    params_dict = {}

    if request.method == 'POST':
        params_dict = {
            'last_name': request.form['last_name'], 
            'first_name': request.form['first_name'],
            'middle_name': request.form['middle_name'],
            'login': request.form['login'],
            'password': request.form['password'],
            'role_id': request.form['role_id']
        }

        for key in params_dict:
            if params_dict[key].strip() == '':
                params_dict[key] = None

        try:
            from app import db
            cnx = db.connect()
            with cnx.cursor(named_tuple=True) as cursor:
                query = ('INSERT INTO users ('
                'last_name, first_name, middle_name, login, password_hash, role_id) '
                'VALUES (%(last_name)s, %(first_name)s, '
                '%(middle_name)s, %(login)s, SHA2(%(password)s, 256), %(role_id)s)')

                cursor.execute(query, params_dict)

                cnx.commit()

                flash('Пользователь был успешно добавлен', category = 'success')

                return redirect(url_for('users.index'))
        except DatabaseError:
            flash('Введены некоректные данные', category = 'danger')

            cnx.rollback()

    return render_template(
        'new_user.html', 
        data=params_dict, 
        roles=load_roles(),
        can_edit_role=True
    )

@bp.route('/users/<int:user_id>/view', methods=['GET', 'POST'])
@check_rights('view')
def view(user_id):
    from app import db
    cnx = db.connect()

    with cnx.cursor(named_tuple=True) as cursor:
        query = (
            "SELECT users.id, users.login, users.last_name, users.first_name, users.middle_name, "
            "roles.name AS role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s"
        )

        cursor.execute(query, (user_id, ))
        user_data = cursor.fetchall()

    return render_template('view.html', user_data=user_data)

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@check_rights('edit')
def edit(user_id):
    from app import db
    data = {}

    if request.method == 'GET':
        try:
            cnx = db.connect()
            with cnx.cursor(named_tuple=True) as cursor:
                query = ("SELECT * FROM users WHERE id = %s")
                cursor.execute(query, (user_id,))
                data = cursor.fetchone()
            if data is None:
                flash("Пользователь не найден", category = 'info')
                return redirect(url_for('users.index'))
        except DatabaseError:
            flash('Возникла ошибка про обращении к БД!', category = 'danger')
            return redirect(url_for('users.index'))
        
    elif request.method == 'POST':
        data = {
            'id': str(user_id),
            'last_name': request.form['last_name'], 
            'first_name': request.form['first_name'],
            'middle_name': request.form['middle_name'],
            'role_id': request.form['role_id'],
        }

        for key in data:
            if data[key].strip() == '':
                data[key] = None

        try:
            cnx = db.connect()

            with cnx.cursor(named_tuple=True) as cursor:
                query = ("UPDATE users SET last_name = %(last_name)s, "
                          "first_name = %(first_name)s, middle_name = %(middle_name)s, "
                           "role_id = %(role_id)s WHERE id = %(id)s")
                cursor.execute(query, data)
                cnx.commit()

                flash('Пользователь был успешно изменён', category = 'success')
                return redirect(url_for('users.index'))
        except DatabaseError:
            flash('Введены некоректные данные', category = 'danger')
            cnx.rollback()

    return render_template(
        "edit.html", 
        data=data, 
        roles=load_roles(),
        can_edit_role=current_user.can('show_statistics', current_user)
    )

@bp.route('/users/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
@check_rights('delete')
def delete():
    try:
        from app import db
        cnx = db.connect()

        with cnx.cursor(named_tuple=True) as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (list(request.values.get('user_id'))))

            cnx.commit()

            flash('Пользователь был удален', category = 'success')

            return redirect(url_for('index'))
    except DatabaseError:
        flash('Произошла непредвиденная ошибка', category = 'danger')
        cnx.rollback()
    
def load_roles():
    from app import db
    cnx = db.connect()
    with cnx.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT id, name FROM roles')
        roles = cursor.fetchall()
    return roles