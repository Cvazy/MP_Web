from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from mysql.connector.errors import DatabaseError
from mysqldb import DatabaseConnector
from string import ascii_letters

app = Flask(__name__)
application = app

app.config.from_pyfile("config.py")
login_manager = LoginManager()
login_manager.login_view = 'enter'
login_manager.login_message = 'Пожалуйста, авторизуйтесь.'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)
db = DatabaseConnector(app)


class User(UserMixin):
    def __init__(self, login, user_id):
        self.login = login
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    cnx = db.connect()
    with cnx.cursor(named_tuple=True) as cursor:
        cursor = cnx.cursor(named_tuple=True)
        cursor.execute("SELECT id, login FROM users where id = %s", (user_id,))
        user_data = cursor.fetchone()
    if user_data is not None:
        return User(user_data.login, user_data.id)
    return None


@app.route('/')
def index():
    cnx = db.connect()

    with cnx.cursor(named_tuple=True) as cursor:
        cursor.execute("SELECT users.*, roles.name AS role_name FROM users "
        "LEFT JOIN roles ON users.role_id = roles.id")
        users_list = cursor.fetchall()

    return render_template('index.html', users_list=users_list)


@app.route('/enter', methods=['post', 'get'])
def enter():
    massage=''
    if request.method == 'POST':
        user_login = request.form['login']
        user_password = request.form['password']
        check_remember = True if request.form.get('user_remember') else False 
        cnx = db.connect()
        with cnx.cursor(named_tuple=True) as cursor:
            query = "SELECT login, id FROM users where login = %s and password_hash = SHA2(%s, 256)"
            cursor.execute(query, (user_login, user_password))
            user_data = cursor.fetchone()
        if user_data is not None:
            login_user(User(user_data.login, user_data.id), remember=check_remember)
            flash("Вход выполнен успешно", "success")      
            return redirect(request.args.get('next', url_for('index')))
        massage = 'Введены неверные данные'
        flash(massage, "danger")
    return render_template('enter.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    errors_dict = {}

    if request.method == 'POST':
        params_dict = {
            'past_password': request.form['past_password'],
            'new_password': request.form['new_password'],
            'repeat_password': request.form['repeat_password']
        }

        for key in params_dict:
            if params_dict[key].strip() == '':
                params_dict[key] = None

        # Валидация введеных значений
        for key, value in params_dict.items():
            if key != 'past_password':
                _, message = validation('password', value)
                if message != 'Удовлетворяет требованиям':
                    errors_dict[key] = message

        if len(errors_dict) == 0:
            try:
                cnx = db.connect()

                with cnx.cursor(named_tuple=True) as cursor:
                    cursor.execute(
                        "SELECT id FROM users WHERE id = %s AND password_hash = SHA2(%s, 256)", 
                        (current_user.get_id(), params_dict['past_password'])
                    )
                    
                    correct_past_password = cursor.fetchone()

                    if correct_past_password is not None and params_dict['new_password'] == params_dict['repeat_password']:
                        cursor.execute(
                            'UPDATE users SET password_hash = SHA2(%s, 256) WHERE id = %s',
                            (params_dict['new_password'], current_user.get_id()) 
                        )

                        cnx.commit()

                        flash('Пароль был успешно изменен', "success")

                        return redirect(url_for('index'))
                    else:
                        flash('Пароль не был изменен', 'danger')

            except DatabaseError:
                flash('Введены некоректные данные', category = 'danger')

                cnx.rollback()

    return render_template('change_password.html', errors=errors_dict)


@app.route('/users/<int:user_id>/view', methods=['GET', 'POST'])
def view_user(user_id):
    cnx = db.connect()

    with cnx.cursor(named_tuple=True) as cursor:
        query = (
            "SELECT users.id, users.login, users.last_name, users.first_name, users.middle_name, "
            "roles.name AS role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id = %s"
        )

        cursor.execute(query, (user_id, ))
        user_data = cursor.fetchall()

    return render_template('view.html', user_data=user_data)


def validation(key, value):
    if key in ['last_name', 'first_name', 'login', 'password'] and value == None:
        return (key, 'Поле не может быть пустым')
    
    elif key == 'login':  
        if not all(map(lambda x: 1 if x in ascii_letters or x in map(str, range(10)) else 0, value)):
            return (key, 'Логин должен состоять только из латинских букв и цифр')
        elif len(value) < 5:
            return (key, 'Логин должен быть не менее 5 символов')
        else:
            return (key, 'Удовлетворяет требованиям')
        
    elif key == 'password':
        available_chars = '''абвгдеёжзийклмнопрстуфхцчшщъыьэюя''' + '''~!?@#$%^&*_-+()[]{>}</\|"'.,:;'''

        if len(value) < 8:
            return (key, 'Пароль должен быть не менее 8 символов')
        elif len(value) > 128:
            return (key, 'Пароль должен быть не более 128 символов')
        elif value.replace(' ', '') != value:
            return (key, 'Пароль не должен содержать пробельных символов')
        elif sum(map(lambda x: 1 if x.isupper() else 0, value)) == 0:
            return (key, 'Пароль должен содержать как минимум одну заглавную букву')
        elif sum(map(lambda x: 1 if x.islower() else 0, value)) == 0:
            return (key, 'Пароль должен содержать как минимум одну строчную букву')
        elif not all(map(lambda x: x in ascii_letters or x in available_chars, filter(lambda x: not x.isdigit(), value))):
            return (key, 'Пароль должен содержать только латинские или кириллические буквы') 
        elif sum(map(lambda x: 1 if x.isdigit() else 0, value)) == 0:
            return (key, 'Пароль должен содержать как минимум одну цифру')
        elif not all(map(lambda x: int(x) in range(10), filter(lambda x: x.isdigit(), value))):
            return (key, 'Пароль должен содержать только арабские цифры')
        else:
            return (key, 'Удовлетворяет требованиям')
        
    else:
        return (key, 'Удовлетворяет требованиям')


@app.route('/users/new', methods=['GET', 'POST'])
def new_user():
    params_dict = {}

    errors_dict = {}

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

        # Валидация введеных значений
        for key, value in params_dict.items():
            if key not in ['middle_name', 'role_id']:
                param, message = validation(key, value)
                if message != 'Удовлетворяет требованиям':
                    errors_dict[param] = message

        if len(errors_dict) == 0:
            try:
                cnx = db.connect()

                with cnx.cursor(named_tuple=True) as cursor:
                    query = ('INSERT INTO users ('
                    'last_name, first_name, middle_name, login, password_hash, role_id) '
                    'VALUES (%(last_name)s, %(first_name)s, '
                    '%(middle_name)s, %(login)s, SHA2(%(password)s, 256), %(role_id)s)')

                    cursor.execute(query, params_dict)

                    cnx.commit()

                    flash('Пользователь был успешно добавлен', category = 'success')

                    return redirect(url_for('index'))
            except DatabaseError:
                flash('Введены некоректные данные', category = 'danger')

                cnx.rollback()

    return render_template('new_user.html', data=params_dict, errors=errors_dict, roles=load_roles())


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
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
                return redirect(url_for('index'))
        except DatabaseError:
            flash('Возникла ошибка про обращении к БД!', category = 'danger')
            return redirect(url_for('index'))
        
    elif request.method == 'POST':
        data = {
            "id": user_id,
            'last_name': request.form['last_name'], 
            'first_name': request.form['first_name'],
            'middle_name': request.form['middle_name'],
            'role_id': request.form['role_id']
        }

        for key in data:
            if key != 'id' and data[key].strip() == '':
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
                return redirect(url_for('index'))
        except DatabaseError:
            flash('Введены некоректные данные', category = 'danger')
            cnx.rollback()

    return render_template("edit.html", data=data, errors={}, roles=load_roles()) 


@app.route('/remove', methods=['GET', 'POST'])
def remove_user():
    try:
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
    cnx = db.connect()

    with cnx.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT id, name FROM roles')

        return cursor.fetchall()


if __name__ == '__main__':
    app.run(port=8000)
