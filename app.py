from flask import Flask, request
import json
import os
from oandaAPI import Oanda

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def main():

    reqData = json.loads(request.data)
    order = Oanda(reqData)
    msg = order.order()
    return msg


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
