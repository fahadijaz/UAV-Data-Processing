from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class LogForm(FlaskForm):
    user = SelectField('User', coerce=int, validators=[DataRequired()])
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    process = SelectField('Process', coerce=int, validators=[DataRequired()])
    instrument = SelectField('Instrument', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Log Process')
