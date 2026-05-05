# -*- coding: utf-8 -*-
import copy
import os
from typing import Any

import pymysql
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
    'weixin': {
        'corp_id': '',
        'secret': '',
        'agent_id': 0,
        'to_user': '@all',
    },
    'trade': {
        'ma_x': 5,
        'ma_y': 60,
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
    'mysql': {
        'enabled': False,
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'smart_quant',
        'charset': 'utf8mb4',
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

    def __init__(self):
        self._config = copy.deepcopy(_DEFAULT_CONFIG)
        self._load_from_yaml()
        self._load_from_mysql()

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

    def _load_from_mysql(self):
        """从 MySQL 数据库加载 Binance API 配置"""
        mysql_config = self._config.get('mysql', {})
        if not mysql_config.get('enabled', False):
            print('MySQL 配置未启用，跳过从数据库加载')
            return

        try:
            connection = pymysql.connect(
                host=mysql_config.get('host', 'localhost'),
                port=int(mysql_config.get('port', 3306)),
                user=mysql_config.get('user', 'root'),
                password=mysql_config.get('password', ''),
                database=mysql_config.get('database', 'smart_quant'),
                charset=mysql_config.get('charset', 'utf8mb4'),
                connect_timeout=5
            )
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        'SELECT api_key, api_secret, dingding_token, dingding_token2 FROM binance_config WHERE enabled = 1 ORDER BY id DESC LIMIT 1'
                    )
                    result = cursor.fetchone()
                    if result:
                        if result.get('api_key'):
                            self._config['binance']['api_key'] = result['api_key']
                            self._config['binance']['api_secret'] = result['api_secret']
                            print('已从 MySQL 加载 Binance API 配置')
                        if result.get('dingding_token') is not None:
                            self._config['dingding']['token'] = result['dingding_token']
                            print('已从 MySQL 加载钉钉配置')
                        if result.get('dingding_token2') is not None:
                            self._config['dingding']['token2'] = result['dingding_token2']
                    else:
                        print('MySQL 中没有启用的 Binance 配置，使用 YAML 或默认配置')
            finally:
                connection.close()
        except Exception as e:
            print(f'MySQL 连接失败，使用 YAML 或默认配置: {e}')

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
        return value if value is not None else default

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
