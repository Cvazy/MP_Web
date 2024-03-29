import re
import random
from flask import Flask, render_template, request, redirect
from faker import Faker

fake = Faker()

app = Flask(__name__)
application = app

images_ids = ['7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
              '2d2ab7df-cdbc-48a8-a936-35bba702def5',
              '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
              'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
              'cab5b7f2-774e-4884-a200-0c0180fa777f']

def generate_comments(replies=True):
    comments = []
    for i in range(random.randint(1, 3)):
        comment = { 'author': fake.name(), 'text': fake.text() }
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    return {
        'title': 'Заголовок поста',
        'text': fake.paragraph(nb_sentences=100),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.jpg',
        'comments': generate_comments()
    }

posts_list = sorted([generate_post(i) for i in range(5)], key=lambda p: p['date'], reverse=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def posts():
    return render_template('posts.html', title='Посты', posts=posts_list)

@app.route('/posts/<int:index>')
def post(index):
    p = posts_list[index]
    return render_template('singlePost.html', title=p['title'], post=p)

@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')

@app.route('/phone', methods=['GET', 'POST'])
def check_phone():
    if request.method == 'POST':
        phone = request.form['phone_number'].replace(' ', '')
        str_success = '()-.+0123456789 '
        str_nums = '+0123456789'
        check_symbols = False

        for i in '()-.+ ':
            phone.replace(i, '')

        for check in phone:
            if not check in str_success:
                check_symbols = True

        if all(chr.isdigit() for chr in phone):
            for index in range(len(phone)):
                if not phone[index] in str_nums:
                    phone = phone[:index] + phone[index + 1:]

        if len(phone) != 11 and len(phone) != 12 and not check_symbols:
            return render_template(
                'checkPhone.html',
                title='Проверка номера телефона',
                success=False,
                checked=True,
                phone=phone,
                message='Недопустимый ввод. Неверное количество цифр.',
            )
        elif check_symbols:
            return render_template(
                'checkPhone.html',
                title='Проверка номера телефона',
                success=False,
                checked=True,
                phone=phone,
                message='Недопустимый ввод. В номере телефона встречаются недопустимые символы.',
            )
        else:
            if phone[0] == '+':
                phone_formatted = f"+7 {phone[2:5]} {phone[5:8]} {phone[8:10]} {phone[10:12]}"
            else:
                phone_formatted = f"+7 {phone[1:4]} {phone[4:7]} {phone[7:9]} {phone[9:11]}"

            return render_template(
                'checkPhone.html',
                title='Проверка номера телефона',
                success=True,
                checked=True,
                phone=phone_formatted,
            )
    else:
        return render_template('checkPhone.html', title='Проверка номера телефона')