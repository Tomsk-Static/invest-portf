from portf import db
from datetime import datetime


class Actives(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    ticket = db.Column(db.String(10), nullable=False, unique=True)
    count = db.Column(db.Float, nullable=True, default=0)
    price = db.Column(db.Float, nullable=True, default=0)
    type = db.Column(db.String(10), nullable=False)
    history_orders = db.relationship('History', backref='active')

    def __repr__(self):
        return {'active': self.name, 'ticket': self.ticket,
                'id': self.id, 'count': self.count,
                'price': self.price, 'type': self.type}


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active_name = db.Column(db.String(20), db.ForeignKey(Actives.name), nullable=False)
    count = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return {'id': self.id, 'name': self.active_name,
                'price': self.price, 'profit': self.profit,
                'count': self.count, 'date': self.date}



