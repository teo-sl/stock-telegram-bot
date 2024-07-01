import threading
import telebot
import time
from utils import *

class BotFunctionality:
    def __init__(self,token,chat_id):
        self.stock_settings = {}
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id

    def send_message(self, stock_name, old_price=None):
        infos = None
        is_first = old_price is None
        try:
            if self.stock_settings[stock_name].stock_type==StockTypes.STOCK:
                infos = get_stock_data(stock_name)
            else:
                infos = get_crypto_data(stock_name+"USDT")
            cur_price = infos['current_price']
            text_to_send = f"{stock_name}\n"
            
            if is_first:
                old_price = infos['previous_close']
                
            prev_close = infos['previous_close']

            if abs(old_price - cur_price) >= 0.1 or is_first:
                trend = "falling" if old_price > cur_price else "rising"
                difference_price = round(abs(old_price - cur_price), 2)
                text_to_send += f"Price is {trend} of {difference_price} ||| {'+' if difference_price>=0 else ''} {round((difference_price/old_price)*100,2)} % \nCurrent price {cur_price}\n"
                text_to_send += f"Change from today {'+' if cur_price - prev_close>=0 else ''}{round((cur_price - prev_close) / float(prev_close) * 100, 3)} %"
                self.bot.send_message(self.chat_id, text_to_send)  
            return cur_price
        
        except Exception as e:
            print(f"Error when executing function, printing error:\n {e}\n Printing payload: ")
            print(infos)
            return old_price

    def monitoring_func(self, stock_name, message):
        stock_info = self.stock_settings[stock_name]
        old_price = None
        while True:
            with stock_info.lock:
                if not stock_info.is_monitoring:
                    return
            try:
                old_price = self.send_message(stock_name, old_price)
            except Exception as e:
                self.bot.send_message(self.chat_id, "Error when monitoring, please relaunch service")
                self.stop_monitor(message)
                print(e)
                return
            time.sleep(stock_info.interval_minutes * 60)

    def start_monitor(self, message):
        interval_minutes = 5
        try:
            parsed_msg = parse_message(message,InputPayloads.MONITOR)
            command = parsed_msg['command']
            stock_name = parsed_msg['stock_name']
            interval_minutes = parsed_msg['interval_minutes']
        except Exception as e:
            self.bot.reply_to(message, "Error when monitoring, please relaunch service")
            print(e)
            return
        
        if stock_name not in self.stock_settings:
            self.stock_settings[stock_name] = StockSettings(stock_name, interval_minutes, is_monitoring=False)   
        else:
            # using monitor to update interval_minutes
            self.stock_settings[stock_name].interval_minutes = interval_minutes
            
        if "crypto" in command:
                self.stock_settings[stock_name].stock_type=StockTypes.CRYPTO     
        stock_info = self.stock_settings[stock_name]
        
        with stock_info.lock:
            if not stock_info.is_monitoring:
                stock_info.is_monitoring = True
                threading.Thread(target=self.monitoring_func, args=[stock_name, message]).start()
                self.bot.reply_to(message, "Monitoring started.")
            else:
                self.bot.reply_to(message, "Monitoring is already running.")

    def stop_all(self, message):
        for x in self.stock_settings:
            with self.stock_settings[x].lock:
                self.stock_settings[x].is_monitoring = False
                self.bot.reply_to(message, f"Stopping {x}")

    def stop_monitor(self, message):
        try:
            stock_name = parse_message(message,InputPayloads.STOCK_NAME)['stock_name']
        except:
            self.bot.reply_to(message, "Error when monitoring, please relaunch service")
            return
        
        if stock_name not in self.stock_settings:
            self.bot.reply_to(message, f"Monitor of {stock_name} not present")
            return
        
        stock_info = self.stock_settings[stock_name]
        with stock_info.lock:
            if stock_info.is_monitoring:
                stock_info.is_monitoring = False
                self.bot.reply_to(message, "Monitoring stopped.")
            else:
                self.bot.reply_to(message, "Monitoring is not running.")

    def get_stock_summary(self, message):
        try:
            stock_name = parse_message(message,InputPayloads.STOCK_NAME)['stock_name']
        except:
            self.bot.reply_to(message, "Error when getting summary, please relaunch service")
            return
        
        try:
            res = get_stock_percentage_changes(stock_name)
            mex_to_send = ""
            for x in res:
                mex_to_send += f"{x} : {res[x]}\n"
            
            self.bot.reply_to(message, mex_to_send)
        except:
            self.bot.reply_to(message, "Error when getting summary data. Please contact administrator")

    def get_stock_code(self, message):
        try:
            parsed_msg = parse_message(message,InputPayloads.COMPANY)['stock_name']
            company_name = parsed_msg['company_name']
            market = parsed_msg['market']
        except:
            self.bot.reply_to(message, "Bad input format")
            return
        
        try:
            codes = get_ticker(company_name, market)
            if codes == []:
                self.bot.reply_to(message, f"No ticker found for: {company_name}")
            text_to_reply = f"Found this ticker for: {company_name}\n"
            for x in codes:
                text_to_reply += x + "\n"
            self.bot.reply_to(message, text_to_reply)
        except:
            self.bot.reply_to(message, "Error when executing func")
    

    def run(self):
        # Add message handlers
        self.bot.message_handler(commands=['monitor', 'monitoring','mcrypto'])(self.start_monitor)
        self.bot.message_handler(commands=['stopall'])(self.stop_all)
        self.bot.message_handler(commands=['stop'])(self.stop_monitor)
        self.bot.message_handler(commands=['summary', 'sum'])(self.get_stock_summary)
        self.bot.message_handler(commands=['search', 's'])(self.get_stock_code)

        # Start the bot
        self.bot.infinity_polling(timeout=10, long_polling_timeout = 5)
