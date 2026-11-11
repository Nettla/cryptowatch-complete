# CryptoWatch Complete

Self-hosted Ethereum market monitoring application using Python, FastAPI,
PostgreSQL and Docker.

## Features

- Live ETH prices from Binance, Coinbase, Kraken and Bitstamp
- Automatic market data collection
- Historical price storage in PostgreSQL 17
- REST API and web dashboard
- Historical market-average chart
- Manual price refresh
- Isolated Docker Compose deployment

## Architecture

The application consists of six services:

- API: FastAPI backend and web dashboard
- PostgreSQL: persistent market history
- Binance collector
- Coinbase collector
- Kraken collector
- Bitstamp collector

The four collectors share the same Python implementation.

## Requirements

- Docker Engine and Docker Compose
- Internet access
- Permission to execute Docker commands

## Installation

Copy the example configuration:

    cp .env.example .env

Edit .env and replace REPLACE_WITH_A_NEW_RANDOM_PASSWORD
with a newly generated database password.

Never commit .env to Git.

Validate the configuration:

    docker compose config --quiet

Start the application:

    docker compose up -d --build

If Docker requires administrative permissions, use sudo.

Open the dashboard:

    http://127.0.0.1:8096

The port is configurable using CRYPTOWATCH_PORT.

## API

- GET /health
- GET /prices/latest
- GET /prices/history
- GET /prices/average-history
- POST /prices/manual-refresh
- GET / (web dashboard)

## Market Data

The application continuously collects live ETH prices.

Collection frequency is configured through CHECK_INTERVAL.

The dashboard refreshes independently of background collectors.

Manual refresh retrieves new prices from all four exchanges
and stores successful observations in PostgreSQL.

Binance uses ETH/USDT, while the other exchanges use ETH/USD.
These market pairs are not perfectly interchangeable.

## Database

A fresh installation creates a separate PostgreSQL database.

The initial database schema is defined in database/init.sql.

Historical data is not required for the application to run.
History starts accumulating when collectors begin operating.

## Demo Edition

CryptoWatch Portable V7 is a separate demonstration edition
using simulated market data.

CryptoWatch Complete uses live exchange prices and PostgreSQL.

## Security

- Never commit credentials or .env files.
- Generate unique database passwords.
- Keep API access bound to localhost by default.
- Do not distribute production database volumes or backups.

## Verification

Check the status of all six services:

    docker compose ps

Check API availability:

    curl -fsS http://127.0.0.1:8096/health

Check the latest collected prices:

    curl -fsS http://127.0.0.1:8096/prices/latest

Trigger a manual price refresh:

    curl -fsS -X POST http://127.0.0.1:8096/prices/manual-refresh

Use sudo before Docker commands if Docker daemon access requires it.

## Operations

View recent application logs:

    docker compose logs --tail=50 api

View collector logs:

    docker compose logs --tail=50 binance-collector

Stop only this Compose deployment:

    docker compose down

Do not add the -v option unless you intentionally want to remove
the deployment's named database volume and its stored market history.

## Historical Data

A new installation starts with an empty prices table.

The chart gradually accumulates historical observations as the
collectors run. The application does not automatically import
older market history.

Any optional historical dataset should be documented separately
and must not contain credentials or production database backups.

## Distribution

CryptoWatch Complete is the live-data implementation.

CryptoWatch Portable V7 is a separate demo edition and is not
included automatically by this source directory.

## License

No license has been assigned. All rights reserved.
