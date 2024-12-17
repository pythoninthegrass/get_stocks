#!/usr/bin/env python

import sqlite3
from decouple import config
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from stockstir import Stockstir


@dataclass
class DatabaseManager:
    """
    Manages database connections and operations for storing and retrieving stock prices.
    """

    db_name: str
    conn: sqlite3.Connection = field(init=False, default=None)
    cursor: sqlite3.Cursor = field(init=False, default=None)

    def __enter__(self):
        self.create_connection()
        if config("DROP_DB", default=False, cast=bool):
            self.wipe_database()
        self.initialize_table()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def create_connection(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def wipe_database(self):
        """
        Drops all tables in the database.
        """
        self.cursor.execute("DROP TABLE IF EXISTS stock_data")
        self.cursor.execute("DROP TABLE IF EXISTS ticker")
        self.cursor.execute("DROP TABLE IF EXISTS price")
        self.cursor.execute("DROP TABLE IF EXISTS date")
        self.conn.commit()

    def initialize_table(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS ticker
                               (id INTEGER PRIMARY KEY, symbol TEXT UNIQUE)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS price
                               (id INTEGER PRIMARY KEY, value FLOAT)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS date
                               (id INTEGER PRIMARY KEY, timestamp DATETIME)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS stock_data
                               (ticker_id INTEGER, price_id INTEGER, date_id INTEGER,
                                FOREIGN KEY (ticker_id) REFERENCES ticker(id),
                                FOREIGN KEY (price_id) REFERENCES price(id),
                                FOREIGN KEY (date_id) REFERENCES date(id))""")
        self.conn.commit()

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def get_price(self, symbol, ttl_minutes):
        self.cursor.execute(
            """SELECT price.value, date.timestamp FROM stock_data
                               JOIN ticker ON stock_data.ticker_id = ticker.id
                               JOIN price ON stock_data.price_id = price.id
                               JOIN date ON stock_data.date_id = date.id
                               WHERE ticker.symbol = ?""",
            (symbol,),
        )
        if result := self.cursor.fetchone():
            price, timestamp = result
            if datetime.now() - datetime.fromisoformat(timestamp) < timedelta(
                minutes=ttl_minutes
            ):
                return price
        return None

    def store_price(self, symbol, price):
        self.cursor.execute(
            "INSERT OR IGNORE INTO ticker (symbol) VALUES (?)", (symbol,)
        )
        self.cursor.execute("INSERT INTO price (value) VALUES (?)", (price,))
        self.cursor.execute(
            "INSERT INTO date (timestamp) VALUES (?)", (datetime.now().isoformat(),)
        )
        self.cursor.execute(
            """INSERT INTO stock_data (ticker_id, price_id, date_id)
                               VALUES ((SELECT id FROM ticker WHERE symbol = ?),
                                       (SELECT id FROM price ORDER BY id DESC LIMIT 1),
                                       (SELECT id FROM date ORDER BY id DESC LIMIT 1))""",
            (symbol,),
        )
        self.conn.commit()


def get_stock_prices(tickers, ttl_minutes):
    """
    Retrieves and prints stock prices for the given tickers, using cached values if within TTL.
    """

    stockstir = Stockstir(print_output=True, random_user_agent=True, provider="cnbc")

    with DatabaseManager("stock_prices.db") as db:
        for ticker in tickers:
            price = db.get_price(ticker, ttl_minutes)
            if price is None:
                try:
                    price = stockstir.tools.get_single_price(ticker)
                    db.store_price(ticker, price)
                except Exception as e:
                    print(f"\nError fetching price for {ticker}: {str(e)}")
                    continue
            print(f"Ticker: {ticker:<6} Price: {price:>8.2f}")


def main():
    tickers = config("TICKERS", default="AAPL").split(",")
    ttl_minutes = int(config("TTL", default=5))
    get_stock_prices(tickers, ttl_minutes)


if __name__ == "__main__":
    main()
