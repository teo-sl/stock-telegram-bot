from bot_func import BotFunctionality
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    load_dotenv()
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    bot_func = BotFunctionality(bot_token,chat_id)
    bot_func.run()
    