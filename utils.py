import yfinance as yf
import threading
import datetime
import requests


class StockSettings():
    def __init__(self,stock_name,interval_minutes=5,is_monitoring=False):
        self.stock_name = stock_name
        self.interval_minutes = interval_minutes
        self.is_monitoring = is_monitoring
        self.lock = threading.Lock()
        
    def __str__(self):
        return f"{self.stock_name} - {self.interval_minutes} - {self.is_monitoring}"

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