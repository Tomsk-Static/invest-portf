from portf import db


class Actives(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    ticket = db.Column(db.String(10), nullable=False, unique=True)
    count = db.Column(db.Float, nullable=True, default=0)
    price = db.Column(db.Float, nullable=True, default=0)

    def __repr__(self):
        return '<Active: {}, ticket: {}, id: {}, count: {}, price: {}>'.format(self.name, self.ticket, self.id, self.count, self.price)


