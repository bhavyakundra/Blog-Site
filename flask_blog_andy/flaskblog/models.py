import os
import bleach
from bleach import clean
from flask import current_app
from datetime import datetime
from flask_login import UserMixin
from flaskblog import db, login_manager
from itsdangerous import URLSafeTimedSerializer, BadSignature

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    is_admin = db.Column(db.Boolean, default=False)
    can_add_post = db.Column(db.Boolean, default=False)
    can_update_post = db.Column(db.Boolean, default=False)
    can_delete_post = db.Column(db.Boolean, default=False)
    send_notifications = db.Column(db.Boolean, default=False)
    is_subscribed = db.Column(db.Boolean, default=True)

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=1800)
            user_id = data.get('user_id')
            return User.query.get(user_id)
        except BadSignature:
            return None

    def __repr__(self):
        return "User('{}', '{}', '{}')".format(self.username, self.email, self.image_file)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_filename = db.Column(db.String(255))  # Store the filename of the uploaded image
    pdf_filename = db.Column(db.String(255)) 
    excel_filename = db.Column(db.String(255))   # Store the filename of the uploaded PDF
    files_filename = db.Column(db.String(255))
    files = db.relationship('File', secondary='post_file_association', back_populates='posts')

    def __repr__(self):
        return "Post('{}', '{}')".format(self.title, self.date_posted)
    
    def image_path(self):
        if self.image_filename:
            return os.path.join(current_app.config['UPLOAD_FOLDER'], self.image_filename)
        return None

    def pdf_path(self):
        if self.pdf_filename:
            return os.path.join(current_app.config['UPLOAD_FOLDER'], self.pdf_filename)
        return None

    def excel_path(self):
        if self.excel_filename:
            return os.path.join(current_app.config['UPLOAD_FOLDER'], self.excel_filename)
        return None

    def files_path(self):
        if self.files_filename:
            return os.path.join(current_app.config['UPLOAD_FOLDER'], self.files_filename)
        return None

    @property
    def sanitized_content(self):
        return clean(self.content, tags=bleach.sanitizer.ALLOWED_TAGS, attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES)
    

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    posts = db.relationship('Post', secondary='post_file_association', back_populates='files')

# Association table for many-to-many relationship between Post and File models
post_file_association = db.Table(
    'post_file_association',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'))
)