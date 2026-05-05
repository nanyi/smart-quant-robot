-- Smart Quant Robot 数据库初始化脚本
CREATE DATABASE IF NOT EXISTS smart_quant DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smart_quant;

-- 币安配置表
CREATE TABLE IF NOT EXISTS `binance_config` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `api_key` VARCHAR(256) NOT NULL COMMENT '币安API密钥',
  `api_secret` VARCHAR(256) NOT NULL COMMENT '币安API私钥',
  `enabled` TINYINT DEFAULT 1 COMMENT '是否启用此配置（1=启用，0=禁用）',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='币安API配置表';

-- 插入默认配置（测试用）
INSERT INTO `binance_config` (`api_key`, `api_secret`, `enabled`) VALUES ('', '', 1);