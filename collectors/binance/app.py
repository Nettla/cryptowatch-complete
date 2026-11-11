
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
CHECK_INTERVAL = 300


def fetch_eth_price():
    # Fetch the current ETH/USDT price from Binance
    with urllib.request.urlopen(API_URL, timeout=10) as response:
        data = json.load(response)

    return float(data["price"])


def log_event(level, message, price=None):
    # Write structured JSON logs
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "exchange": "binance",
        "level": level,
        "message": message,
    }

    if price is not None:
        entry["symbol"] = "ETHUSDT"
        entry["price"] = price

    print(json.dumps(entry), flush=True)


def main():
    log_event("INFO", "Collector started")

    while True:
        try:
            price = fetch_eth_price()
            log_event("INFO", "Price fetched successfully", price)

        except (urllib.error.URLError, ValueError, KeyError) as error:
            # Log API errors and retry during the next cycle
            log_event("ERROR", str(error))

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
