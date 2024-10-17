import datetime

import requests
import schedule
import telebot
import time
from telebot import types
from bs4 import BeautifulSoup
from datetime import datetime

# Initialize the bot with your token
TELEGRAM_BOT_TOKEN = '7418868531:AAGEX4o6WfAx7BzltTVFIqiEuq7L6l9AVsQ'
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
CHAT_ID = '5888302454'
CHAT_ID1 = '7230793258'
ALERT_USERS = [5888302454, 7230793258]

# URLs for Chartink
CHARTINK_URL = "https://chartink.com/screener"
CHARTINK_POST_URL = "https://chartink.com/screener/process"

# Store previous results
previous_results = None

# Function to send a message to all alert users
def send_alert(message):
    print("message - send alert")
    for user in ALERT_USERS:
        bot.send_message(user, message)

# Function to get CSRF token and cookies
def get_csrf_token():
    print("inside csrf token")
    session = requests.Session()
    response = session.get(CHARTINK_URL)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find("meta", {"name": "csrf-token"})["content"]
        return csrf_token, session.cookies
    else:
        print(f"Failed to load Chartink page: {response.status_code}")
        return None, None

# Function to get screener results using CSRF token and cookies
def get_chartink_rsi40_results():
    print("inside rsi40 results")
    csrf_token, cookies = get_csrf_token()
    if not csrf_token or not cookies:
        return None

    payload = {
        '_token': csrf_token,
        'scan_clause': "( {cash} ( latest rsi( 14 ) > 40 and 1 day ago rsi( 14 ) <= 40 and latest volume > 200000 "
                       "and latest close > 50 and latest close < 1000 ) )"
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(CHARTINK_POST_URL, data=payload, headers=headers, cookies=cookies)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get data: {response.status_code}")
        return None

# Function to track delta results and send alerts for changes
def track_and_send_delta(current_results, stock_message=None):
    print("inside track and send delta")
    print(current_results)
    global previous_results
    print(previous_results)
    if previous_results is None:
        rsi_message = "RSI Crossing 40 alerts \n\n"
        send_alert(rsi_message)
        previous_results = current_results
        current_time = datetime.now().strftime("%d %B %H:%M")

        for stock in current_results['data']:
            stock_message = ""
            stock_name = stock['nsecode']
            stock_price = stock['close']
            print("First list",stock_name)
            #stock_volume = stock['volume']
            stock_message += f"\nTime : {current_time}\nStock: {stock_name}\nCurrent Price: {stock_price}\n"
            send_alert(stock_message)
        return  # First run, no deltas to track
    else:
        delta_message = "Delta Results:\n\n"
        deltas_found = False
        for stock in previous_results['data']:
            stock_name = stock['nsecode']
            stock_price = stock['close']
            stock_volume = stock['volume']
            print("Previous Results",stock_name)
        for stock in current_results['data']:
            stock_name = stock['nsecode']
            stock_price = stock['close']
            stock_volume = stock['volume']
            print("Current Results",stock_name)
        # Find the same stock in the previous results
        prev_stock = next((s for s in previous_results['data'] if s['nsecode'] == stock_name), None)

        if prev_stock:
            deltas_found = False
        else:
            current_time = datetime.now().strftime("%d %B %H:%M")
            delta_message += f"\nTime : {current_time}\nStock: {stock_name}\nCurrent Price: {stock_price}\n"
            deltas_found = True
            # Check if there's a delta in price or volume
            #if stock_price != prev_stock['close'] or stock_volume != prev_stock['volume']:
             #   delta_message += f"Stock: {stock_name}\nPrevious Price: {prev_stock['close']} | Current Price: {stock_price}\n"
             #  delta_message += f"Previous Volume: {prev_stock['volume']} | Current Volume: {stock_volume}\n\n"
             # deltas_found = True

    # Send message only if deltas were found
    if deltas_found:
        send_alert(delta_message)
    else:
        print("No deltas found.")

    # Update previous results
    previous_results = current_results

# Function to check screener results and send deltas
def check_for_alerts():
    results = get_chartink_rsi40_results()
    if results and 'data' in results:
        track_and_send_delta(results)
    else:
        print("No valid data or error in results")

# Schedule task to check for alerts every 5 minutes
def start_alerts():
    schedule.every(10).seconds.do(check_for_alerts)
    print("Bot started. Checking for alerts every 5 minutes...")

    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the bot and schedule
if __name__ == "__main__":
    try:
        start_alerts()
    except KeyboardInterrupt:
        print("Bot stopped.")
