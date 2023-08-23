from flask_wtf import FlaskForm
from wtforms import SubmitField

class UserPermissionsForm(FlaskForm):
    submit = SubmitField("Save Permissions")