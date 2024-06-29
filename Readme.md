# Stock telegram bot

This repo contains the source code for a simple telegram bot. The bot can:
- monitor the price of a particular stock (user can specify the time interval)
- get a summary fort a certain stock (mean price for the last 5 days ecc...)
- search for a ticker given the company name and (optionally) the market code (e.g. .MI)


This version can currently sends message only to one chat at a time (this may change in future version).

# How to use

1. create a .env file and add your TELEGRAM_BOT_TOKEN and CHAT_ID
2. install the dependencies in requirements.txt
3. launch main.py
4. enjoy!

