from datetime import datetime, timedelta
import yfinance as yf
import requests
import pandas
from pandas.tseries.offsets import BDay
from sqlalchemy.inspection import inspect
from portf.models import Actives, History

#incorrect logic
def get_actives(type='all', amount='all'):
    if type == 'all':
        if amount == 'all':
            return Actives.query.filter().all()
        elif amount == 'bought':
            return Actives.query.filter(Actives.type==type, Actives.count > 0).all()
    if amount == 'all':
        return Actives.query.filter(Actives.type==type).all()
    elif amount == 'bought':
        return Actives.query.filter(Actives.type==type, Actives.count > 0).all()


def get_actual_shares(actives, request):
    if not actives:
        return request

    actives_info = {active.ticket.upper(): active.name for active in actives}
    actives_tick = ' '.join(list(actives_info.keys()))

    date = datetime.today().date()
    print(date)
    if date.weekday() in (5, 6):
        date = date - BDay(1)

    prices = yf.download(actives_tick, start=date)

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
    date = datetime.today() - timedelta(days=days)
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
    start_date = datetime.today().date() - timedelta(days=days)
    end_date = datetime.today().date()

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


def correct_price(price):
    price = str(price)

    if '.' in price:
        price = price.split('.')

        if price[0] == '0':
            price[1] = price[1][:5]
        elif len(price[0]) > 3:
            price[1] = '0'
        else:
            try: price[1] = price[1][:2]
            except: pass
        price = '.'.join(price)

    return float(price)


#for serialize model objects to json format
#call example - json.dumps(serialize_list(actives))-> json
#for one entry
def serialize(el):
    return {c: getattr(el, c) for c in inspect(el).attrs.keys() if c != 'history_orders'}


#for list entries
def serialize_list(lst):
        return [serialize(el) for el in lst]


# 1) func get_actives incorrect logic need repair