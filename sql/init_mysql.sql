-- Smart Quant Robot 数据库初始化脚本
CREATE DATABASE IF NOT EXISTS smart_quant_robot DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smart_quant_robot;

-- 币安配置表
CREATE TABLE IF NOT EXISTS `binance_config` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `api_key` VARCHAR(256) NOT NULL COMMENT '币安API密钥',
  `api_secret` VARCHAR(256) NOT NULL COMMENT '币安API私钥',
  `dingding_token` VARCHAR(256) DEFAULT '' COMMENT '钉钉主token',
  `dingding_token2` VARCHAR(256) DEFAULT '' COMMENT '钉钉备用token',
  `weixin_enabled` TINYINT DEFAULT 0 COMMENT '是否启用企业微信',
  `weixin_corp_id` VARCHAR(128) DEFAULT '' COMMENT '企业微信CorpID',
  `weixin_secret` VARCHAR(256) DEFAULT '' COMMENT '企业微信Secret',
  `weixin_agent_id` INT DEFAULT 0 COMMENT '企业微信AgentID',
  `weixin_to_user` VARCHAR(64) DEFAULT '@all' COMMENT '企业微信ToUser',
  `enabled` TINYINT DEFAULT 1 COMMENT '是否启用此配置（1=启用，0=禁用）',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='币安API配置表';

-- 插入默认配置（测试用）
INSERT INTO `binance_config` (`api_key`, `api_secret`, `dingding_token`, `dingding_token2`, `weixin_enabled`, `weixin_corp_id`, `weixin_secret`, `weixin_agent_id`, `weixin_to_user`, `enabled`) VALUES ('', '', '', '', 0, '', '', 0, '@all', 1);