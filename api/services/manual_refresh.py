import json
import math
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

EXCHANGES = {'binance': {'symbol': 'ETHUSDT',
             'url': 'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT'},
 'bitstamp': {'symbol': 'ETH/USD',
              'url': 'https://www.bitstamp.net/api/v2/ticker/ethusd/'},
 'coinbase': {'symbol': 'ETH-USD',
              'url': 'https://api.exchange.coinbase.com/products/ETH-USD/ticker'},
 'kraken': {'symbol': 'ETH/USD',
            'url': 'https://api.kraken.com/0/public/Ticker?pair=ETHUSD'}}

_refresh_lock = threading.Lock()


def fetch_price(exchange):
    config = EXCHANGES[exchange]
    request = urllib.request.Request(
        config["url"],
        headers={"User-Agent": "CryptoWatch/1.0"},
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.load(response)

    if exchange == "kraken":
        if data.get("error"):
            raise ValueError("Exchange returned an error")
        ticker = next(iter(data["result"].values()))
        price = float(ticker["c"][0])
    elif exchange == "bitstamp":
        price = float(data["last"])
    else:
        price = float(data["price"])

    if not math.isfinite(price) or price <= 0:
        raise ValueError("Invalid exchange price")

    return exchange, config["symbol"], price


def run_manual_refresh(get_connection):
    if not _refresh_lock.acquire(blocking=False):
        return {"status": "busy", "updated": 0, "failed": []}

    try:
        results = []
        failed = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            jobs = {
                executor.submit(fetch_price, exchange): exchange
                for exchange in EXCHANGES
            }

            for future in as_completed(jobs):
                exchange = jobs[future]
                try:
                    results.append(future.result())
                except Exception:
                    failed.append(exchange)

        if not results:
            return {
                "status": "unavailable",
                "updated": 0,
                "failed": sorted(failed),
            }

        with get_connection() as connection:
            with connection.cursor() as cursor:
                for exchange, symbol, price in results:
                    cursor.execute(
                        """
                        INSERT INTO prices (exchange, symbol, price)
                        VALUES (%s, %s, %s)
                        """,
                        (exchange, symbol, str(price)),
                    )

        return {
            "status": "ok" if not failed else "partial",
            "updated": len(results),
            "failed": sorted(failed),
        }
    finally:
        _refresh_lock.release()
