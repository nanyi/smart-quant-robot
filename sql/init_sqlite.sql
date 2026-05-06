-- Smart Quant Robot SQLite 数据库初始化脚本
-- 数据库文件保存在 /data/db/smart_quant_robot.db

-- 币安配置表
CREATE TABLE IF NOT EXISTS binance_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key VARCHAR(256) NOT NULL,
    api_secret VARCHAR(256) NOT NULL,
    dingding_token VARCHAR(256) DEFAULT '',
    dingding_token2 VARCHAR(256) DEFAULT '',
    enabled INTEGER DEFAULT 1,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置（测试用）
INSERT OR IGNORE INTO binance_config (id, api_key, api_secret, dingding_token, dingding_token2, enabled) 
VALUES (1, '', '', '', '', 1);

-- K线数据表
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
);

CREATE INDEX IF NOT EXISTS idx_kline_symbol_interval ON kline_data(symbol, interval);
CREATE INDEX IF NOT EXISTS idx_kline_open_time ON kline_data(open_time);