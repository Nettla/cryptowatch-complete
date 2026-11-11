
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import psycopg


# Collector configuration
EXCHANGE = os.getenv("EXCHANGE", "binance").lower()
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "120"))

# PostgreSQL configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "cryptowatch")
DB_USER = os.getenv("POSTGRES_USER", "cryptowatch")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")


# Supported cryptocurrency exchanges
EXCHANGES = {
    "binance": {
        "url": "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
        "symbol": "ETHUSDT",
    },
    "coinbase": {
        "url": "https://api.exchange.coinbase.com/products/ETH-USD/ticker",
        "symbol": "ETH-USD",
    },
    "kraken": {
        "url": "https://api.kraken.com/0/public/Ticker?pair=ETHUSD",
        "symbol": "ETH/USD",
    },
    "bitstamp": {
        "url": "https://www.bitstamp.net/api/v2/ticker/ethusd/",
        "symbol": "ETH/USD",
    },
}


def log_event(level, message, **details):
    # Write structured JSON logs to Docker
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "exchange": EXCHANGE,
        "level": level,
        "message": message,
    }

    event.update(details)
    print(json.dumps(event), flush=True)


def fetch_eth_price():
    # Fetch the ETH price from the selected exchange
    config = EXCHANGES[EXCHANGE]

    request = urllib.request.Request(
        config["url"],
        headers={"User-Agent": "CryptoWatch/1.0"},
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.load(response)

    # Kraken uses a different API response structure
    if EXCHANGE == "kraken":
        if data.get("error"):
            raise ValueError(str(data["error"]))

        ticker = next(iter(data["result"].values()))
        return float(ticker["c"][0])

    # Bitstamp returns the latest price in "last"
    if EXCHANGE == "bitstamp":
        return float(data["last"])

    # Binance and Coinbase return the price in "price"
    return float(data["price"])


def save_price(price):
    # Store the collected price in PostgreSQL
    with psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO prices (exchange, symbol, price)
                VALUES (%s, %s, %s)
                """,
                (
                    EXCHANGE,
                    EXCHANGES[EXCHANGE]["symbol"],
                    str(price),
                ),
            )


def main():
    if EXCHANGE not in EXCHANGES:
        raise ValueError(f"Unsupported exchange: {EXCHANGE}")

    if CHECK_INTERVAL <= 0:
        raise ValueError("CHECK_INTERVAL must be positive")

    if not DB_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD is not configured")

    log_event("INFO", "Collector started")

    while True:
        try:
            price = fetch_eth_price()

            log_event(
                "INFO",
                "Price fetched successfully",
                symbol=EXCHANGES[EXCHANGE]["symbol"],
                price=price,
            )

            try:
                save_price(price)
                log_event("INFO", "Price saved to PostgreSQL")

            except psycopg.Error as error:
                log_event("ERROR", f"Database error: {error}")

        except (
            urllib.error.URLError,
            ValueError,
            KeyError,
            StopIteration,
            IndexError,
        ) as error:
            log_event("ERROR", str(error))

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
