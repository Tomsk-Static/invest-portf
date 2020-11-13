import requests
import datetime
import pytz

start = datetime.datetime(2020, 11, datetime.datetime.today().day) - datetime.timedelta(days=13)
start = start.isoformat('T') + 'Z'

# end = datetime(2020, 10, 11, 19, 29, 43, 79043)
# end = start.replace(tzinfo=pytz.UTC)
# end.isoformat()

api_url = 'https://api.nomics.com/v1/currencies/sparkline?key=3264cf50e622153fa78146f301941e86'

params = { 'ids': 'ETH',
           'start': start}
print(start)
req = requests.get(api_url, params=params).json()
print(len(req[0]['prices']))