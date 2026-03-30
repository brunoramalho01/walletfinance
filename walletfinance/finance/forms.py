from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, BooleanField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_wtf.file import FileField, FileAllowed, FileRequired

class TransactionForm(FlaskForm):
    description = StringField('Descrição', validators=[DataRequired(), Length(max=140)])
    expected_amount = DecimalField('Valor Previsto', validators=[Optional(), NumberRange(min=0)], places=2)
    amount = DecimalField('Valor Realizado', validators=[DataRequired(), NumberRange(min=0)], places=2)
    category = SelectField('Categoria', choices=[], validators=[DataRequired()])
    month = SelectField('Mês de Referência', choices=[
        ('Janeiro', 'Janeiro'), ('Fevereiro', 'Fevereiro'), ('Março', 'Março'),
        ('Abril', 'Abril'), ('Maio', 'Maio'), ('Junho', 'Junho'),
        ('Julho', 'Julho'), ('Agosto', 'Agosto'), ('Setembro', 'Setembro'),
        ('Outubro', 'Outubro'), ('Novembro', 'Novembro'), ('Dezembro', 'Dezembro')
    ], validators=[DataRequired()])
    type = SelectField('Tipo', choices=[('income', 'Receita'), ('expense', 'Despesa')], validators=[DataRequired()])
    paid = BooleanField('Pago/Recebido?')
    due_date = DateField('Data de Vencimento', validators=[Optional()])

class ImportTransactionForm(FlaskForm):
    file = FileField('Arquivo CSV', validators=[
        FileRequired(message='Por favor, selecione um arquivo.'),
        FileAllowed(['csv'], message='Apenas arquivos .csv são permitidos.')
    ])
