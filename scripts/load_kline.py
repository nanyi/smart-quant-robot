# -*- coding: utf-8 -*-
"""
K线数据批量加载脚本

用于从Binance API获取历史K线数据并存储到数据库。
支持指定交易对、K线周期和时间范围。

用法：
    python scripts/load_kline.py --symbol DOGEUSDT --interval 15m --limit 1000
    python scripts/load_kline.py --symbol BTCUSDT --interval 1h --days 30
    python scripts/load_kline.py --symbol ETHUSDT --interval 1d --start 1767196800000 --end 1777564800000
"""
import argparse
import time
from datetime import datetime, timedelta

from app.services import KlineService
from db.manager import DBManager


def parse_args():
    parser = argparse.ArgumentParser(description='K线数据批量加载工具')
    parser.add_argument('--symbol', type=str, default='DOGEUSDT', help='交易对符号')
    parser.add_argument('--interval', type=str, default='15m', help='K线周期')
    parser.add_argument('--limit', type=int, default=1000, help='获取数量')
    parser.add_argument('--days', type=int, default=None, help='加载最近N天的数据')
    parser.add_argument('--start', type=int, default=None, help='起始时间戳（毫秒）')
    parser.add_argument('--end', type=int, default=None, help='结束时间戳（毫秒）')
    return parser.parse_args()


def main():
    args = parse_args()
    
    print(f"=" * 50)
    print(f"K线数据加载工具")
    print(f"=" * 50)
    print(f"交易对: {args.symbol}")
    print(f"周期: {args.interval}")
    
    DBManager.get_instance().init_kline_table()
    kline_service = KlineService()
    
    if args.days is not None:
        end_time = int(round(time.time() * 1000))
        start_time = int((datetime.now() - timedelta(days=args.days)).timestamp() * 1000)
        print(f"时间范围: {datetime.fromtimestamp(start_time / 1000)} ~ {datetime.fromtimestamp(end_time / 1000)}")
        print(f"加载最近 {args.days} 天的数据...")
        count = kline_service.fetch_all_historical(args.symbol, args.interval, start_time, end_time)
    elif args.start is not None and args.end is not None:
        print(f"时间范围: {datetime.fromtimestamp(args.start / 1000)} ~ {datetime.fromtimestamp(args.end / 1000)}")
        count = kline_service.fetch_all_historical(args.symbol, args.interval, args.start, args.end)
    else:
        print(f"加载最新 {args.limit} 条数据...")
        count = kline_service.fetch_and_save(args.symbol, args.interval, args.limit)
    
    print(f"=" * 50)
    print(f"加载完成，共存储 {count} 条K线数据")
    print(f"=" * 50)


if __name__ == '__main__':
    main()
