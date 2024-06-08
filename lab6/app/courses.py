from flask_login import login_required
from os.path import splitext, join
from sqlalchemy.exc import IntegrityError
from models import db, Course, Category, User, Image, Review
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from flask_login import current_user
from tools import CoursesFilter
import hashlib, uuid

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

def to_dict(item):
    return {
        'last_name': item.user.last_name,
        'first_name': item.user.first_name,
        'middle_name': item.user.middle_name,
        'created_at': item.created_at,
        'rating': item.rating,
        'text': item.text
    }

@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()  

    return render_template(
        'courses/index.html',
        courses=courses,
        categories=categories,
        pagination=pagination,
        search_params=search_params()
    )

@bp.route('/new')
@login_required
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()

    return render_template(
        'courses/new.html',
        categories=categories,
        users=users,
        course=course
    )

@bp.route('/create', methods=['POST'])
@login_required
def create():
    try:
        course = Course(**params())
        if request.files.get('background_img') and request.files['background_img'].filename:
            image = Image(filename=request.files['background_img'].filename, 
                          mimetype=request.files['background_img'].mimetype, 
                          md5hash=hashlib.md5(request.files.get('background_img').read()).hexdigest(),
                          id = str(uuid.uuid4()))
            db.session.add(image)
            db.session.commit()
            course.image_id = image.id
            db.session.add(course)
            db.session.commit()
            flash(f'Курс был успешно добавлен!', 'success')
            request.files['background_img'].seek(0)
            request.files['background_img'].save(join(current_app.config['UPLOAD_FOLDER'], image.id + splitext(image.filename)[1])) 
    except IntegrityError as error:
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        flash(f'Произошла ошибка! {error}', 'danger')

        return render_template(
            'courses/new.html',
            categories=categories,
            users=users,
            course=course
        )
    
    return redirect(url_for('courses.index'))


def get_review_and_update_db(course_id):
    rating_value = int(request.form['select-mark'])
    text = request.form['text-area']

    review = Review(
        text=text, 
        rating=rating_value, 
        course_id=course_id, 
        user_id=current_user.id
    )

    try:
        db.session.add(review)
        course = db.get_or_404(Course, course_id)
        course.rating_sum += rating_value
        course.rating_num += 1
        db.session.commit()
        flash(f'Отзыв успешно добавлен', 'success')
    except:
        db.session.rollback()
        flash(f'При сохранении отзыва произошла ошибка', 'danger')


def check_post_review(course_id):
    review_list = db.session.query(Review).filter(Review.user_id == current_user.get_id())

    return all(1 if review.course_id != course_id else 0 for review in review_list)


@bp.route('/<int:course_id>', methods=['GET', 'POST'])
def show(course_id):
    if request.method == 'POST':
        get_review_and_update_db(course_id)
        return redirect(url_for('courses.show', course_id=course_id))

    course = db.get_or_404(Course, course_id)
    category = db.get_or_404(Category, course.category_id)
    reviewData = db.session.query(Review).filter(Review.course_id == course_id).limit(5)

    return render_template(
        'courses/show.html', 
        course=course, 
        category=category, 
        reviewData=reviewData,
        check_review=check_post_review(course_id)
    )


def sorting_by():
    sorted_by_value = session['data']['sorted-by-value']
    # Сортировка по новизне
    if sorted_by_value == "by-new":
        session.get("data")["sorted-review-list"] = sorted(
            session.get("data")["sorted-review-list"],
            key = lambda x: x['created_at'], reverse = True
        )
    # Сортировка по положительным отзывам
    elif sorted_by_value == "firstly-good":
        session.get("data")["sorted-review-list"] = sorted(
            session.get("data")["sorted-review-list"],
            key = lambda x: x['rating'], reverse = True
        )
    # Сортировка по отрицательным отзывам
    elif sorted_by_value == "firstly-bad":
        session.get("data")["sorted-review-list"] = sorted(
            session.get("data")["sorted-review-list"],
            key = lambda x: x['rating']
        )

@bp.route('courses/<int:course_id>/reviews', methods=['GET', 'POST'])
def reviews(course_id):
    session.modified = True

    review_list = list(map(to_dict, sorted(
        db.session.query(Review).filter(Review.course_id == course_id),
        key = lambda x: x.created_at, reverse = True
    )))

    if request.args.get('sorted-at') is None and session.get('data') is None:
        session['data'] = {
            'sorted-review-list': review_list, 
            'course_id': course_id,
            'sorted-by-value': 'by-new'
        } 
    
    elif len(review_list) != len(session['data']['sorted-review-list']):
        session['data'] = {
            'sorted-review-list': review_list, 
            'course_id': course_id,
            'sorted-by-value': session['data']['sorted-by-value']
        }
        sorting_by() 

    elif request.args.get('sorted-at') is not None and session.get('data') is not None and session.get('data').get('course_id') == course_id:
        session['data']['sorted-by-value'] = request.args.get('sorted-at')
        sorting_by()  

    elif request.args.get('sorted-at') is None and session.get('data') is not None and session.get('data').get('course_id') != course_id:
        session['data'] = {
            'sorted-review-list': list(map(to_dict, sorted(
                    db.session.query(Review).filter(Review.course_id == course_id),
                    key = lambda x: x.created_at, reverse = True
                ))),
            'course_id': course_id,
            'sorted-by-value': session.get('data').get('sorted-by-value')
        }
        sorting_by()  
        
    pagination = db.paginate(db.select(Review))
    
    if request.method == 'POST':
        get_review_and_update_db(course_id)
        return redirect(url_for('courses.reviews', course_id=course_id))

    return render_template(
        'courses/reviews.html',
        pagination=pagination,
        allReviewData=session.get('data').get("sorted-review-list"),
        sortedByValue=session.get('data').get('sorted-by-value'),
        check_review=check_post_review(course_id),
        # доработать
        params={'course_id': course_id}
    )
