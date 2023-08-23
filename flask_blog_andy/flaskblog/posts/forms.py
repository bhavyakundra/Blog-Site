from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, TextAreaField, SubmitField

ALLOWED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
ALLOWED_PDF_EXTENSIONS = ['pdf']
ALLOWED_EXCEL_EXTENSIONS = ['xlsx', 'xls']


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    files = FileField('Attachments', validators=[FileAllowed(ALLOWED_IMAGE_EXTENSIONS + ALLOWED_PDF_EXTENSIONS + ALLOWED_EXCEL_EXTENSIONS)])
    submit = SubmitField('Post')
