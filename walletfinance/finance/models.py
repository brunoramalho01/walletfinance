from datetime import datetime
from walletfinance.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False, unique=True)
    type = db.Column(db.String(10), nullable=False)  # 'income' ou 'expense'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    transactions = db.relationship('Transaction', backref='category_obj', lazy=True)

    def __repr__(self):
        return f'<Category {self.name} - {self.type}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(140), nullable=False)
    expected_amount = db.Column(db.Numeric(10, 2), nullable=True)  # Valor previsto
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Valor realizado
    category = db.Column(db.String(60), nullable=False)  # Categoria dinâmica (nome)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    month = db.Column(db.String(20), nullable=False)  # Mês de referência (Janeiro, Fevereiro...)
    type = db.Column(db.String(10), nullable=False)  # 'income' ou 'expense'
    paid = db.Column(db.Boolean, default=False)  # Pago? ou Recebido?
    due_date = db.Column(db.Date, nullable=True)  # Data de vencimento/opcional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<Transaction {self.description} - {self.amount}>'
