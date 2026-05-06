# -*- coding: utf-8 -*-
import time
from typing import List, Optional

from app.BinanceAPI import BinanceAPI
from db.kline_repo import KlineRepo
from db.kline_data import KlineData


class KlineService:
    def __init__(self, binance_api: BinanceAPI = None, kline_repo: KlineRepo = None):
        self.binance_api = binance_api or BinanceAPI()
        self.kline_repo = kline_repo or KlineRepo()

    def fetch_and_save(self, symbol: str, interval: str, limit: int = 1000) -> int:
        """从Binance获取K线并存储到数据库
        
        :param symbol: 交易对符号，例如 'BTCUSDT'
        :param interval: K线周期，例如 '15m'
        :param limit: 获取数量，默认1000
        :return: 存储的K线数量
        """
        millis_stamp = int(round(time.time() * 1000))
        
        try:
            kline_json = self.binance_api.get_klines(symbol, interval, limit, None, millis_stamp)
            if not kline_json or not isinstance(kline_json, list):
                return 0
            
            klines = [KlineData.from_api_list(d, symbol, interval) for d in kline_json]
            count = self.kline_repo.save_batch(klines)
            print(f"已存储 {count} 条K线数据: {symbol} {interval}")
            return count
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return 0

    def fetch_all_historical(
        self, symbol: str, interval: str, start_time: int, end_time: int
    ) -> int:
        """批量加载历史K线数据到数据库
        
        :param symbol: 交易对符号
        :param interval: K线周期
        :param start_time: 起始时间（毫秒时间戳）
        :param end_time: 结束时间（毫秒时间戳）
        :return: 总存储数量
        """
        total_count = 0
        current_start = start_time
        
        while current_start < end_time:
            try:
                kline_json = self.binance_api.get_klines(
                    symbol, interval, 1000, current_start, end_time
                )
                if not kline_json or not isinstance(kline_json, list):
                    break
                
                klines = [KlineData.from_api_list(d, symbol, interval) for d in kline_json]
                count = self.kline_repo.save_batch(klines)
                total_count += count
                
                if count < 1000:
                    break
                
                last_open_time = klines[-1].open_time
                if last_open_time <= current_start:
                    break
                current_start = last_open_time + 1
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"批量加载失败: {e}")
                break
        
        print(f"历史K线加载完成: {symbol} {interval} 共 {total_count} 条")
        return total_count

    def get_from_db(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: int = None,
        end_time: int = None,
    ) -> List[KlineData]:
        """从数据库获取K线数据
        
        :param symbol: 交易对符号
        :param interval: K线周期
        :param limit: 限制数量
        :param start_time: 起始时间（毫秒时间戳）
        :param end_time: 结束时间（毫秒时间戳）
        :return: KlineData列表
        """
        return self.kline_repo.get_by_symbol_interval(
            symbol, interval, limit, start_time, end_time
        )

    def get_latest(self, symbol: str, interval: str) -> Optional[KlineData]:
        """获取最新一条K线
        
        :param symbol: 交易对符号
        :param interval: K线周期
        :return: KlineData或None
        """
        return self.kline_repo.get_latest(symbol, interval)

    def get_kline_dataframe(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: int = None,
        end_time: int = None,
    ):
        """从数据库获取K线并转换为DataFrame
        
        :param symbol: 交易对符号
        :param interval: K线周期
        :param limit: 限制数量
        :param start_time: 起始时间（毫秒时间戳）
        :param end_time: 结束时间（毫秒时间戳）
        :return: DataFrame格式的K线数据
        """
        klines = self.get_from_db(symbol, interval, limit, start_time, end_time)
        if not klines:
            return KlineData.to_dataframe([])
        return KlineData.to_dataframe(klines)

    def get_latest_kline_dataframe(self, symbol: str, interval: str):
        """获取最新一条K线并转换为DataFrame

        :param symbol: 交易对符号
        :param interval: K线周期
        :return: DataFrame格式的K线数据
        """
        kline = self.get_latest(symbol, interval)
        if not kline:
            return KlineData.to_dataframe([])
        return KlineData.to_dataframe([kline])

    def get_kline_dataframe_from_api(
        self,
        symbol: str,
        interval: str,
        limit: int = 1000,
    ):
        """从Binance获取K线保存到数据库后，从数据库中获取limit条数据转换为DataFrame

        :param symbol: 交易对符号
        :param interval: K线周期
        :param limit: 获取数量，默认1000
        :return: DataFrame格式的K线数据
        """
        k_last = self.get_latest(symbol, interval)
        if k_last:
            start_time = k_last.open_time
            end_time = int(round(time.time() * 1000))
            self.fetch_all_historical(symbol, interval, start_time, end_time)
        else:
            self.fetch_and_save(symbol, interval, limit)

        return self.get_kline_dataframe(symbol, interval, limit)


    def get_count(self, symbol: str = None, interval: str = None) -> int:
        """获取K线数量
        
        :param symbol: 交易对符号（可选）
        :param interval: K线周期（可选）
        :return: 数量
        """
        return self.kline_repo.count(symbol, interval)
