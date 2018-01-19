import time
from decimal import Decimal

import bitfinex.bitfinex as bitfinex
import numpy as np
import pandas as pd
from bitfinex_bot.Indicator import Indicator


class Bot:
    coinPairs = ['btcusd', 'ethusd', 'iotusd', 'xrpusd', 'ltcusd',
                'zecusd', 'dshusd', 'eosusd', 'neousd', 'etcusd']

    publicV1 = bitfinex.PublicV1()
    publicV2 = bitfinex.PublicV2()

    f = open("account_info.txt", 'r')
    message = f.read().split("\n")

    tradingV1 = bitfinex.TradingV1(message[0], message[1])
    tradingV2 = bitfinex.Trading_v2(message[0], message[1])

    # parameters

    maxSpendInUSD = 75
    maxNumberOfCurrencies = 5
    interval = ["1h"]

    def __init__(self):

        self.USD = 0  # available USD dollars
        self.balance = []  # shows currencies with amounts(0.0 currencies are also included)
        self.available_currencies = []  # shows only available currencies
        self.refreshBalance()
        print("Bot initialized")

    def run(self):
        print("Bot is running")
        while True:
            for coin in self.coinPairs:
                buy = 0
                sell = 0

                for minute in self.interval:
                    try:
                        array = np.array(self.publicV2.candles(minute, "t" + coin.upper(), "hist"))[::-1]
                        df = pd.DataFrame(data=array[:,0:6],
                                          columns=["date", "open", "close", "high", "low", "volume"])

                        indicator = Indicator(df)
                        signal = indicator.signal()

                        if (signal == 1):
                            buy = buy + 1
                        elif (signal == -1):
                            sell = sell + 1
                        time.sleep(15.0)

                    except Exception as ex:
                        time.sleep(75.0)
                        print(ex)
                        pass

                if(buy == len(self.interval)):
                    self.buyCoin(coin, str(df["close"][len(df) - 1]))

                elif(sell == len(self.interval)):
                    self.sellCoin(coin, df["close"][len(df) - 1])


    def buyCoin(self, coin, price):
        self.refreshBalance()
        if (coin not in self.available_currencies):
            print("Buying coin attempt: " + coin)
            print("Available currencies: " + str(self.available_currencies))
            print("Don't have it")
            if (len(self.available_currencies) >= self.maxNumberOfCurrencies):
                print("More than", self.maxNumberOfCurrencies ,"currencies")
                if (self.coinPairs.index(coin) < self.coinPairs.index(self.available_currencies[len(self.available_currencies) - 1])):
                    print(str(coin) + "is more valuable than " + str(self.available_currencies[len(self.available_currencies) - 1]))
                    self.sellCoin(self.available_currencies[len(self.available_currencies) - 1], 1.0)
                    time.sleep(60.0)
                    self.refreshBalance()
                    amount = (min(self.maxSpendInUSD, Decimal(self.USD)) - 2) / Decimal(price)
                    print("Buying", amount, coin, "at", price)
                    self.tradingV1.new_order(coin, amount, price, "buy", "exchange market", exchange='bitfinex', use_all_available=False)

                else:
                    print("Coin not valuable to sell available currencies")
            else:
                amount = (min(self.maxSpendInUSD, Decimal(self.USD)) - 2) / Decimal(price)
                print("Buying", amount, coin, "at", price)
                self.tradingV1.new_order(coin, amount, Decimal(price), "buy", "exchange market", exchange='bitfinex', use_all_available=False)
                self.refreshBalance()

    def sellCoin(self, coin, price):
        self.refreshBalance()
        if (coin in self.available_currencies):
            print("Selling coin attempt: " + coin)
            print("Available currencies: " + str(self.available_currencies))
            amount = "0"
            for dict in self.balance:
                if dict["currency"] == coin:
                    amount = dict["amount"]
            print("Selling", amount, coin, "at", price)
            self.tradingV1.new_order(coin, amount, price, "sell", "exchange market", exchange='bitfinex', use_all_available=True)
            self.refreshBalance()

    def refreshBalance(self):
        balance = self.tradingV1.balances()
        if(balance != None):
            self.available_currencies = []
            self.balance = []
            for dict in balance:
                if dict["currency"] == "usd":
                    self.USD = dict["amount"]
                elif (dict["amount"] != "0.0"):
                    dict["currency"]= dict["currency"] + "usd"
                    self.available_currencies.append(dict["currency"])
                    self.balance.append(dict)
            self.available_currencies = self.sort(self.available_currencies)

    def sort(self, currency_list):
        index_currency_dict = {}
        res = []
        for currency in currency_list:
            index_currency_dict[self.coinPairs.index(currency)] = currency

        for key in sorted(index_currency_dict):
            res.append(index_currency_dict[key])

        return res
