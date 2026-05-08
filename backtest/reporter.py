# -*- coding: utf-8 -*-
from typing import List, Dict, Optional
from datetime import datetime
import json

from backtest.models import BacktestOrder, BacktestTrade, BacktestStats, BacktestPosition, PositionRecord, OrderSide


class BacktestReporter:
    def __init__(self, stats: BacktestStats, orders: List[BacktestOrder], trades: List[BacktestTrade]):
        self.stats = stats
        self.orders = orders
        self.trades = trades

    def generate_text_report(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("回测报告")
        lines.append("=" * 60)
        lines.append("")

        lines.append("【账户信息】")
        lines.append(f"  初始资金: {self.stats.initial_capital:.2f} USDT")
        lines.append(f"  最终资金: {self.stats.final_capital:.2f} USDT")
        lines.append(f"  现金: {self.stats.cash:.2f} USDT")
        lines.append(f"  持仓市值: {self.stats.position_value:.2f} USDT")
        lines.append(f"  总收益: {self.stats.final_capital - self.stats.initial_capital:.2f} USDT")
        lines.append(f"  收益率: {(self.stats.final_capital / self.stats.initial_capital - 1) * 100:.2f}%")
        lines.append("")

        if self.stats.current_positions:
            lines.append("【当前持仓】")
            for symbol, pos in self.stats.current_positions.items():
                pnl_sign = "+" if pos.unrealized_pnl >= 0 else ""
                pnl_ratio_sign = "+" if pos.unrealized_pnl_ratio >= 0 else ""
                lines.append(
                    f"  {symbol} | {pos.side.value} | 数量: {pos.quantity:.4f} | "
                    f"成本: {pos.avg_entry_price:.4f} | 当前: {pos.current_price:.4f} | "
                    f"浮动盈亏: {pnl_sign}{pos.unrealized_pnl:.2f} ({pnl_ratio_sign}{pos.unrealized_pnl_ratio * 100:.2f}%)"
                )
            lines.append("")

        if self.stats.position_records:
            lines.append("【持仓记录】")
            for record in self.stats.position_records:
                pnl_sign = "+" if record.pnl >= 0 else ""
                pnl_ratio_sign = "+" if record.pnl_ratio >= 0 else ""
                hold_days = record.hold_seconds / 86400
                open_time_str = record.open_time.strftime('%Y-%m-%d') if isinstance(record.open_time, datetime) else str(record.open_time)
                close_time_str = record.close_time.strftime('%Y-%m-%d') if isinstance(record.close_time, datetime) else str(record.close_time)
                lines.append(
                    f"  {record.symbol} | 开仓: {record.entry_price:.4f} @ {open_time_str} | "
                    f"平仓: {record.exit_price:.4f} @ {close_time_str} | "
                    f"盈亏: {pnl_sign}{record.pnl:.2f} ({pnl_ratio_sign}{record.pnl_ratio * 100:.2f}%) | "
                    f"持仓: {hold_days:.1f}天"
                )
            lines.append("")

        lines.append("【交易统计】")
        lines.append(f"  总交易次数: {self.stats.total_trades}")
        lines.append(f"  盈利交易次数: {self.stats.winning_trades}")
        lines.append(f"  亏损交易次数: {self.stats.losing_trades}")
        lines.append(f"  胜率: {self.stats.win_rate * 100:.2f}%")
        lines.append("")

        lines.append("【收益统计】")
        lines.append(f"  总盈利: {self.stats.total_profit:.2f} USDT")
        lines.append(f"  总亏损: {self.stats.total_loss:.2f} USDT")
        lines.append(f"  盈利因子: {self.stats.profit_factor:.2f}")
        lines.append("")

        lines.append("【风险统计】")
        lines.append(f"  最大回撤: {self.stats.max_drawdown:.2f} USDT")
        lines.append(f"  最大回撤率: {self.stats.max_drawdown_ratio * 100:.2f}%")
        lines.append(f"  夏普比率: {self.stats.sharpe_ratio:.2f}")
        lines.append("")

        lines.append("【订单统计】")
        lines.append(f"  总订单数: {len(self.orders)}")
        filled_orders = [o for o in self.orders if o.is_filled]
        lines.append(f"  成交订单数: {len(filled_orders)}")
        lines.append("")

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        report = {
            "account": {
                "initial_capital": self.stats.initial_capital,
                "final_capital": self.stats.final_capital,
                "cash": self.stats.cash,
                "position_value": self.stats.position_value,
                "total_return": self.stats.final_capital - self.stats.initial_capital,
                "return_rate": (self.stats.final_capital / self.stats.initial_capital - 1),
            },
            "trade_stats": {
                "total_trades": self.stats.total_trades,
                "winning_trades": self.stats.winning_trades,
                "losing_trades": self.stats.losing_trades,
                "win_rate": self.stats.win_rate,
            },
            "profit_stats": {
                "total_profit": self.stats.total_profit,
                "total_loss": self.stats.total_loss,
                "profit_factor": self.stats.profit_factor,
            },
            "risk_stats": {
                "max_drawdown": self.stats.max_drawdown,
                "max_drawdown_ratio": self.stats.max_drawdown_ratio,
                "sharpe_ratio": self.stats.sharpe_ratio,
            },
            "current_positions": [
                {
                    "symbol": pos.symbol,
                    "side": pos.side.value,
                    "quantity": pos.quantity,
                    "avg_entry_price": pos.avg_entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_ratio": pos.unrealized_pnl_ratio,
                    "position_value": pos.position_value,
                }
                for pos in self.stats.current_positions.values()
            ],
            "position_records": [
                {
                    "symbol": r.symbol,
                    "side": r.side.value,
                    "quantity": r.quantity,
                    "entry_price": r.entry_price,
                    "exit_price": r.exit_price,
                    "pnl": r.pnl,
                    "pnl_ratio": r.pnl_ratio,
                    "commission": r.commission,
                    "open_time": r.open_time.isoformat() if isinstance(r.open_time, datetime) else str(r.open_time),
                    "close_time": r.close_time.isoformat() if isinstance(r.close_time, datetime) else str(r.close_time),
                    "hold_seconds": r.hold_seconds,
                }
                for r in self.stats.position_records
            ],
            "orders": {
                "total_orders": len(self.orders),
                "filled_orders": len([o for o in self.orders if o.is_filled]),
            },
            "trades": [
                {
                    "trade_id": t.trade_id,
                    "symbol": t.symbol,
                    "side": t.side.value,
                    "price": t.price,
                    "quantity": t.quantity,
                    "turnover": t.turnover,
                    "commission": t.commission,
                    "trade_time": t.trade_time.isoformat() if isinstance(t.trade_time, datetime) else str(t.trade_time),
                }
                for t in self.trades
            ],
            "generated_at": datetime.now().isoformat(),
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    def generate_dict_report(self) -> Dict:
        return {
            "account": {
                "initial_capital": self.stats.initial_capital,
                "final_capital": self.stats.final_capital,
                "cash": self.stats.cash,
                "position_value": self.stats.position_value,
                "total_return": self.stats.final_capital - self.stats.initial_capital,
                "return_rate": (self.stats.final_capital / self.stats.initial_capital - 1),
            },
            "trade_stats": {
                "total_trades": self.stats.total_trades,
                "winning_trades": self.stats.winning_trades,
                "losing_trades": self.stats.losing_trades,
                "win_rate": self.stats.win_rate,
            },
            "profit_stats": {
                "total_profit": self.stats.total_profit,
                "total_loss": self.stats.total_loss,
                "profit_factor": self.stats.profit_factor,
            },
            "risk_stats": {
                "max_drawdown": self.stats.max_drawdown,
                "max_drawdown_ratio": self.stats.max_drawdown_ratio,
                "sharpe_ratio": self.stats.sharpe_ratio,
            },
        }

    def print_report(self):
        print(self.generate_text_report())

    def save_report(self, filepath: str, format: str = "text"):
        if format == "json":
            content = self.generate_json_report()
        else:
            content = self.generate_text_report()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
