import yfinance as yf
import threading
import datetime
import requests
from enum import Enum
from datetime import datetime
import re


class InputPayloads(Enum):
    MONITOR = 1
    STOCK_NAME = 2
    COMPANY = 3
class StockTypes(Enum):
    STOCK = 1
    CRYPTO = 2

class StockSettings():
    def __init__(self,stock_name,interval_minutes=5,is_monitoring=False, stock_type : StockTypes = StockTypes.STOCK):
        self.stock_name = stock_name
        self.interval_minutes = interval_minutes
        self.is_monitoring = is_monitoring
        self.lock = threading.Lock()
        self.stock_type = stock_type
        
    def __str__(self):
        return f"{self.stock_name} - {self.interval_minutes} - {self.is_monitoring}"

def parse_message(message : str, payload_type : InputPayloads):
    splt_msg = [x.strip() for x in message.text.split(' ')]
    if payload_type == InputPayloads.MONITOR:
        payload = {
            "command" : "",
            "stock_name" : "",
            "interval_minutes" : 5
        }
        assert len(splt_msg)>=2
        payload['command']=splt_msg[0]
        payload['stock_name']=splt_msg[1]
        if len(splt_msg)>=3:
            payload['interval_minutes']=int(splt_msg[2])
    elif payload_type==InputPayloads.STOCK_NAME:
        payload = {
            "stock_name" : "",
        }
        assert len(splt_msg)>=2
        payload['stock_name']=splt_msg[1]
    elif payload_type==InputPayloads.COMPANY:
        payload = {
            "company_name" : "",
            "maket" : None
        }
        assert len(splt_msg)>=2
        payload['company_name']=splt_msg[1]
        if len(splt_msg)>=3:
            market = splt_msg[2]
            pattern = r'^\.\w+$'
            assert re.match(pattern, market) != None
            payload['market']=market
    return payload
        
def get_stock_data(ticker):
    """
    Retrieves real-time stock data for a given European ticker symbol.

    Args:
        ticker (str): The ticker symbol of the stock (e.g., 'ENI.MI' for ENI S.p.A. on the Borsa Italiana)

    Returns:
        dict: A dictionary containing the stock's current price, previous close, and other relevant information.
    """
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info
        # Extracting relevant information
        current_price = stock_info.get('bid')
        previous_close = stock_info.get('previousClose')
        volume = stock_info.get('volume')
        currency = stock_info.get('currency')
        market_time = stock_info.get('regularMarketTime')

        return {
            'ticker': ticker,
            'current_price': current_price,
            'previous_close': previous_close,
            'volume': volume,
            'currency': currency,
            'market_time': market_time
        }
    except Exception as e:
        return {'error': str(e)}
    
    
def get_stock_percentage_changes(ticker,time_deltas=[5,30,182,365],names=["five days", "one month","six months","one year"]):
    """
    Retrieves the percentage change of the stock over the last 10 days, 1 month, 6 months, and 1 year.

    Args:
        ticker (str): The ticker symbol of the stock (e.g., 'ENI.MI' for ENI S.p.A. on the Borsa Italiana)

    Returns:
        dict: A dictionary containing the percentage changes for the specified periods.
    """
    try:
        stock = yf.Ticker(ticker)

        # Define the periods for which we want to calculate percentage changes
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        
        past_dates = [(datetime.datetime.today() - datetime.timedelta(days=delta)).strftime('%Y-%m-%d') for delta in time_deltas]

        # Fetch historical data for the specified periods
        history_data = [stock.history(start=past_d,end=today) for past_d in past_dates]
        # Calculate percentage changes
        def calculate_percentage_change(data):
            if data.empty:
                return None
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            return ((end_price - start_price) / start_price) * 100
        percentage_changes = [calculate_percentage_change(data) for data in history_data]
        ret = {'ticker':ticker}
        for i,n in enumerate(names):
            ret[n]=f"{round(percentage_changes[i],2)} %"
        return ret
    except Exception as e:
        return {'error': str(e)}
    
    
def get_ticker(company_name,market_ref=None):
    yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    params = {"q": company_name, "quotes_count": 1, "country": "United States"}

    res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
    data = res.json()
    codes = [x['symbol'] for x in data['quotes']]
    if codes == []:
        return codes
    if market_ref is not None:
        codes = [codes[0]]+[x for x in codes[1:] if x.endswith(market_ref)]
    return codes

def get_current_crypto(crypto_id):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={crypto_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return float(response.json()['price'])
    else:
        return None
    
def get_historical_crypto(crypto_id, date):
    url = f"https://api.binance.com/api/v3/klines?symbol={crypto_id}&interval=1d&startTime={date}&limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data[0][1]) 
    else:
        return None
    
def get_crypto_data(stock_name):
    current_price = get_current_crypto(stock_name)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_unix = int(today.timestamp() * 1000)
    yesterday_price = get_historical_crypto(stock_name,start_of_day_unix)
    
    infos = {
        "current_price" : current_price,
        "previous_close" : yesterday_price,
    }
    return infos