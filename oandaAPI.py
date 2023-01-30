import requests
import json
import re
import datetime
import math
from datetime import timedelta, timezone
from decimal import Decimal


class TradingView:
    def __init__(self, reqData) -> None:
        if reqData.get("PASSWORD"):
            if self.passwordVerify(reqData["PASSWORD"]):
                self.defData(reqData)
            else:
                raise {"code": "error", "message": "Nice try"}
        else:
            raise {"code": "error", "message": "Password Empty"}

    def passwordVerify(self, password):
        with open("./config.json") as f:
            config = json.load(f)
        if password == config["TRADINGVIEW"]["TRADINGVIEW_PASSWD"]:
            return True
        else:
            return False

    def defData(self, reqData):
        self.total_order = reqData["TOTAL_ORDER"]
        self.instrument = re.sub(r"([A-Z]{3})([A-Z]{3})", r"\1_\2", reqData["TICKER"])
        if reqData["SIDE"] == "buy":
            self.side = 1
        elif reqData["SIDE"] == "sell":
            self.side = -1
        else:
            self.side = 0
        roundC = len(str(reqData["ORDER_PRICE"]).split(".")[1])
        self.order_price = Decimal(str(reqData["ORDER_PRICE"]))
        self.limit_price = Decimal(str(round(reqData["LIMIT_PRICE"], roundC)))
        self.stop_price = Decimal(str(round(reqData["STOP_PRICE"], roundC)))
        self.order_time = reqData["ORDER_TIME"] / 1000


class Oanda(TradingView):
    def __init__(self, reqData) -> None:
        TradingView.__init__(self, reqData)

        with open("./config.json") as f:
            data = json.load(f)
            self.headers = {"Authorization": "Bearer " + data["OANDA"]["OANDA_TOEKN"]}

        self.accountId = self.requestGet(
            "https://api-fxpractice.oanda.com/v3/accounts"
        )["accounts"][0]["id"]

        self.balance = Decimal(
            str(
                self.requestGet(
                    "https://api-fxpractice.oanda.com/v3/accounts/" + self.accountId
                )["account"]["balance"]
            )
        )

        self.marginAva = Decimal(
            str(
                self.requestGet(
                    "https://api-fxpractice.oanda.com/v3/accounts/" + self.accountId
                )["account"]["marginAvailable"]
            )
        )

        self.tradingCount = len(
            self.requestGet(
                "https://api-fxpractice.oanda.com/v3/accounts/" + self.accountId
            )["account"]["trades"]
        )
        if self.total_order - self.tradingCount >= 1:
            self.perAmount = Decimal(
                str(
                    (self.marginAva - self.balance * Decimal(str(0.2)))
                    / (self.total_order - self.tradingCount)
                )
            )

        else:
            raise {"code": "error", "message": "TradingCount too much."}

        if self.perAmount < 1:
            raise {"code": "error", "message": "Balance not enough."}

    def requestGet(self, url):
        r = requests.get(
            url=url,
            headers=self.headers,
        )
        response = r.json()
        return response

    def requestPost(self, url):
        r = requests.post(
            url=url,
            headers=self.headers,
            json=self.orderData,
        )
        response = r.json()
        return response

    def order(self):
        if self.side == 0:
            return "It's close"
        else:
            rfc3339_order_time = datetime.datetime.fromtimestamp(
                self.order_time, timezone(timedelta(hours=8))
            ) + timedelta(minutes=2)
            self.unit = math.floor(self.perAmount / self.order_price * 50 * self.side)
            self.orderData = {
                "order": {
                    "instrument": self.instrument,
                    "type": "MARKET_IF_TOUCHED",
                    "units": self.unit,
                    "price": str(self.order_price),
                    "timeInForce": "GTD",
                    "gtdTime": rfc3339_order_time.isoformat(),
                    "stopLossOnFill": {"price": str(self.stop_price)},
                    "takeProfitOnFill": {"price": str(self.limit_price)},
                }
            }
            orderResp = self.requestPost(
                "https://api-fxpractice.oanda.com/v3/accounts/"
                + self.accountId
                + "/orders"
            )
            return orderResp
