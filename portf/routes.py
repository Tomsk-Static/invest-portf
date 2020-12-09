from portf import app, db
from flask import render_template, session, request, jsonify, redirect
from portf.models import Actives, History
import datetime
import portf.func_p as fm
import json


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
            type = request.form.get('type')

            if not active_name or not ticket or not type:
                error = "Enter active's name, ticket and type"
            elif Actives.query.filter_by(name=active_name.capitalize()).first():
                error = 'Active with name {} already exists'.format(active_name)
            elif Actives.query.filter_by(ticket=ticket.lower()).first():
                error = 'Active with ticket {} already exists'.format(ticket)
            else:
                active = Actives(name=active_name.capitalize(), ticket=ticket.lower(), type=type)
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
    count = float(request.form.get('count'))
    price = float(request.form.get('price'))

    if not name:
        session['error'] = "Enter the active's name"
    elif not count:
        session['error'] = "Enter the count"
    elif not price:
        session['error'] = "Enter the price"
    else:
        active = Actives.query.filter_by(name=name.capitalize()).first()
        if not active:
            session['error'] = "Active with name {} is not exist".format(name)
        else:
            active.price = (active.price * active.count + price * count)/(active.count + count)
            active.price = fm.correct_price(active.price)
            active.count += count

            trans_time = datetime.datetime.now().replace(second=0, microsecond=0)
            transaction = History(active_name=name.capitalize(), count=count,
                                  price=price, date=trans_time)
            db.session.add(transaction)
            db.session.commit()
    return redirect('/')


@app.route('/form_sell', methods=['POST'])
def form_sell():
    name = request.form.get('active_name')
    count = float(request.form.get('count'))
    price = float(request.form.get('price'))

    if not name:
        session['error'] = "Enter active's name"
    elif not count:
        session['error'] = "Enter count"
    elif not price:
        session['error'] = "Enter price"
    else:
        active = Actives.query.filter_by(name=name.capitalize()).first()
        if not active:
            session['error'] = "Active with name {} is not exist".format(name)
        elif active.count <= 0:
            session['error'] = "You did not have active {}".format(name)
        elif active.count < count:
            session['error'] = "You have only {} {}, you can't sell {}".format(active.count,
                                                                               active.name,
                                                                               count)
        else:
            profit = count * price - count * active.price
            profit = fm.correct_price(profit)
            active.count -= count

            trans_time = datetime.datetime.now().replace(second=0, microsecond=0)
            transaction = History(active_name=name.capitalize(), count=count,
                                  price=price, profit=profit,
                                  date=trans_time)
            db.session.add(transaction)
            db.session.commit()
    return redirect('/')


@app.route('/get_actual_prices', methods=['GET', 'POST'])
def get_actual_prices():
    request = dict()

    crypto = fm.get_actives('crypto', 'bought')
    request = fm.get_actual_crypto(crypto, request)

    shares = fm.get_actives('shares', 'bought')
    try: request = fm.get_actual_shares(shares, request)
    except: request = request
    print(request)

    request = {name: fm.correct_price(price) for name, price in request.items()}
    print(request)
    return request


#need unite with /get_actual_prices
#change block try/except
@app.route('/get_actual_price/<string:ticket>', methods=['GET'])
def get_actual_price(ticket):
    request = dict()
    act = Actives.query.filter(Actives.ticket == ticket).all()

    try: request = fm.get_actual_crypto(act, request)
    except: pass

    try: request = fm.get_actual_shares(act, request)
    except: pass

    request = {name: fm.correct_price(price) for name, price in request.items()}
    return request


@app.route('/data_for_chart/<string:ticket>', methods=['GET', 'POST'])
def data_for_chart(ticket):
    active = Actives.query.filter(Actives.ticket == ticket).first()
    if active.type == 'crypto':
        prices = fm.get_sparkline_crypto(ticket)

    elif active.type == 'shares':
        prices = fm.get_sparkline_share(ticket)

    else: prices = {'prices': [], 'timestamps': []}

    return prices


@app.route('/get_actives/<string:args>', methods=['GET'])
def get_actives_route(args):
    type, amount = args.split('_')
    actives = fm.get_actives(type, amount)
    return json.dumps(fm.serialize_list(actives))





# 2) изменить количество выводимых символов для сумм
# 3) решить вопрос с кэшированием акутальных цен на активы
# 5) разбить поиск цен для графиков акций и крипты в три функции?
# 6) оставить комметарии к функциям
# 7) сделать сортировку по дате для истории транзакций

