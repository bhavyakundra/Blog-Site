from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField

class UserPermissionsForm(FlaskForm):
    submit = SubmitField("Save Permissions")