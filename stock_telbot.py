from utils import get_stock_data, get_stock_percentage_changes, StockSettings
import threading
import telebot
import threading
import time

stock_settings = {}


bot_token = "your token"
bot = telebot.TeleBot(bot_token)


def send_message(bot,stock_name,chat_id,old_price=None):
    infos = None
    is_first = old_price is None
    try:
        infos = get_stock_data(stock_name)
        cur_price = infos['current_price']
        text_to_send = f"{stock_name}\n"
        
        if old_price is None:
            old_price=infos['previous_close']

        if abs(old_price-cur_price)>=0.1 or is_first:
            trend = "falling" if old_price>cur_price else "rising"
            text_to_send+=f"Price is {trend} of {round(abs(old_price-cur_price),2)}\nCurrent price {cur_price}"
            bot.send_message(chat_id,text_to_send)  
        return cur_price
    
    except Exception as e:
        print(f"Error when executing function, pringing error:\n {e}\n Printing payload: ")
        print(infos)
        
        return old_price


def monitoring_func(stock_name,message):
    global stock_settings
    stock_info = stock_settings[stock_name]
    chat_id = "your chat"
    old_price = None
    while True:
        with stock_info.lock :
            if not stock_info.is_monitoring:
                return
        try:
            old_price = send_message(bot,stock_name,chat_id,old_price)
        except:
            bot.send_message("Error when monitoring, please relaunch service")
            stop_monitor(message)
            return
        time.sleep(stock_info.interval_minutes*60)
        
@bot.message_handler(commands=['monitor','monitoring'])
def start_monitor(message):
    interval_minutes=5
    try:
        splitted_msg = message.text.split(' ')
        stock_name = splitted_msg[1].strip()
        if len(splitted_msg)>2:
            interval_minutes = int(splitted_msg[2])
    except:
        bot.reply_to(message,"Error when monitoring, please relaunch service")
        return
    
    global stock_settings
    if stock_name not in stock_settings:
        stock_settings[stock_name] = StockSettings(stock_name,interval_minutes,False)
    
    stock_info = stock_settings[stock_name]
    
    with stock_info.lock:
        if not stock_info.is_monitoring:
            stock_info.is_monitoring = True
            threading.Thread(target=monitoring_func,args=[stock_name,message]).start()
            bot.reply_to(message, "Monitoring started.")
        else:
            bot.reply_to(message, "Monitoring is already running.")


    
@bot.message_handler(commands=['stopall'])
def stop_all(message):
    global stock_settings
    for x in stock_settings:
        with stock_settings[x].lock:
            stock_settings[x].is_monitoring=False
            bot.reply_to(message,f"Stopping {x}")
    
           
    
    
@bot.message_handler(commands=['stop'])
def stop_monitor(message):
    try:
        stock_name = message.text.split(' ')[1].strip()
    except:
        bot.reply_to(message,"Error when monitoring, please relaunch service")
        return
    
    global stock_settings
    if stock_name not in stock_settings:
        bot.reply_to(message,f"Monitor of {stock_name} not present")
        return
    stock_info = stock_settings[stock_name]
    with stock_info.lock:
        if stock_info.is_monitoring:
            stock_info.is_monitoring = False
            bot.reply_to(message, "Monitoring stopped.")
        else:
            bot.reply_to(message, "Monitoring is not running.")
            
@bot.message_handler(commands=['summary','sum'])
def get_stock_summary(message):
    try:
        stock_name = message.text.split(' ')[1].strip()
    except:
        bot.reply_to(message,"Error when getting summary, please relaunch service")
        return
    try:
        res = get_stock_percentage_changes(stock_name)
        mex_to_send = ""
        for x in res:
            mex_to_send+=f"{x} : {res[x]}\n"
        
        bot.reply_to(message,mex_to_send)
    except:
        bot.reply_to(message,"Error when getting summary data. Please contact administrator")


bot.polling()
