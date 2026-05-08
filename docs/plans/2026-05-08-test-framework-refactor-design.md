# 测试框架重构设计方案

## 1. 概述

重构测试框架，将 `tests/` 下的测试类抽象一个基类，统一管理测试数据生成和回测报告保存功能。

## 2. 当前问题

- `generate_test_data()` 在每个测试文件中重复定义
- `save_backtest_data()` 和 `generate_unique_filename()` 只在 `test_ma.py` 中
- 测试类之间没有统一的基类，不利于扩展和维护

## 3. 重构方案

### 3.1 文件结构

```
tests/
├── __init__.py           # 新增：测试基类 BaseStrategyTestCase
├── test_ma.py            # 继承基类
├── test_lifemore.py      # 继承基类
└── test_turtle.py        # 继承基类

backtest/
└── reporter.py           # 新增 save_backtest_report 静态方法
```

### 3.2 BaseStrategyTestCase 基类

```python
class BaseStrategyTestCase(unittest.TestCase):
    """策略测试基类，提供通用测试方法"""
    
    @staticmethod
    def generate_test_data(days=365, start_price=100) -> pd.DataFrame:
        """生成模拟K线数据
        
        :param days: 数据天数
        :param start_price: 起始价格
        :return: DataFrame格式的K线数据
        """
    
    def save_backtest_report(self, df, strategy, engine, stats):
        """保存回测报告到文件
        
        :param df: K线数据DataFrame
        :param strategy: 策略实例
        :param engine: 回测引擎
        :param stats: 回测统计
        """
```

### 3.3 BacktestReporter 新增方法

```python
class BacktestReporter:
    @staticmethod
    def save_backtest_report(df, strategy, engine, stats, output_dir="./backtest/report"):
        """保存回测数据到文件
        
        保存内容：
        - 回测报告 (txt)
        - K线数据 (xlsx)
        - 订单数据 (xlsx)
        - 交易数据 (xlsx)
        - 持仓数据 (xlsx)
        """
```

## 4. 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `tests/__init__.py` | 新增 `BaseStrategyTestCase` 基类，包含 `generate_test_data()` 和 `save_backtest_report()` |
| `tests/test_ma.py` | 继承基类，移除重复的 `generate_test_data()` 和 `save_backtest_data()` |
| `tests/test_lifemore.py` | 继承基类，移除重复的 `generate_test_data()` |
| `tests/test_turtle.py` | 继承基类，移除重复的 `generate_test_data()` |
| `backtest/reporter.py` | 新增 `save_backtest_report()` 静态方法 |

## 5. 测试类继承关系

```
unittest.TestCase
    └── BaseStrategyTestCase (新增)
            ├── test_ma.py::TestMAStrategy(BaseStrategyTestCase)
            ├── test_lifemore.py::TestLivermoreStrategy(BaseStrategyTestCase)
            └── test_turtle.py::TestTurtleStrategy(BaseStrategyTestCase)
```

## 6. 实现检查点

1. `BaseStrategyTestCase` 正确继承 `unittest.TestCase`
2. `generate_test_data()` 生成的DataFrame包含正确的列
3. `save_backtest_report()` 保存所有必要的文件
4. 各测试类正确调用父类方法