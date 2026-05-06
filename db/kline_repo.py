# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional
from db.manager import DBManager


class KlineData:
    def __init__(
        self,
        symbol: str,
        interval: str,
        open_time: int,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        close_time: int,
        turnover: float = 0,
        trade_count: int = 0,
        buy_volume: float = 0,
        buy_turnover: float = 0,
        is_candle_closed: int = 1,
        id: int = None,
    ):
        self.id = id
        self.symbol = symbol
        self.interval = interval
        self.open_time = open_time
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.close_time = close_time
        self.turnover = turnover
        self.trade_count = trade_count
        self.buy_volume = buy_volume
        self.buy_turnover = buy_turnover
        self.is_candle_closed = is_candle_closed

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.interval,
            self.open_time,
            self.open_price,
            self.high_price,
            self.low_price,
            self.close_price,
            self.volume,
            self.close_time,
            self.turnover,
            self.trade_count,
            self.buy_volume,
            self.buy_turnover,
            self.is_candle_closed,
        )

    @classmethod
    def from_row(cls, row: dict) -> "KlineData":
        return cls(
            id=row["id"],
            symbol=row["symbol"],
            interval=row["interval"],
            open_time=row["open_time"],
            open_price=row["open_price"],
            high_price=row["high_price"],
            low_price=row["low_price"],
            close_price=row["close_price"],
            volume=row["volume"],
            close_time=row["close_time"],
            turnover=row.get("turnover", 0),
            trade_count=row.get("trade_count", 0),
            buy_volume=row.get("buy_volume", 0),
            buy_turnover=row.get("buy_turnover", 0),
            is_candle_closed=row.get("is_candle_closed", 1),
        )


class KlineRepo:
    def __init__(self, db_manager: DBManager = None):
        self.db_manager = db_manager or DBManager.get_instance()

    def save(self, kline: KlineData) -> int:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO kline_data 
                (symbol, interval, open_time, open_price, high_price, low_price, 
                 close_price, volume, close_time, turnover, trade_count, 
                 buy_volume, buy_turnover, is_candle_closed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                kline.to_tuple(),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def save_batch(self, klines: List[KlineData]) -> int:
        if not klines:
            return 0
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO kline_data 
                (symbol, interval, open_time, open_price, high_price, low_price, 
                 close_price, volume, close_time, turnover, trade_count, 
                 buy_volume, buy_turnover, is_candle_closed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [k.to_tuple() for k in klines],
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def get_by_symbol_interval(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: int = None,
        end_time: int = None,
    ) -> List[KlineData]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            sql = "SELECT * FROM kline_data WHERE symbol = ? AND interval = ?"
            params = [symbol, interval]

            if start_time is not None:
                sql += " AND open_time >= ?"
                params.append(start_time)
            if end_time is not None:
                sql += " AND open_time <= ?"
                params.append(end_time)

            sql += " ORDER BY open_time ASC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [KlineData.from_row(dict(row)) for row in rows]
        finally:
            conn.close()

    def get_latest(self, symbol: str, interval: str) -> Optional[KlineData]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM kline_data 
                WHERE symbol = ? AND interval = ?
                ORDER BY open_time DESC 
                LIMIT 1
                """,
                (symbol, interval),
            )
            row = cursor.fetchone()
            return KlineData.from_row(dict(row)) if row else None
        finally:
            conn.close()

    def delete_old_data(self, days: int = 30) -> int:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            timestamp = int((datetime.now().timestamp() - days * 86400) * 1000)
            cursor.execute(
                "DELETE FROM kline_data WHERE open_time < ?", (timestamp,)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
