import os
import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from psycopg.rows import dict_row

app = FastAPI(title="CryptoWatch API", version="1.0.0")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "postgres"),
        dbname=os.getenv("POSTGRES_DB", "cryptowatch"),
        user=os.getenv("POSTGRES_USER", "cryptowatch"),
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "cryptowatch-api"}


@app.get("/prices/latest")
def latest_prices():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT ON (exchange)
                    exchange,
                    symbol,
                    price,
                    recorded_at
                FROM prices
                ORDER BY exchange, recorded_at DESC, id DESC
            """)
            rows = cursor.fetchall()

    return {
        "count": len(rows),
        "prices": [
            {
                "exchange": row["exchange"],
                "symbol": row["symbol"],
                "price": str(row["price"]),
                "recorded_at": row["recorded_at"].isoformat(),
            }
            for row in rows
        ],
    }
@app.get("/prices/history")
def price_history(exchange: str = "coinbase", limit: int = 100):
    allowed_exchanges = {
        "binance", "coinbase", "kraken", "bitstamp"
    }

    if exchange not in allowed_exchanges:
        raise HTTPException(
            status_code=400,
            detail="Unsupported exchange"
        )

    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 1000"
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT exchange, symbol, price, recorded_at
                FROM prices
                WHERE exchange = %s
                ORDER BY recorded_at DESC, id DESC
                LIMIT %s
                """,
                (exchange, limit),
            )
            rows = cursor.fetchall()

    return {
        "exchange": exchange,
        "count": len(rows),
        "prices": [
            {
                "symbol": row["symbol"],
                "price": str(row["price"]),
                "recorded_at": row["recorded_at"].isoformat(),
            }
            for row in reversed(rows)
        ],
    }

@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse("/app/static/index.html")


@app.get("/prices/average-history")
def average_price_history(limit: int = 100):
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 1000"
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH latest_per_exchange AS (
                    SELECT DISTINCT ON (bucket, exchange)
                        bucket,
                        exchange,
                        price
                    FROM (
                        SELECT
                            to_timestamp(
                                floor(
                                    extract(epoch FROM recorded_at)
                                    / 120
                                ) * 120
                            ) AS bucket,
                            exchange,
                            price,
                            recorded_at,
                            id
                        FROM prices
                        WHERE exchange IN (
                            'binance',
                            'coinbase',
                            'kraken',
                            'bitstamp'
                        )
                    ) AS grouped
                    ORDER BY
                        bucket DESC,
                        exchange,
                        recorded_at DESC,
                        id DESC
                ),
                averages AS (
                    SELECT
                        bucket,
                        AVG(price) AS average_price,
                        COUNT(DISTINCT exchange) AS exchange_count
                    FROM latest_per_exchange
                    GROUP BY bucket
                    HAVING COUNT(DISTINCT exchange) = 4
                    ORDER BY bucket DESC
                    LIMIT %s
                )
                SELECT
                    bucket,
                    average_price,
                    exchange_count
                FROM averages
                ORDER BY bucket ASC
                """,
                (limit,),
            )
            rows = cursor.fetchall()

    return {
        "count": len(rows),
        "interval_seconds": 120,
        "currency_note": (
            "Indicative average: Binance ETH/USDT "
            "and three ETH/USD markets."
        ),
        "prices": [
            {
                "recorded_at": row["bucket"].isoformat(),
                "average_price": str(row["average_price"]),
                "exchange_count": row["exchange_count"],
            }
            for row in rows
        ],
    }


@app.get("/chart.css", include_in_schema=False)
def chart_css():
    return FileResponse(
        "/app/static/chart.css",
        media_type="text/css"
    )


@app.get("/chart.js", include_in_schema=False)
def chart_js():
    return FileResponse(
        "/app/static/chart.js",
        media_type="application/javascript"
    )


from services.manual_refresh import run_manual_refresh


@app.post("/prices/manual-refresh")
def manual_refresh():
    result = run_manual_refresh(get_connection)

    if result["status"] == "busy":
        raise HTTPException(
            status_code=409,
            detail="Manual refresh already running",
        )

    if result["status"] == "unavailable":
        raise HTTPException(
            status_code=503,
            detail="Exchange prices temporarily unavailable",
        )

    return result
