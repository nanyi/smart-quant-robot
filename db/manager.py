# -*- coding: utf-8 -*-
import os
import sqlite3


class DBManager:
    _instance = None
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()
    
    @classmethod
    def get_instance(cls, db_path: str = None):
        if cls._instance is None:
            if db_path is None:
                from runtime_config import config
                db_path = config.get('sqlite.db_path', './data/db/smart_quant_robot.db')
            cls._instance = cls(db_path)
        return cls._instance
    
    def _ensure_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_kline_table(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kline_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    open_time INTEGER NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    close_time INTEGER NOT NULL,
                    turnover REAL DEFAULT 0,
                    trade_count INTEGER DEFAULT 0,
                    buy_volume REAL DEFAULT 0,
                    buy_turnover REAL DEFAULT 0,
                    is_candle_closed INTEGER DEFAULT 1,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval, open_time)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_kline_symbol_interval ON kline_data(symbol, interval)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_kline_open_time ON kline_data(open_time)')
            conn.commit()
        finally:
            conn.close()