# K线服务层重构设计方案

## 1. 概述

本文档描述对K线数据处理流程的重构方案，新增K线服务层，封装从Binance API获取、转换、存储的完整流程。

## 2. 架构

```
app/
├── BinanceAPI.py           # Binance API封装（已存在）
├── OrderManager.py         # 订单管理器（改造：移除gain_kline）
└── services/
    ├── __init__.py
    └── kline_service.py    # K线服务层（新增）

db/
├── manager.py              # 数据库管理器（已存在）
├── kline_repo.py           # 数据访问层（改造）
└── kline_data.py           # K线数据模型（从kline_repo.py分离）
```

## 3. 核心类设计

| 类 | 路径 | 职责 |
|---|---|---|
| KlineData | db/kline_data.py | K线数据模型 |
| KlineRepo | db/kline_repo.py | 数据访问层 |
| KlineService | app/services/kline_service.py | K线业务服务层 |
| BinanceAPI | app/BinanceAPI.py | Binance API封装 |

## 4. KlineData 模型

```python
@dataclass
class KlineData:
    symbol: str
    interval: str
    open_time: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    close_time: int
    turnover: float
    trade_count: int
    buy_volume: float
    buy_turnover: float
    is_candle_closed: int
    
    @classmethod
    def from_api_list(cls, data: list, symbol: str, interval: str) -> KlineData
    @classmethod
    def from_row(cls, row: dict) -> KlineData
    def to_tuple() -> tuple
    def to_dataframe() -> pd.DataFrame
```

## 5. KlineService 核心方法

| 方法 | 说明 |
|---|---|
| fetch_and_save(symbol, interval, limit=1000) | 从Binance获取K线并存储到数据库 |
| fetch_all_historical(symbol, interval, start_time, end_time) | 批量加载历史K线数据 |
| get_from_db(symbol, interval, limit, start_time, end_time) | 从数据库获取K线数据列表 |
| get_kline_dataframe(symbol, interval, limit, start_time, end_time) | 获取K线并转换为DataFrame |

## 6. 数据流转

```
Binance API → KlineService.fetch_and_save() → KlineData列表 → KlineRepo.save_batch() → SQLite
                                              ↓
                                     KlineService.to_dataframe()
                                              ↓
                                        DataFrame → 策略
```

## 7. OrderManager 改造

- 移除 gain_kline() 方法
- 移除 _klines_to_dataframe() 方法
- 新增 KlineService 实例依赖注入
- 通过 kline_service.get_kline_dataframe() 获取数据

## 8. 启动自动加载

程序启动时自动从Binance拉取K线数据到数据库：
```python
kline_service.fetch_and_save(symbol, interval)
```

## 9. 手动脚本

```bash
python scripts/load_kline.py --symbol DOGEUSDT --interval 15m --limit 1000
```
