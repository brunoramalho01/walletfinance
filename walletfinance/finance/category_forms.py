from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Length

class CategoryForm(FlaskForm):
    name = StringField('Nome da Categoria', validators=[DataRequired(), Length(max=60)])
    type = SelectField('Tipo', choices=[('income', 'Receita'), ('expense', 'Despesa')], validators=[DataRequired()])
