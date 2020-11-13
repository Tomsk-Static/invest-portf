from portf import app, db
from flask import render_template, session, request, jsonify, redirect
from portf.models import Actives, History
from datetime import datetime
import requests
import datetime


@app.route('/')
def main():
    if not session.get('error'): error = None
    else:
        error = session['error']
        session.pop('error', None)
    return render_template('index.html', error=error)


@app.route('/go_to_actives')
def go_to_actives():
    return redirect('/actives')


@app.route('/actives', methods=('POST', 'GET'))
def actives():
    if request.method == 'POST':
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
                    session.pop('actual_prices', None)
                    session.modified = True
        else:
            active_name = request.form.get('active_name')
            ticket = request.form.get('ticket')
            type = request.form.get('type')
            if not active_name or not ticket or not type:
                error = "Enter active's name, ticket and type"
            elif Actives.query.filter_by(name=active_name).first():
                error = 'Active with name {} already exists'.format(active_name)
            elif Actives.query.filter_by(ticket=ticket).first():
                error = 'Active with ticket {} already exists'.format(ticket)
            else:
                active = Actives(name=active_name, ticket=ticket, type=type)
                db.session.add(active)
                db.session.commit()
                session.pop('actual_prices', None)
                session.modified = True
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
        if not active:
            session['error'] = "Active with name {} is not exist".format(name)
        else:
            active.price = (active.price * active.count + price * count)/(active.count + count)
            active.count += count
            # db.session.add(active)
            transaction = History(active_name=name, count=count, price=price, date=datetime.datetime.now())
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
            transaction = History(active_name=name, count=count, price=price, profit=profit, date=datetime.datetime.now())
            db.session.add(transaction)
            db.session.commit()
    return redirect('/')


@app.route('/get_actives', methods=['GET', 'POST'])
def get_actives(type, amount='all'):
    if amount == 'all':
        return Actives.query.filter(Actives.type==type).all()
    elif amount == 'bought':
        return Actives.query.filter(Actives.type==type, Actives.count > 0).all()


@app.route('/price', methods=['GET', 'POST'])
def crypto_price():
    if session.get('actual_prices'):
        print('session is not null')
        return session['actual_prices']
    req = dict()
    all_actives = get_actives('crypto', 'bought')
    price_url = 'https://api.binance.com/api/v3/ticker/24hr'
    params = {'symbol': ''}
    for active in all_actives:
        params['symbol'] = str(active.ticket).upper() + 'USDT'
        price = requests.get(price_url, params=params).json()['lastPrice']
        price = price.split('.')
        try:
            price[1] = price[1][:3]
        except:
            pass
        req[active.name] = '.'.join(price)
    session['actual_prices'] = req
    return req


def get_sparkline(active, days=10):
    prices = {'prices': [], 'timestamps': []}
    date = datetime.datetime.today() - datetime.timedelta(days=days)
    date = date.isoformat('T') + 'Z'

    api_url = 'https://api.nomics.com/v1/currencies/sparkline'
    api_key = '3264cf50e622153fa78146f301941e86'
    api_url = api_url + '?key=' + api_key

    params = {'ids': active.upper(),
              'start': date}
    req = requests.get(api_url, params=params).json()

    prices['prices'] = [float(price[:7]) if len(price) >= 7 else float(price) for price in req[0]['prices']]
    prices['timestamps'] = [time[:10] if len (time) >= 10 else time for time in req[0]['timestamps']]

    return prices


@app.route('/data_for_chart/<string:ticket>', methods=['GET', 'POST'])
def data_for_chart(ticket):
    active = Actives.query.filter(Actives.ticket == ticket).first()
    if active.type == 'crypto':
        prices = get_sparkline(ticket)

    else: prices = {'prices': [], 'timestamps': []}
    print(prices)
    return prices

