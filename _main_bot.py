from environs import Env
import json
import pprint
import time

import websocket
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

try:
    import thread
except ImportError:
    import _thread as thread

from btcturk import Btcturk

env = Env()
env.read_env()

API_PUBLIC_KEY = env("BTC_API_PUBLIC_KEY")
API_PRIVATE_KEY = env("BTC_API_PRIVATE_KEY")

IS_TEST = False

my_update = None

PAIR_SYMBOL = "NEO_TRY"
MIN = 160
MAX = 170

client = Btcturk(API_PUBLIC_KEY, API_PRIVATE_KEY, IS_TEST)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def create_order(pair_symbol, price, quantity, order_type, order_method, stop_price):
    result = client.createOrder(pair_symbol, price, quantity, order_type, order_method, stop_price)
    print("createOrder")
    print(result)

    return result

def check_open_orders(pair_symbol):
    #checkOpenOrders
    result = client.checkOpenOrders(pair_symbol)
    print("checkOpenOrders")
    print(result)

    return result

def check_balances(pair_symbol):
    my_assets = {}
    #print(f"{bcolors.OKCYAN}VARLIKLARIM:{bcolors.ENDC}")
    result = client.checkBalances(pair_symbol,format = "raw")
    for r in result:
        if r["asset"] in ["TRY","NEO", "BTC"]:
            asset = r["asset"]
            balance = r["balance"]
            
            #print(f"{bcolors.OKCYAN}{asset}: {balance}{bcolors.ENDC}")

            my_assets[asset] = balance

    #print("\n")

    return my_assets

    
def on_message(ws, message):
    data = json.loads(message)
    #pprint.pprint(data)

    if data[0] == 402:
        result = data[1]

        pairSymbol = result["PS"]
        last = result["LA"]
        daily = result["D"]
        dailyPercent = result["DP"]
        high = result["H"]
        low = result["L"]
        bid = result["B"]
        ask = result["A"]


        print(f"{pairSymbol}: {last}")
        if float(daily) > 0:
            print(f"{bcolors.OKGREEN}24s Değişim: {daily}{bcolors.ENDC}")
        else:
            print(f"{bcolors.FAIL}24s Değişim: {daily}{bcolors.ENDC}")
        if float(dailyPercent) > 0:
            print(f"{bcolors.OKGREEN}24s Değişim - Yüzde: %{dailyPercent}{bcolors.ENDC}")
        else:
            print(f"{bcolors.FAIL}24s Değişim - Yüzde: %{dailyPercent}{bcolors.ENDC}")
            
        print(f"24s En Yüksek: {high}")
        print(f"24s En Düşük: {low}")
        print(f"En İyi Alış: {bid}")
        print(f"En İyi Satış: {ask}\n")


        if float(last) < MIN or float(last) > MAX:
            #VARLIKLARIM
            print(f"{bcolors.OKCYAN}VARLIKLARIM:{bcolors.ENDC}")
            my_assets = check_balances(PAIR_SYMBOL)
            print("my_assets", my_assets)

            #AÇIK EMİRLERİM
            my_open_orders = check_open_orders(PAIR_SYMBOL)


            # hesabımda NEO'varsa ve NEO değeri 170 üzerine çıkarsa satış emri ver.
            if my_open_orders == "":
                if float(my_assets["NEO"]) > 0 and float(last) > MAX:
                    _pairSymbol = "NEO_TRY"
                    _price = last
                    _quantity = my_assets["NEO"]
                    _orderType = "sell"
                    _orderMethod = "limit"
                    _stopPrice = "0"

                    result = create_order(_pairSymbol, _price, _quantity, _orderType, _orderMethod, _stopPrice)
                    if type(result) == int:
                        print(f"{OKGREEN.OKCYAN}SATIŞ EMRİ BAŞARIYLA VERİLDİ :){bcolors.ENDC}")
                        if my_update:
                            my_update.message.reply_text("SATIŞ EMRİ BAŞARIYLA VERİLDİ :)")
                    else:
                        print(f"{OKGREEN.FAIL}SATIŞ EMRİ VERİLİRKEN BİR HATA OLUŞTU!{bcolors.ENDC}")
                        if my_update:
                            my_update.message.reply_text("SATIŞ EMRİ VERİLİRKEN BİR HATA OLUŞTU!")
                        
                    print(result)



                # hesabımda TL'varsa ve NEO değeri 165 altına inerse alış emri ver.
                elif float(my_assets["TRY"]) > 10 and float(last) < MIN:
                    _pairSymbol = "NEO_TRY"
                    _price = last
                    _quantity = my_assets["TRY"]
                    _orderType = "buy"
                    _orderMethod = "limit"
                    _stopPrice = "0"

                    create_order(_pairSymbol, _price, _quantity, _orderType, _orderMethod, _stopPrice)   
                    if type(result) == int:
                        print(f"{OKGREEN.OKCYAN}ALIŞ EMRİ BAŞARIYLA VERİLDİ :){bcolors.ENDC}")
                        if my_update:
                            my_update.message.reply_text("SATIŞ EMRİ BAŞARIYLA VERİLDİ :)")
                    else:
                        print(f"{OKGREEN.FAIL}ALIŞ EMRİ VERİLİRKEN BİR HATA OLUŞTU!{bcolors.ENDC}")
                        if my_update:
                            my_update.message.reply_text("SATIŞ EMRİ VERİLİRKEN BİR HATA OLUŞTU!")
                    print(result)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")
    if my_update:
        my_update.message.reply_text("WS Connection Close!")


def on_open(ws):
    def run(*args):
        time.sleep(1)
        message = [
            151,
            {
                "type": 151,
                "channel": 'ticker',
                "event": 'NEOTRY',
                "join": True
            }
        ]
        ws.send(json.dumps(message))
    thread.start_new_thread(run, ())
    thread.start_new_thread(bot_main, ())


#Telegram Bot
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hi! Satoshi Başladı :) - Min:{0}, Max:{1}".format(MIN, MAX))
    global my_update
    my_update = update


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)
    
def bot_main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1493363690:AAE9jLKy1tr1IcHwh1NuN7kK4Is76s9TwSw", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    if API_PUBLIC_KEY and API_PRIVATE_KEY:
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            "wss://ws-feed-pro.btcturk.com/",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close)

        ws.on_open = on_open
        ws.run_forever()