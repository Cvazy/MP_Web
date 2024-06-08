import os

SECRET_KEY = 'c21b53cf1799629b3ac0acd3a46581c5afd4b370127f7d2ee3face937142'

SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://std_2650_lab5_221_332:r0manus_@std-mysql.ist.mospolytech.ru/std_2650_lab5_221_332'
# SQLALCHEMY_DATABASE_URI = "sqlite:////Users/r0mashka/Downloads/lab6/app/my_db.sqlite3"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images')
