from flask import Flask, render_template, session, request
from flask_login import login_required, current_user
from mysqldb import DatabaseConnector
from mysql.connector.errors import DatabaseError

app = Flask(__name__)
application = app

app.config.from_pyfile("config.py")

db = DatabaseConnector(app)

from auth import bp as auth_bp, create_login_manager
app.register_blueprint(auth_bp)
create_login_manager(app)
from users import bp as users_bp
app.register_blueprint(users_bp)
from action_logs import bp as action_logs_bp
app.register_blueprint(action_logs_bp)

@app.before_request
def action_logs():
    if current_user.get_id() is not None:
        user_id = current_user.get_id()
    else:
        user_id = -1
    path = request.path
    cnx = db.connect()
    try:
        with cnx.cursor(named_tuple=True) as cursor:
            query = ('INSERT INTO action_logs (user_id, path) VALUES (%s, %s)')
            cursor.execute(query, (user_id, path))
            cnx.commit()
    except DatabaseError:
        cnx.rollback()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/counter')
def counter():
    if not("counter" in session):
        session["counter"] = 1
    else:
        session["counter"] += 1
    return render_template('counter.html')

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')

if __name__ == '__main__':
    app.run(port=8001)