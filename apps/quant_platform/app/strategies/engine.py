import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from loguru import logger


@dataclass
class Trade:
    date: str
    action: str
    price: float
    shares: int
    commission: float
    amount: float


@dataclass
class Position:
    shares: int = 0
    avg_cost: float = 0.0

    @property
    def is_empty(self):
        return self.shares == 0


@dataclass
class BacktestConfig:
    initial_capital: float = 1_000_000
    commission_rate: float = 0.0003
    stamp_tax: float = 0.001
    slippage: float = 0.002
    min_commission: float = 5.0


@dataclass
class BacktestResult:
    strategy_name: str
    ts_code: str
    start_date: str
    end_date: str
    config: BacktestConfig

    initial_capital: float = 0
    final_capital: float = 0
    total_return: float = 0
    annual_return: float = 0
    sharpe_ratio: float = 0
    max_drawdown: float = 0
    max_drawdown_duration: int = 0
    win_rate: float = 0
    profit_loss_ratio: float = 0
    trade_count: int = 0

    trades: List[dict] = field(default_factory=list)
    equity_curve: List[dict] = field(default_factory=list)

    def to_dict(self):
        return {
            "strategy_name": self.strategy_name,
            "ts_code": self.ts_code,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "final_capital": round(self.final_capital, 2),
            "total_return": round(self.total_return * 100, 2),
            "annual_return": round(self.annual_return * 100, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "max_drawdown": round(self.max_drawdown * 100, 2),
            "max_drawdown_duration": self.max_drawdown_duration,
            "win_rate": round(self.win_rate * 100, 2),
            "profit_loss_ratio": round(self.profit_loss_ratio, 4),
            "trade_count": self.trade_count,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
        }


class BacktestEngine:
    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def run(self, data: List[dict], strategy_func: Callable, params: dict = None) -> BacktestResult:
        df = pd.DataFrame(data)
        if df.empty or len(df) < 30:
            raise ValueError("Insufficient data, need at least 30 trading days")

        params = params or {}
        df = strategy_func(df.copy(), params)

        if 'signal' not in df.columns:
            raise ValueError("Strategy function must generate a 'signal' column")

        capital = self.config.initial_capital
        position = Position()
        trades: List[Trade] = []
        equity_curve = []

        for i, row in df.iterrows():
            current_price = row['close']
            signal = row['signal']

            if signal == 1 and position.is_empty:
                buy_price = current_price * (1 + self.config.slippage)
                max_shares = int(capital * 0.95 / (buy_price * 100)) * 100
                if max_shares >= 100:
                    amount = max_shares * buy_price
                    commission = max(amount * self.config.commission_rate, self.config.min_commission)
                    capital -= (amount + commission)
                    position.shares = max_shares
                    position.avg_cost = buy_price
                    trades.append(Trade(
                        date=row['date'], action="BUY", price=buy_price,
                        shares=max_shares, commission=commission, amount=amount,
                    ))

            elif signal == -1 and not position.is_empty:
                sell_price = current_price * (1 - self.config.slippage)
                amount = position.shares * sell_price
                commission = max(amount * self.config.commission_rate, self.config.min_commission)
                stamp_tax = amount * self.config.stamp_tax
                capital += (amount - commission - stamp_tax)
                trades.append(Trade(
                    date=row['date'], action="SELL", price=sell_price,
                    shares=position.shares, commission=commission + stamp_tax,
                    amount=amount,
                ))
                position = Position()

            market_value = position.shares * current_price if not position.is_empty else 0
            total_equity = capital + market_value
            equity_curve.append({
                "date": row['date'],
                "equity": round(total_equity, 2),
                "cash": round(capital, 2),
                "position_value": round(market_value, 2),
                "benchmark_close": current_price,
            })

        result = self._compute_stats(
            equity_curve, trades, df,
            strategy_name=params.get('strategy_name', 'Custom'),
            ts_code=params.get('ts_code', ''),
        )
        return result

    def _compute_stats(self, equity_curve, trades, df, strategy_name, ts_code) -> BacktestResult:
        equities = [e['equity'] for e in equity_curve]
        dates = [e['date'] for e in equity_curve]

        initial = self.config.initial_capital
        final = equities[-1] if equities else initial

        total_return = (final - initial) / initial

        n_days = len(equities)
        annual_return = (1 + total_return) ** (252 / max(n_days, 1)) - 1

        daily_returns = pd.Series(equities).pct_change().dropna()
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            sharpe = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252))
        else:
            sharpe = 0

        peak = pd.Series(equities).cummax()
        drawdown = (pd.Series(equities) - peak) / peak
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0

        dd_duration = 0
        max_dd_duration = 0
        for i in range(len(equities)):
            if equities[i] < peak.iloc[i]:
                dd_duration += 1
                max_dd_duration = max(max_dd_duration, dd_duration)
            else:
                dd_duration = 0

        profits = []
        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                buy = trades[i]
                sell = trades[i + 1]
                pnl = (sell.price - buy.price) * buy.shares - buy.commission - sell.commission
                profits.append(pnl)

        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p <= 0]
        win_rate = len(wins) / len(profits) if profits else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 1
        pl_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        result = BacktestResult(
            strategy_name=strategy_name,
            ts_code=ts_code,
            start_date=dates[0] if dates else "",
            end_date=dates[-1] if dates else "",
            config=self.config,
            initial_capital=initial,
            final_capital=final,
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            win_rate=win_rate,
            profit_loss_ratio=pl_ratio,
            trade_count=len(trades),
            trades=[{
                "date": t.date, "action": t.action, "price": round(t.price, 2),
                "shares": t.shares, "commission": round(t.commission, 2),
                "amount": round(t.amount, 2),
            } for t in trades],
            equity_curve=equity_curve,
        )
        return result


# ===== Built-in Strategies =====

def strategy_dual_ma(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    short = params.get('short_period', 5)
    long = params.get('long_period', 20)
    df['ma_short'] = df['close'].rolling(short).mean()
    df['ma_long'] = df['close'].rolling(long).mean()
    df['signal'] = 0
    df.loc[(df['ma_short'] > df['ma_long']) & (df['ma_short'].shift(1) <= df['ma_long'].shift(1)), 'signal'] = 1
    df.loc[(df['ma_short'] < df['ma_long']) & (df['ma_short'].shift(1) >= df['ma_long'].shift(1)), 'signal'] = -1
    return df


def strategy_macd(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    fast = params.get('fast_period', 12)
    slow = params.get('slow_period', 26)
    signal_period = params.get('signal_period', 9)
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal_period).mean()
    df['signal'] = 0
    df.loc[(dif > dea) & (dif.shift(1) <= dea.shift(1)), 'signal'] = 1
    df.loc[(dif < dea) & (dif.shift(1) >= dea.shift(1)), 'signal'] = -1
    return df


def strategy_bollinger(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get('period', 20)
    std_dev = params.get('std_dev', 2)
    ma = df['close'].rolling(period).mean()
    std = df['close'].rolling(period).std()
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    df['signal'] = 0
    df.loc[(df['close'] < lower) & (df['close'].shift(1) >= lower.shift(1)), 'signal'] = 1
    df.loc[(df['close'] > upper) & (df['close'].shift(1) <= upper.shift(1)), 'signal'] = -1
    return df


def strategy_turtle(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    entry_period = params.get('entry_period', 20)
    exit_period = params.get('exit_period', 10)
    df['high_n'] = df['high'].rolling(entry_period).max()
    df['low_n'] = df['low'].rolling(exit_period).min()
    df['signal'] = 0
    df.loc[df['close'] > df['high_n'].shift(1), 'signal'] = 1
    df.loc[df['close'] < df['low_n'].shift(1), 'signal'] = -1
    return df


def strategy_rsi(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    period = params.get('period', 14)
    overbought = params.get('overbought', 70)
    oversold = params.get('oversold', 30)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    df['signal'] = 0
    df.loc[(rsi < oversold) & (rsi.shift(1) >= oversold), 'signal'] = 1
    df.loc[(rsi > overbought) & (rsi.shift(1) <= overbought), 'signal'] = -1
    return df


BUILTIN_STRATEGIES = {
    "dual_ma": {
        "name": "Dual MA",
        "func": strategy_dual_ma,
        "description": "Buy on golden cross, sell on death cross",
        "params": {
            "short_period": {"label": "Short MA", "default": 5, "min": 2, "max": 60},
            "long_period": {"label": "Long MA", "default": 20, "min": 5, "max": 250},
        },
    },
    "macd": {
        "name": "MACD",
        "func": strategy_macd,
        "description": "Buy on MACD golden cross, sell on death cross",
        "params": {
            "fast_period": {"label": "Fast Period", "default": 12, "min": 5, "max": 30},
            "slow_period": {"label": "Slow Period", "default": 26, "min": 10, "max": 60},
            "signal_period": {"label": "Signal Period", "default": 9, "min": 5, "max": 20},
        },
    },
    "bollinger": {
        "name": "Bollinger Bands",
        "func": strategy_bollinger,
        "description": "Buy at lower band, sell at upper band",
        "params": {
            "period": {"label": "Period", "default": 20, "min": 10, "max": 60},
            "std_dev": {"label": "Std Dev", "default": 2, "min": 1, "max": 3},
        },
    },
    "turtle": {
        "name": "Turtle Trading",
        "func": strategy_turtle,
        "description": "Buy on N-day high breakout, sell on M-day low breakdown",
        "params": {
            "entry_period": {"label": "Entry Period", "default": 20, "min": 10, "max": 60},
            "exit_period": {"label": "Exit Period", "default": 10, "min": 5, "max": 30},
        },
    },
    "rsi": {
        "name": "RSI",
        "func": strategy_rsi,
        "description": "Buy on oversold, sell on overbought",
        "params": {
            "period": {"label": "RSI Period", "default": 14, "min": 5, "max": 30},
            "overbought": {"label": "Overbought", "default": 70, "min": 60, "max": 90},
            "oversold": {"label": "Oversold", "default": 30, "min": 10, "max": 40},
        },
    },
}
