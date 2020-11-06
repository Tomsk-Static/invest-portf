from portf import app, db
from flask import render_template, session, request, jsonify, redirect
from portf.models import Actives, History
from datetime import datetime


@app.route('/')
def main():
    if not session.get('error'): error = None
    else:
        error = session['error']
        session.pop('error', None)
    return render_template('index.html', error=error)


@app.route('/actives', methods=('POST', 'GET'))
def actives():
    if request.method == 'POST':
        print(request.form)
        if 'id' in request.form:
            if not request.form.get('id'):
                error = "Enter active's id"
            else:
                active_id = request.form.get('id')
                active = Actives.query.filter_by(id=active_id).first()
                if not active:
                    error = 'Active with id {} is not exists'.format(active_id)
                else:
                    db.session.delete(active)
                    db.session.commit()
        else:
            active_name = request.form.get('active_name')
            ticket = request.form.get('ticket')
            if not active_name or not ticket:
                error = "Enter active's name and ticket"
            elif Actives.query.filter_by(name=active_name).first():
                error = 'Active with name {} already exists'.format(active_name)
            elif Actives.query.filter_by(ticket=ticket).first():
                error = 'Active with ticket {} already exists'.format(ticket)
            else:
                active = Actives(name=active_name, ticket=ticket)
                db.session.add(active)
                db.session.commit()
    actives = Actives.query.filter(Actives.count != 0)
    all_actives = Actives.query.all()
    if 'error' not in locals():
        error = None
    return render_template('actives.html', actives=actives, all_actives=all_actives, error=error)


@app.route('/history', methods=['GET', 'POST'])
def history():
    history = History.query.order_by(History.date.desc()).all()
    return render_template('history.html', history=history)

@app.route('/form_buy', methods=['POST'])
def form_buy():
    name = request.form.get('active_name')
    count = int(request.form.get('count'))
    price = int(request.form.get('price'))
    if not name:
        session['error'] = "Enter the active's name"
    elif not count:
        session['error'] = "Enter the count"
    elif not price:
        session['error'] = "Enter the price"
    else:
        active = Actives.query.filter_by(name=name).first()
        print(active)
        if not active:
            session['error'] = "Active with name {} is not exist".format(name)
        else:
            active.price = (active.price * active.count + price * count)/(active.count + count)
            active.count += count
            # db.session.add(active)
            transaction = History(active_name=name, count=count, price=price, date=datetime.now())
            db.session.add(transaction)
            db.session.commit()
    return redirect('/')


@app.route('/form_sell', methods=['POST'])
def form_sell():
    name = request.form.get('active_name')
    count = int(request.form.get('count'))
    price = int(request.form.get('price'))

    if not name:
        session['error'] = "Enter active's name"
    elif not count:
        session['error'] = "Enter count"
    elif not price:
        session['error'] = "Enter price"
    else:
        active = Actives.query.filter_by(name=name).first()
        if not active:
            session['error'] = "Active with name {} is not exist".format(name)
        elif active.count <= 0:
            session['error'] = "You did not have active {}".format(name)
        else:
            profit = count * price - count * active.price
            # active.price = (active.price * active.count - price * count)/(active.count - count)
            active.count -= count
            transaction = History(active_name=name, count=count, price=price, profit=profit, date=datetime.now())
            db.session.add(transaction)
            db.session.commit()
    return redirect('/')





