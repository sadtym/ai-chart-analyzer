# -*- coding: utf-8 -*-
"""
موتور Backtesting برای استراتژی‌های SMC
پشتیبانی از: Order Block Breakout, FVG Reversal, BOS, Liquidity Sweep
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class PositionType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class TradeStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    TP = "TAKE_PROFIT"
    SL = "STOP_LOSS"


@dataclass
class Trade:
    """ساختار یک معامله"""
    entry_time: datetime
    entry_price: float
    position_type: PositionType
    stop_loss: float
    take_profit: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.OPEN
    profit_percent: float = 0.0
    risk_reward: float = 0.0
    reason: str = ""


@dataclass
class BacktestResult:
    """نتیجه بک‌تست"""
    symbol: str
    strategy: str
    timeframe: str
    start_date: str
    end_date: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_percent: float
    max_drawdown: float
    avg_trade_duration: float
    best_trade: float
    worst_trade: float
    trades: List[Trade]


class SMCAnalyzer:
    """تحلیلگر SMC برای شناسایی الگوها"""
    
    @staticmethod
    def find_order_blocks(df: pd.DataFrame) -> List[Dict]:
        """
        شناسایی Order Block‌ها
        Order Block = آخرین کندل نزولی (برای صعود) یا صعودی (برای نزول)
        قبل از یک حرکت قوی در جهت مخالف
        """
        ob_list = []
        df = df.copy()
        df['is_bearish'] = df['close'] < df['open']
        df['is_bullish'] = df['close'] > df['open']
        
        # برای هر کندل، بررسی آیا Order Block است
        for i in range(5, len(df)):
            current = df.iloc[i]
            prev_candles = df.iloc[i-5:i]
            
            # بررسی OB صعودی (کندل نزولی قبل از صعود)
            if current['is_bearish']:
                # آیا بعد از این کندل، صعود قوی داشتیم؟
                future = df.iloc[i+1:i+5]
                if len(future) > 0:
                    price_change = (future['close'].iloc[-1] - current['close']) / current['close'] * 100
                    if price_change > 1.5:  # حداقل ۱.۵٪ صعود
                        ob_list.append({
                            'index': i,
                            'type': 'BULLISH_OB',
                            'high': current['high'],
                            'low': current['low'],
                            'close': current['close'],
                            'open': current['open'],
                            'timestamp': current['timestamp'],
                            'strength': min(price_change / 3, 3)  # قدرت OB
                        })
            
            # بررسی OB نزولی (کندل صعودی قبل از نزول)
            if current['is_bullish']:
                future = df.iloc[i+1:i+5]
                if len(future) > 0:
                    price_change = (future['close'].iloc[-1] - current['close']) / current['close'] * 100
                    if price_change < -1.5:  # حداقل ۱.۵٪ نزول
                        ob_list.append({
                            'index': i,
                            'type': 'BEARISH_OB',
                            'high': current['high'],
                            'low': current['low'],
                            'close': current['close'],
                            'open': current['open'],
                            'timestamp': current['timestamp'],
                            'strength': min(abs(price_change) / 3, 3)
                        })
        
        return ob_list
    
    @staticmethod
    def find_fvgs(df: pd.DataFrame) -> List[Dict]:
        """
        شناسایی Fair Value Gaps
        FVG = فاصله بین Low کندل i+2 و High کندل i
        """
        fvg_list = []
        df = df.copy()
        
        for i in range(1, len(df) - 1):
            prev_high = df.iloc[i-1]['high']
            curr_low = df.iloc[i]['low']
            curr_high = df.iloc[i]['high']
            next_low = df.iloc[i+1]['low']
            
            # FVG صعودی (گپ به سمت بالا)
            if next_low < prev_high:
                gap_size = ((prev_high - next_low) / prev_high) * 100
                if gap_size > 0.1:  # حداقل ۰.۱٪ گپ
                    fvg_list.append({
                        'index': i,
                        'type': 'BULLISH_FVG',
                        'top': prev_high,
                        'bottom': next_low,
                        'gap_size': gap_size,
                        'mid': (prev_high + next_low) / 2
                    })
            
            # FVG نزولی (گپ به سمت پایین)
            if next_low > prev_high:
                gap_size = ((next_low - prev_high) / prev_high) * 100
                if gap_size > 0.1:
                    fvg_list.append({
                        'index': i,
                        'type': 'BEARISH_FVG',
                        'top': next_low,
                        'bottom': prev_high,
                        'gap_size': gap_size,
                        'mid': (next_low + prev_high) / 2
                    })
        
        return fvg_list
    
    @staticmethod
    def check_bos(df: pd.DataFrame, index: int, direction: str = 'up') -> bool:
        """
        بررسی Break of Structure
        BOS = شکستن سقف/کف قبلی در جهت روند
        """
        if index < 5:
            return False
        
        current = df.iloc[index]
        
        if direction == 'up':
            # برای BOS صعودی، باید سقف کندل قبلی شکسته شود
            prev_swing_high = df.iloc[index-5:index]['high'].max()
            return current['high'] > prev_swing_high
        else:
            # برای BOS نزولی، باید کف کندل قبلی شکسته شود
            prev_swing_low = df.iloc[index-5:index]['low'].min()
            return current['low'] < prev_swing_low
    
    @staticmethod
    def find_liquidity_levels(df: pd.DataFrame) -> Dict:
        """
        شناسایی سطوح نقدینگی (سقف‌ها و کف‌های محلی)
        """
        df = df.copy()
        
        # یافتن سقف‌های محلی
        highs = []
        for i in range(2, len(df) - 2):
            if df.iloc[i]['high'] > df.iloc[i-1]['high'] and \
               df.iloc[i]['high'] > df.iloc[i-2]['high'] and \
               df.iloc[i]['high'] > df.iloc[i+1]['high'] and \
               df.iloc[i]['high'] > df.iloc[i+2]['high']:
                highs.append({
                    'index': i,
                    'price': df.iloc[i]['high'],
                    'timestamp': df.iloc[i]['timestamp']
                })
        
        # یافتن کف‌های محلی
        lows = []
        for i in range(2, len(df) - 2):
            if df.iloc[i]['low'] < df.iloc[i-1]['low'] and \
               df.iloc[i]['low'] < df.iloc[i-2]['low'] and \
               df.iloc[i]['low'] < df.iloc[i+1]['low'] and \
               df.iloc[i]['low'] < df.iloc[i+2]['low']:
                lows.append({
                    'index': i,
                    'price': df.iloc[i]['low'],
                    'timestamp': df.iloc[i]['timestamp']
                })
        
        return {
            'swing_highs': sorted(highs, key=lambda x: x['price'], reverse=True)[:10],
            'swing_lows': sorted(lows, key=lambda x: x['price'])[:10]
        }


class StrategyBase:
    """کلاس پایه برای استراتژی‌ها"""
    
    def __init__(self, name: str, risk_reward: float = 2.0):
        self.name = name
        self.risk_reward = risk_reward
        self.smc = SMCAnalyzer()
    
    def generate_signal(self, df: pd.DataFrame, index: int) -> Optional[Dict]:
        """تولید سیگنال - باید در کلاس‌های فرزند پیاده‌سازی شود"""
        raise NotImplementedError


class OBBreakoutStrategy(StrategyBase):
    """استراتژی شکست Order Block"""
    
    def __init__(self, risk_reward: float = 2.0):
        super().__init__("Order Block Breakout", risk_reward)
        self.order_blocks = []
    
    def generate_signal(self, df: pd.DataFrame, index: int) -> Optional[Dict]:
        """سیگنال خرید وقتی قیمت به Order Block برمی‌گردد"""
        if index < 10:
            return None
        
        current = df.iloc[index]
        current_price = current['close']
        
        # بررسی تمام OB‌های شناسایی‌شده
        for ob in self.order_blocks:
            if ob['index'] >= index - 5:  # OB اخیر
                continue
            
            if ob['type'] == 'BULLISH_OB':
                # بررسی بازگشت قیمت به OB
                if current_price >= ob['low'] and current_price <= ob['high']:
                    # بررسی تأیید SMC (FVG یا BOS)
                    fvgs = self.smc.find_fvgs(df.iloc[index-3:index+3])
                    has_bullish_fvg = any(f['type'] == 'BULLISH_FVG' for f in fvgs)
                    
                    if has_bullish_fvg:
                        # محاسبه SL و TP
                        sl = ob['low'] * 0.99  # ۱٪ زیر OB
                        tp = current_price + (current_price - sl) * self.risk_reward
                        
                        return {
                            'type': 'LONG',
                            'entry': current_price,
                            'stop_loss': sl,
                            'take_profit': tp,
                            'reason': f"Bullish OB Retest + FVG Confirmation",
                            'ob_index': ob['index']
                        }
        
        return None


class FVGReversalStrategy(StrategyBase):
    """استراتژی بازگشت از Fair Value Gap"""
    
    def __init__(self, risk_reward: float = 2.0):
        super().__init__("FVG Reversal", risk_reward)
        self.fvgs = []
    
    def generate_signal(self, df: pd.DataFrame, index: int) -> Optional[Dict]:
        """سیگنال بر اساس بازگشت از FVG"""
        if index < 5:
            return None
        
        current = df.iloc[index]
        current_price = current['close']
        
        # بررسی FVG‌های اخیر
        for fvg in self.fvgs:
            if fvg['index'] >= index - 3:
                continue
            
            if fvg['type'] == 'BULLISH_FVG':
                # قیمت به ناحیه FVG برگشته
                if current_price <= fvg['top'] and current_price >= fvg['bottom']:
                    sl = fvg['bottom'] * 0.99
                    tp = fvg['top'] + (fvg['top'] - fvg['bottom']) * self.risk_reward * 2
                    
                    return {
                        'type': 'LONG',
                        'entry': current_price,
                        'stop_loss': sl,
                        'take_profit': tp,
                        'reason': f"FVG Retest - Gap: {fvg['gap_size']:.2f}%"
                    }
            
            elif fvg['type'] == 'BEARISH_FVG':
                if current_price >= fvg['bottom'] and current_price <= fvg['top']:
                    sl = fvg['top'] * 1.01
                    tp = fvg['bottom'] - (fvg['top'] - fvg['bottom']) * self.risk_reward * 2
                    
                    return {
                        'type': 'SHORT',
                        'entry': current_price,
                        'stop_loss': sl,
                        'take_profit': tp,
                        'reason': f"FVG Retest - Gap: {fvg['gap_size']:.2f}%"
                    }
        
        return None


class BOSContinuationStrategy(StrategyBase):
    """استراتژی ادامه روند پس از BOS"""
    
    def __init__(self, risk_reward: float = 2.0):
        super().__init__("BOS Continuation", risk_reward)
    
    def generate_signal(self, df: pd.DataFrame, index: int) -> Optional[Dict]:
        """سیگنال بر اساس ادامه روند پس از BOS"""
        if index < 10:
            return None
        
        current = df.iloc[index]
        current_price = current['close']
        
        # بررسی BOS صعودی
        if self.smc.check_bos(df, index, 'up'):
            # تأیید با FVG
            recent_fvgs = self.smc.find_fvgs(df.iloc[index-3:index+1])
            if any(f['type'] == 'BULLISH_FVG' for f in recent_fvgs):
                sl = df.iloc[index-5:index]['low'].min() * 0.995
                tp = current_price + (current_price - sl) * self.risk_reward
                
                return {
                    'type': 'LONG',
                    'entry': current_price,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'reason': "BOS + FVG Continuation"
                }
        
        # بررسی BOS نزولی
        if self.smc.check_bos(df, index, 'down'):
            recent_fvgs = self.smc.find_fvgs(df.iloc[index-3:index+1])
            if any(f['type'] == 'BEARISH_FVG' for f in recent_fvgs):
                sl = df.iloc[index-5:index]['high'].max() * 1.005
                tp = current_price - (sl - current_price) * self.risk_reward
                
                return {
                    'type': 'SHORT',
                    'entry': current_price,
                    'stop_loss': sl,
                    'take_profit': tp,
                    'reason': "BOS + FVG Continuation"
                }
        
        return None


class BacktestEngine:
    """موتور اصلی بک‌تست"""
    
    STRATEGIES = {
        'ob_breakout': OBBreakoutStrategy,
        'fvg_reversal': FVGReversalStrategy,
        'bos_continuation': BOSContinuationStrategy,
        'smc_combo': lambda rr: FVGReversalStrategy(rr)  # ترکیبی
    }
    
    def __init__(self, exchange_id: str = 'binance'):
        self.exchange_id = exchange_id
        self.exchange = None
    
    def connect(self):
        """اتصال به صرافی"""
        try:
            self.exchange = getattr(ccxt, self.exchange_id)({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
        except AttributeError:
            # اگر صرافی پشتیبانی نمی‌شود، از بایننس اسپات استفاده کن
            self.exchange = ccxt.binance({
                'enableRateLimit': True
            })
    
    def fetch_data(self, symbol: str, timeframe: str, limit: int = 1000) -> pd.DataFrame:
        """دریافت داده‌های کندل"""
        if not self.exchange:
            self.connect()
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return self._generate_sample_data(limit)
    
    def _generate_sample_data(self, limit: int) -> pd.DataFrame:
        """تولید داده نمونه"""
        import random
        base_price = 50000
        data = []
        
        for i in range(limit):
            timestamp = datetime.now() - timedelta(hours=limit-i)
            volatility = random.uniform(0.005, 0.02)
            change = random.gauss(0, volatility)
            
            open_price = base_price * (1 + change)
            close_price = base_price * (1 + change + random.gauss(0, volatility))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            
            data.append([timestamp, open_price, high_price, low_price, close_price, random.uniform(100, 1000)])
            base_price = close_price
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def run_backtest(self, symbol: str, strategy_name: str, 
                     timeframe: str = '1h', days: int = 365,
                     risk_reward: float = 2.0,
                     sl_percent: float = 2.0,
                     tp_percent: float = 4.0) -> BacktestResult:
        """اجرای بک‌تست"""
        
        # دریافت داده‌ها
        df = self.fetch_data(symbol, timeframe, limit=min(days * 24, 2000))
        
        if df.empty or len(df) < 100:
            return self._empty_result(symbol, strategy_name, timeframe)
        
        # انتخاب استراتژی
        strategy_class = self.STRATEGIES.get(strategy_name, FVGReversalStrategy)
        strategy = strategy_class(risk_reward)
        
        # اگر استراتژی نیاز به آماده‌سازی دارد
        if hasattr(strategy, 'fvgs'):
            strategy.fvgs = SMCAnalyzer.find_fvgs(df)
        if hasattr(strategy, 'order_blocks'):
            strategy.order_blocks = SMCAnalyzer.find_order_blocks(df)
        
        # شبیه‌سازی معاملات
        trades = []
        current_position = None
        entry_price = 0
        
        for i in range(20, len(df)):
            current = df.iloc[i]
            current_price = current['close']
            current_time = current['timestamp']
            
            # بررسی معامله باز
            if current_position:
                if current_position == 'LONG':
                    # بررسی حد ضرر
                    if current_price <= entry_price * (1 - sl_percent/100):
                        profit = -sl_percent
                        trades.append(self._close_trade(current_time, current_price, profit, 'SL'))
                        current_position = None
                    # بررسی حد سود
                    elif current_price >= entry_price * (1 + tp_percent/100):
                        profit = tp_percent
                        trades.append(self._close_trade(current_time, current_price, profit, 'TP'))
                        current_position = None
                
                elif current_position == 'SHORT':
                    if current_price >= entry_price * (1 + sl_percent/100):
                        profit = -sl_percent
                        trades.append(self._close_trade(current_time, current_price, profit, 'SL'))
                        current_position = None
                    elif current_price <= entry_price * (1 - tp_percent/100):
                        profit = tp_percent
                        trades.append(self._close_trade(current_time, current_price, profit, 'TP'))
                        current_position = None
            
            # اگر معامله باز نیست، بررسی سیگنال جدید
            if not current_position:
                signal = strategy.generate_signal(df, i)
                
                if signal and signal['type'] == 'LONG' and current_position != 'LONG':
                    current_position = 'LONG'
                    entry_price = current_price
                elif signal and signal['type'] == 'SHORT' and current_position != 'SHORT':
                    current_position = 'SHORT'
                    entry_price = current_price
        
        # محاسبه نتایج
        return self._calculate_results(trades, symbol, strategy_name, timeframe, df)
    
    def _close_trade(self, exit_time, exit_price, profit, reason):
        """ایجاد معامله بسته‌شده"""
        return {
            'exit_time': exit_time,
            'exit_price': exit_price,
            'profit_percent': profit,
            'reason': reason
        }
    
    def _calculate_results(self, trades: List, symbol: str, strategy: str, 
                           timeframe: str, df: pd.DataFrame) -> BacktestResult:
        """محاسبه نتایج نهایی"""
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['profit_percent'] > 0)
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_profit = sum(t['profit_percent'] for t in trades)
        
        # محاسبه Max Drawdown
        equity_curve = [100]
        for trade in trades:
            equity_curve.append(equity_curve[-1] * (1 + trade['profit_percent']/100))
        
        peak = equity_curve[0]
        max_drawdown = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        best_trade = max(t['profit_percent'] for t in trades) if trades else 0
        worst_trade = min(t['profit_percent'] for t in trades) if trades else 0
        
        return BacktestResult(
            symbol=symbol,
            strategy=strategy,
            timeframe=timeframe,
            start_date=str(df['timestamp'].iloc[0])[:10],
            end_date=str(df['timestamp'].iloc[-1])[:10],
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_percent=total_profit,
            max_drawdown=max_drawdown,
            avg_trade_duration=0,
            best_trade=best_trade,
            worst_trade=worst_trade,
            trades=trades
        )
    
    def _empty_result(self, symbol: str, strategy: str, timeframe: str) -> BacktestResult:
        """نتیجه خالی برای زمان خطا"""
        return BacktestResult(
            symbol=symbol,
            strategy=strategy,
            timeframe=timeframe,
            start_date="",
            end_date="",
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            profit_percent=0,
            max_drawdown=0,
            avg_trade_duration=0,
            best_trade=0,
            worst_trade=0,
            trades=[]
        )
    
    def format_result_message(self, result: BacktestResult) -> str:
        """فرمت‌بندی پیام نتیجه"""
        if result.total_trades == 0:
            return "[!] داده کافی برای بک‌تست یافت نشد."
        
        # انتخاب ایموجی بر اساس سوددهی
        if result.profit_percent > 50:
            emoji = "[+]"
        elif result.profit_percent > 0:
            emoji = "[~]"
        else:
            emoji = "[-]"
        
        result_text = "سودده" if result.profit_percent > 0 else "ضررده"
        result_icon = "[OK]" if result.profit_percent > 0 else "[X]"
        
        win_rate_str = f"{result.win_rate:.1f}%"
        lose_rate_str = f"{100-result.win_rate:.1f}%"
        profit_str = f"{result.profit_percent:.2f}%"
        drawdown_str = f"{result.max_drawdown:.2f}%"
        best_str = f"+{result.best_trade:.2f}%"
        worst_str = f"{result.worst_trade:.2f}%"
        
        msg = f"""{emoji} گزارش Backtesting

================================
> مشخصات تست:
   نماد: {result.symbol}
   استراتژی: {result.strategy}
   تایم فریم: {result.timeframe}
   بازه: {result.start_date} تا {result.end_date}

> عملکرد کلی:
   تعداد معاملات: {result.total_trades}
   معاملات سودده: {result.winning_trades} ({win_rate_str})
   معاملات ضررده: {result.losing_trades} ({lose_rate_str})

> سود و ضرر:
   کل سود و ضرر: {profit_str}
   حداکثر افت سرمایه: {drawdown_str}
   بهترین معامله: {best_str}
   بدترین معامله: {worst_str}

> نسبت ریسک به ریوارد:
   میانگین R:R: 1:{result.profit_percent/result.max_drawdown:.2f} (تخمینی)

================================
> نتیجه: {result_text} {result_icon}
"""
        return msg


def get_backtest_engine(exchange_id: str = 'binance') -> BacktestEngine:
    """دریافت موتور بک‌تست"""
    return BacktestEngine(exchange_id)


# تست ماژول
if __name__ == "__main__":
    engine = BacktestEngine()
    result = engine.run_backtest('BTC/USDT', 'fvg_reversal', '1h', 30)
    print(engine.format_result_message(result))
