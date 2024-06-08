from flask import render_template, request, redirect, url_for, flash, Blueprint, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from users_policy import UsersPolicy

bp = Blueprint('auth', __name__, url_prefix='/auth')

def create_login_manager(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.enter'
    login_manager.login_message = 'Пожалуйста, авторизуйтесь.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)
    login_manager.user_loader(load_user)

class User(UserMixin):
    def __init__(self, login, user_id, role_id):
        self.login = login
        self.id = user_id
        self.role_id = role_id

    def is_admin(self):
        return self.role_id == current_app.config['ADMIN_ROLE_ID']
    
    def can(self, action, record=None):
        policy = UsersPolicy(record)
        method = getattr(policy, action, None)
        if method == None:
            return False
        else: 
            return method()

def load_user(user_id):
    from app import db
    cnx = db.connect()
    with cnx.cursor(named_tuple=True) as cursor:
        cursor = cnx.cursor(named_tuple=True)
        cursor.execute("SELECT id, role_id, login FROM users where id = %s", (user_id,))
        user_data = cursor.fetchone()
    if user_data is not None:
        return User(user_data.login, user_data.id, user_data.role_id)
    return None

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@bp.route('/enter', methods=['post', 'get'])
def enter():
    from app import db
    massage=''
    if request.method == 'POST':
        user_login = request.form['login']
        user_password = request.form['password']
        check_remember = True if request.form.get('user_remember') else False 
        cnx = db.connect()
        with cnx.cursor(named_tuple=True) as cursor:
            query = "SELECT login, id, role_id FROM users where login = %s and password_hash = SHA2(%s, 256)"
            cursor.execute(query, (user_login, user_password))
            user_data = cursor.fetchone()
        if user_data is not None:
            login_user(User(user_data.login, user_data.id, user_data.role_id), remember=check_remember)
            flash("Вход выполнен успешно", "success")      
            return redirect(request.args.get('next', url_for('index')))
        massage = 'Введены неверные данные'
        flash(massage, "danger")
        
    return render_template('enter.html')