from portf import app, db
from flask import render_template, session, request, jsonify, redirect
from portf.models import Actives, History
import requests
import datetime
import yfinance as yf
import pandas


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
            elif Actives.query.filter_by(name=active_name).first():
                error = 'Active with name {} already exists'.format(active_name)
            elif Actives.query.filter_by(ticket=ticket).first():
                error = 'Active with ticket {} already exists'.format(ticket)
            else:
                active = Actives(name=active_name, ticket=ticket, type=type)
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
        active = Actives.query.filter_by(name=name).first()
        if not active:
            session['error'] = "Active with name {} is not exist".format(name)
        else:
            active.price = (active.price * active.count + price * count)/(active.count + count)
            active.price = correct_price(active.price)
            active.count += count

            trans_time = datetime.datetime.now().replace(second=0, microsecond=0)
            transaction = History(active_name=name, count=count,
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
        active = Actives.query.filter_by(name=name).first()
        if not active:
            session['error'] = "Active with name {} is not exist".format(name)
        elif active.count <= 0:
            session['error'] = "You did not have active {}".format(name)
        else:
            profit = count * price - count * active.price
            profit = correct_price(profit)
            active.count -= count

            trans_time = datetime.datetime.now().replace(second=0, microsecond=0)
            transaction = History(active_name=name, count=count,
                                  price=price, profit=profit,
                                  date=trans_time)
            db.session.add(transaction)
            db.session.commit()
    return redirect('/')


@app.route('/get_actives', methods=['GET', 'POST'])
def get_actives(type, amount='all'):
    if type == 'all':
        if amount == 'all':
            return Actives.query.filter().all()
        elif amount == 'bought':
            return Actives.query.filter(Actives.type==type, Actives.count > 0).all()
    if amount == 'all':
        return Actives.query.filter(Actives.type==type).all()
    elif amount == 'bought':
        return Actives.query.filter(Actives.type==type, Actives.count > 0).all()


@app.route('/actual_prices', methods=['GET', 'POST'])
def price():
    request = dict()

    crypto = get_actives('crypto', 'bought')
    request = get_actual_crypto(crypto, request)

    shares = get_actives('shares', 'bought')
    try: request = get_actual_shares(shares, request)
    except: request = request
    print(request)

    request = {name: correct_price(price) for name, price in request.items()}
    print(request)
    return request


def get_actual_shares(actives, request):
    if not actives:
        return request

    actives_info = {active.ticket.upper(): active.name for active in actives}
    actives_tick = ' '.join(list(actives_info.keys()))

    prices = yf.download(actives_tick,
                         start=datetime.datetime.today().date())

    if len(actives) == 1:
        tick = list(actives_info.values())[0]
        request[tick] = list(prices['Close'].to_dict().values())[0]
    else:
        prices = prices['Close'].to_dict()
        for tick, content in prices.items():
            request[actives_info[tick]] = list(content.values())[0]

    return request


def get_actual_crypto(actives, request):
    price_url = 'https://api.binance.com/api/v3/ticker/24hr'
    params = {'symbol': ''}
    for active in actives:
        params['symbol'] = str(active.ticket).upper() + 'USDT'
        price = requests.get(price_url, params=params).json()['lastPrice']
        price = price.split('.')
        try:
            price[1] = price[1][:3]
        except:
            pass
        request[active.name] = '.'.join(price)

    return request


def get_sparkline_crypto(ticket, days=10):
    prices = {'prices': [], 'timestamps': []}
    date = datetime.datetime.today() - datetime.timedelta(days=days)
    date = date.isoformat('T') + 'Z'

    api_url = 'https://api.nomics.com/v1/currencies/sparkline'
    api_key = '3264cf50e622153fa78146f301941e86'
    api_url = api_url + '?key=' + api_key

    params = {'ids': ticket.upper(),
              'start': date}
    req = requests.get(api_url, params=params).json()

    prices['prices'] = [float(price[:7]) if len(price) >= 7 else float(price) for price in req[0]['prices']]
    prices['timestamps'] = [time[:10] if len(time) >= 10 else time for time in req[0]['timestamps']]

    return prices


def get_sparkline_share(ticket, days=10):
    prices = {'prices': [], 'timestamps': []}
    start_date = datetime.datetime.today().date() - datetime.timedelta(days=days)
    end_date = datetime.datetime.today().date()

    #находим  все будни
    all_weekdays = pandas.date_range(start=start_date,
                                 end=end_date,
                                 freq='B')

    all_weekdays = all_weekdays.to_list()

    share = yf.Ticker(ticket)
    period = str(len(all_weekdays)) + 'd'
    close_price = share.history(period=period)['Close']

    prices['prices'] = [price for price in map(correct_price, close_price)]
    prices['timestamps'] = [str(date)[:10] for date in all_weekdays]

    return prices


@app.route('/data_for_chart/<string:ticket>', methods=['GET', 'POST'])
def data_for_chart(ticket):
    active = Actives.query.filter(Actives.ticket == ticket).first()
    if active.type == 'crypto':
        prices = get_sparkline_crypto(ticket)

    elif active.type == 'shares':
        prices = get_sparkline_share(ticket)

    else: prices = {'prices': [], 'timestamps': []}
    print(prices)
    return prices


def correct_price(price):
    price = str(price)

    if '.' in price:
        price = price.split('.')
        if len(price[0]) > 3:
            price[1] = '0'
        else:
            try: price[1] = price[1][:5]
            except: pass
        price = '.'.join(price)

    return float(price)

# 1) разнести руты и функции в разные файлы
# 2) изменить количество выводимых символов для дат и сумм
# 3) решить вопрос с кэшированием акутальных цен на активы
# 4) при отрисовки графика цен на акции убрать из диапозона дат субботу и воскресенье
# 5) разбить поиск цен для графиков акций и крипты в три функции
# 6) оставить комметарии к функциям
# 7) remove /go_to_actives