"""empty message

Revision ID: 256479bae295
Revises: 
Create Date: 2024-05-31 22:43:08.353980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '256479bae295'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('images',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=75), nullable=False),
    sa.Column('mimetype', sa.String(length=75), nullable=False),
    sa.Column('md5hash', sa.String(length=256), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_images')),
    sa.UniqueConstraint('md5hash', name=op.f('uq_images_md5hash'))
    )
    op.create_table('courses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=75), nullable=False),
    sa.Column('short_desc', sa.String(length=1000), nullable=False),
    sa.Column('full_desc', sa.Text(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('rating_sum', sa.Integer(), nullable=False),
    sa.Column('rating_num', sa.Integer(), nullable=False),
    sa.Column('image_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_courses_author_id_users')),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name=op.f('fk_courses_category_id_categories')),
    sa.ForeignKeyConstraint(['image_id'], ['images.id'], name=op.f('fk_courses_image_id_images')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_courses'))
    )
    op.create_table('reviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_reviews_course_id_courses')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reviews_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reviews'))
    )
    op.alter_column('categories', 'name',
               existing_type=sa.CHAR(length=128),
               type_=sa.String(length=75),
               existing_nullable=False)
    op.alter_column('users', 'middle_name',
               existing_type=sa.VARCHAR(length=75),
               nullable=True)
    op.alter_column('users', 'created_at',
               existing_type=sa.TIMESTAMP(),
               type_=sa.DateTime(),
               existing_nullable=False)
    op.create_unique_constraint(op.f('uq_users_login'), 'users', ['login'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_users_login'), 'users', type_='unique')
    op.alter_column('users', 'created_at',
               existing_type=sa.DateTime(),
               type_=sa.TIMESTAMP(),
               existing_nullable=False)
    op.alter_column('users', 'middle_name',
               existing_type=sa.VARCHAR(length=75),
               nullable=False)
    op.alter_column('categories', 'name',
               existing_type=sa.String(length=75),
               type_=sa.CHAR(length=128),
               existing_nullable=False)
    op.drop_table('reviews')
    op.drop_table('courses')
    op.drop_table('images')
    # ### end Alembic commands ###