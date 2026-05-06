# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional

from db.manager import DBManager
from db.kline_data import KlineData


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

    def get_oldest(self, symbol: str, interval: str) -> Optional[KlineData]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM kline_data 
                WHERE symbol = ? AND interval = ?
                ORDER BY open_time ASC 
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

    def count(self, symbol: str = None, interval: str = None) -> int:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            if symbol and interval:
                cursor.execute(
                    "SELECT COUNT(*) FROM kline_data WHERE symbol = ? AND interval = ?",
                    (symbol, interval),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM kline_data")
            return cursor.fetchone()[0]
        finally:
            conn.close()
