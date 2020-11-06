from portf import db
from datetime import datetime

class Actives(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    ticket = db.Column(db.String(10), nullable=False, unique=True)
    count = db.Column(db.Float, nullable=True, default=0)
    price = db.Column(db.Float, nullable=True, default=0)
    history_orders = db.relationship('History', backref='active')

    def __repr__(self):
        return '<Active: {}, ticket: {}, id: {}, count: {}, price: {}>'.format(self.name, self.ticket, self.id, self.count, self.price)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active_name = db.Column(db.String(20), db.ForeignKey(Actives.name), nullable=False)
    count = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<id: {}, active: {}, price: {}, profit: {}, count: {}, date: {}>'.format(
            self.id,
            self.active_name,
            self.price,
            self.profit,
            self.count,
            self.date)



