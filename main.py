from environs import Env
import json
import pprint
import time

import websocket

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

PAIR_SYMBOL = "NEO_TRY"
SYMBOL = "NEO" 
MIN = 205#177
MAX = 210#182

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
    #print(result)

    return result

def check_balances(pair_symbol):
    my_assets = {}
    #print(f"{bcolors.OKCYAN}VARLIKLARIM:{bcolors.ENDC}")
    result = client.checkBalances(pair_symbol,format = "raw")
    for r in result:
        if r["asset"] in ["TRY","NEO", "BTC", "DOT"]:
            asset = r["asset"]
            balance = r["balance"]
            
            #print(f"{bcolors.OKCYAN}{asset}: {balance}{bcolors.ENDC}")

            my_assets[asset] = balance

    #print("\n")

    return my_assets


def buy_order(price, quantity):
    _pairSymbol = PAIR_SYMBOL
    #_price = last
    #_quantity = my_assets["TRY"]
    _orderType = "buy"
    _orderMethod = "limit"
    _stopPrice = "0"

    result = create_order(_pairSymbol, price, quantity, _orderType, _orderMethod, _stopPrice)  
    return type(result) == int

def sell_order(price, quantity):
    _pairSymbol = PAIR_SYMBOL
    #_price = last
    #_quantity = my_assets["NEO"]
    _orderType = "sell"
    _orderMethod = "limit"
    _stopPrice = "0"

    result = create_order(_pairSymbol, price, quantity, _orderType, _orderMethod, _stopPrice)
    return type(result) == int
    
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
            init_buy_sell_order()


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        time.sleep(1)
        message = [
            151,
            {
                "type": 151,
                "channel": 'ticker',
                "event": PAIR_SYMBOL.replace("_",""),
                "join": True
            }
        ]
        ws.send(json.dumps(message))
    thread.start_new_thread(run, ())


def init_buy_sell_order():
    #AÇIK EMİRLERİM
    my_open_orders = check_open_orders(PAIR_SYMBOL)
    print(f"{bcolors.OKCYAN}Açık Emirlerim:{bcolors.ENDC}")
    print("my_open_orders", my_open_orders)


    #Hiç bir açık emir yoksa ve varlıklarımda NEO varsa MAX tutardan varlıklarımdaki tüm NEO için SATIŞ emri ver
    if my_open_orders == "":
        #VARLIKLARIM
        print(f"{bcolors.OKCYAN}VARLIKLARIM:{bcolors.ENDC}")
        my_assets = check_balances(PAIR_SYMBOL)
        print("my_assets", my_assets)
    
        if float(my_assets[SYMBOL]) > 0:
            price = MAX
            quantity = my_assets[SYMBOL]

            result_sell = sell_order(price, quantity)
            
            if result_sell:
                print(f"{bcolors.OKGREEN}{MAX} TL'den SATIŞ EMRİ BAŞARIYLA VERİLDİ :){bcolors.ENDC}")
            else:
                print(f"{bcolors.FAIL}SATIŞ EMRİ VERİLİRKEN BİR HATA OLUŞTU!{bcolors.ENDC}")
                            
            print(result_sell)

        #Hiç bir açık emir yoksa ve varlıklarımda TL varsa MIN tutardan varlıklarımdaki tüm TL için ALIŞ emri ver
        elif float(my_assets["TRY"]) > 0:
            price = MIN
            quantity = (float(my_assets["TRY"]) / float(price)) * 0.999
            quantity = "{:.4f}".format(quantity)

            print("price", price)
            print("quantity", quantity)

            result_buy = buy_order(price, quantity)  

            if result_buy:
                print(f"{bcolors.OKGREEN} {MIN} TL'den ALIŞ EMRİ BAŞARIYLA VERİLDİ :){bcolors.ENDC}")
            else:
                print(f"{bcolors.FAIL}ALIŞ EMRİ VERİLİRKEN BİR HATA OLUŞTU!{bcolors.ENDC}")

            print(result_buy)


if __name__ == "__main__":
    if API_PUBLIC_KEY and API_PRIVATE_KEY:
        init_buy_sell_order()


        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            "wss://ws-feed-pro.btcturk.com/",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close)

        ws.on_open = on_open
        ws.run_forever()