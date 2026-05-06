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