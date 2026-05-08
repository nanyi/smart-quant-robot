# -*- coding: utf-8 -*-
import copy
import os
from typing import Any

import sqlite3
import yaml

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_YAML = os.path.join(REPO_ROOT, 'config.yaml')

_DEFAULT_CONFIG = {
    'binance': {
        'api_key': '',
        'api_secret': '',
        'recv_window': 5000,
        'proxy': {
            'enabled': False,
            'host': '127.0.0.1',
            'port': 7890,
        },
    },
    'dingding': {
        'enabled': True,
        'token': '',
        'token2': '',
    },
    'notifier': {
        'enabled': True,
        'provider': 'dingding',
    },
    'weixin': {
        'enabled': False,
        'corp_id': '',
        'secret': '',
        'agent_id': 0,
        'to_user': '@all',
    },
    'trade': {
        'kLine_type': '15m',
        'binance_market': 'SPOT',
        'binance_coinBase': 'USDT',
        'binance_coinBase_count': 20,
        'binance_tradeCoin': 'DOGE',
        'isOpenSellStrategy': True,
        'sellStrategy1': {'profit': 1.05, 'sell': 0.1},
        'sellStrategy2': {'profit': 1.10, 'sell': 0.2},
        'sellStrategy3': {'profit': 1.20, 'sell': 0.2},
    },
    'sqlite': {
        'enabled': False,
        'db_path': './data/db/smart_quant_robot.db',
    },
    'strategy': {
        'enabled_strategies': ['ma'],
        'weights': {
            'ma': 1.0,
            'rsi': 0.8,
            'bollinger': 0.8,
            'macd': 0.8,
            'volatility': 0.7,
            'volume': 0.7,
            'lifemore': 1.0,
            'turtle': 1.0
        },
        'threshold': 0.5,
        'ma': {
            'short_period': 5,
            'long_period': 60
        },
        'lifemore': {
            'breakout_period': 30,
            'pyramid_ratio': 0.05,
            'stop_loss_ratio': 0.10,
            'exit_ratio': 0.20
        },
        'turtle': {
            'entry_period': 20,
            'exit_period': 10,
            'atr_period': 20,
            'risk_ratio': 0.02,
            'max_units': 4
        }
    },
    'backtest': {
        'enabled': True,
        'initial_capital': 10000.0,
        'commission_rate': 0.001,
        'data_limit': 1000,
    },
}


def _deep_merge_dict(base: dict, override: dict) -> dict:
    """深度合并字典"""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_config(data: dict) -> dict:
    """标准化配置数据（键名小写化）"""
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for section, section_values in data.items():
        section_name = str(section).strip().lower()
        if not section_name or not isinstance(section_values, dict):
            continue
        normalized[section_name] = {}
        for key, value in section_values.items():
            normalized[section_name][str(key).strip()] = value
    return normalized


class Config:
    """全局配置单例"""
    _instance = None

    def __init__(self, _supper: Any = None, _config: dict = None):
        """初始化配置"""
        self._supper = _supper
        if _config:
            self._config = _config
        else:
            self._config = copy.deepcopy(_DEFAULT_CONFIG)
            self._load_from_yaml()
            self._load_from_sqlite()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_from_yaml(self):
        """从 YAML 文件加载配置"""
        if not os.path.exists(CONFIG_YAML):
            print(f'配置文件不存在，将创建默认配置: {CONFIG_YAML}')
            self._save_yaml(self._config)
            return

        try:
            with open(CONFIG_YAML, 'rt', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}
            normalized = _normalize_config(yaml_data)
            self._config = _deep_merge_dict(self._config, normalized)
            print(f'已从 YAML 加载配置: {CONFIG_YAML}')
        except Exception as e:
            print(f'YAML 解析失败，使用默认配置: {e}')

    def _load_from_sqlite(self):
        """从 SQLite 数据库加载 Binance API 配置"""
        sqlite_config = self._config.get('sqlite', {})
        if not sqlite_config.get('enabled', False):
            print('SQLite 配置未启用，跳过从数据库加载')
            return

        db_path = sqlite_config.get('db_path', './data/db/smart_quant_robot.db')
        
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f'创建数据库目录: {db_dir}')

        # 如果数据库文件不存在，先创建
        if not os.path.exists(db_path):
            print(f'数据库文件不存在，将创建: {db_path}')
            self._init_sqlite_db(db_path)
            return

        try:
            connection = sqlite3.connect(db_path, check_same_thread=False)
            connection.row_factory = sqlite3.Row
            try:
                cursor = connection.cursor()
                cursor.execute(
                    'SELECT api_key, api_secret, dingding_token, dingding_token2 FROM binance_config WHERE enabled = 1 ORDER BY id DESC LIMIT 1'
                )
                result = cursor.fetchone()
                if result:
                    if result['api_key']:
                        self._config['binance']['api_key'] = result['api_key']
                        self._config['binance']['api_secret'] = result['api_secret']
                        print('已从 SQLite 加载 Binance API 配置')
                    if result['dingding_token'] is not None:
                        self._config['dingding']['token'] = result['dingding_token']
                        print('已从 SQLite 加载钉钉配置')
                    if result['dingding_token2'] is not None:
                        self._config['dingding']['token2'] = result['dingding_token2']
                else:
                    print('SQLite 中没有启用的 Binance 配置，使用 YAML 或默认配置')
            finally:
                connection.close()
        except Exception as e:
            print(f'SQLite 连接失败，使用 YAML 或默认配置: {e}')

    def _init_sqlite_db(self, db_path):
        """初始化 SQLite 数据库"""
        try:
            connection = sqlite3.connect(db_path, check_same_thread=False)
            connection.row_factory = sqlite3.Row
            try:
                cursor = connection.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS binance_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_key VARCHAR(256) NOT NULL,
                        api_secret VARCHAR(256) NOT NULL,
                        dingding_token VARCHAR(256) DEFAULT '',
                        dingding_token2 VARCHAR(256) DEFAULT '',
                        enabled INTEGER DEFAULT 1,
                        update_time DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute(
                    "INSERT OR IGNORE INTO binance_config (id, api_key, api_secret, dingding_token, dingding_token2, enabled) VALUES (1, '', '', '', '', 1)"
                )
                connection.commit()
                print(f'SQLite 数据库初始化完成: {db_path}')
            finally:
                connection.close()
        except Exception as e:
            print(f'SQLite 数据库初始化失败: {e}')

    def _save_yaml(self, data: dict):
        """保存配置到 YAML 文件"""
        try:
            with open(CONFIG_YAML, 'wt', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            print(f'保存 YAML 配置失败: {e}')

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号路径
        例如: config.get('binance.api_key')
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return (Config(self, value) if isinstance(value, dict) else value) if value is not None else default

    def set(self, key_path: str, value: Any):
        """设置配置值，支持点号路径"""
        keys = key_path.split('.')
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value


config = Config.get_instance()

if __name__ == '__main__':
    strategy_config = config.get('strategy')
    print(strategy_config)
    ma_config = strategy_config.get('ma')
    print(ma_config)
    print(ma_config.get('short_period'))
    print(config.get('strategy.ma.short_period'))
    ma_config.set('ssss', 22)
    print(config.get('strategy.ma.ssss'))
    print(ma_config.get('ssss'))