from flask import Flask, render_template, send_from_directory, request
from flask_migrate import Migrate
from models import db, Category, Image
from auth import bp as auth_bp, init_login_manager
from courses import bp as courses_bp
from config import SECRET_KEY

app = Flask(__name__)
application = app

app.secret_key = SECRET_KEY

app.config.from_pyfile('config.py')

db.init_app(app)
migrate = Migrate(app, db)

init_login_manager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(courses_bp)

@app.route('/')
def index():
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template(
        'index.html',
        categories=categories,
    )

@app.route('/images/<image_id>')
def image(image_id):
    img = db.get_or_404(Image, image_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               img.storage_filename)

if __name__ == '__main__':
    app.run(port=8002)