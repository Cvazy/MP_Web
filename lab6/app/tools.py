import hashlib
import uuid
import os
from werkzeug.utils import secure_filename
from flask import current_app
from models import db, Course, Image

class CoursesFilter:
    def __init__(self, name, category_ids):
        self.name = name
        self.category_ids = category_ids
        self.query = db.select(Course)

    def perform(self):
        self.__filter_by_name()
        self.__filter_by_category_ids()
        return self.query.order_by(Course.created_at.desc())

    def __filter_by_name(self):
        if self.name:
            self.query = self.query.filter(
                Course.name.ilike('%' + self.name + '%'))

    def __filter_by_category_ids(self):
        if self.category_ids:
            self.query = self.query.filter(
                Course.category_id.in_(self.category_ids))
