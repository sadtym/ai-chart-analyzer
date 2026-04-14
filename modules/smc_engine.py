"""
ماژول موتور تحلیل SMC (Smart Money Concepts)
شناسایی الگوهای معاملاتی институциональی و ساختار بازار

شامل:
- BOS (Break of Structure)
- CHoCH (Change of Character)
- Order Blocks
- Fair Value Gaps (FVG)
- Liquidity Pools
- Market Structure Analysis
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal, Tuple
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """جهت روند بازار"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class StructureType(Enum):
    """نوع رویداد ساختاری"""
    BOS = "BOS"  # Break of Structure - ادامه روند
    CHoCH = "CHoCH"  # Change of Character - تغییر روند


class ZoneType(Enum):
    """نوع ناحیه"""
    ORDER_BLOCK = "OB"
    FAIR_VALUE_GAP = "FVG"
    LIQUIDITY = "LIQUIDITY"


class ZoneStrength(Enum):
    """قدرت ناحیه"""
    WEAK = "Weak"
    MEDIUM = "Medium"
    STRONG = "Strong"
    VERY_STRONG = "Very Strong"


@dataclass
class SwingPoint:
    """نقطه سوئینگ (فراکتال)"""
    index: int
    timestamp: pd.Timestamp
    price: float
    type: Literal['HH', 'HL', 'LH', 'LL']  # Higher High, Higher Low, etc.
    is_confirmed: bool = False


@dataclass
class StructureEvent:
    """رویداد شکست ساختار"""
    index: int
    timestamp: pd.Timestamp
    structure_type: StructureType
    direction: TrendDirection
    price_level: float
    reference_level: float  # سطح مرجع که شکسته شده
    strength: ZoneStrength = ZoneStrength.MEDIUM
    description: str = ""


@dataclass
class OrderBlock:
    """ناحیه سفارش (Order Block)"""
    index_start: int
    timestamp_start: pd.Timestamp
    direction: TrendDirection
    top: float
    bottom: float
    body_top: float
    body_bottom: float
    strength: ZoneStrength
    mitigated: bool = False
    mitigated_at: Optional[float] = None
    volume_profile: float = 0.0  # حجم معاملات در این ناحیه


@dataclass
class FairValueGap:
    """شکاف ارزش منصفانه (FVG)"""
    index_start: int
    timestamp: pd.Timestamp
    direction: TrendDirection
    top: float
    bottom: float
    size: float
    mitigated: bool = False
    strength: ZoneStrength = ZoneStrength.MEDIUM


@dataclass
class LiquidityPool:
    """ناحیه نقدینگی"""
    type: Literal['EQH', 'EQL', 'HPS', 'LPS']  # Equal High/Low, High Probability Sweep, etc.
    price: float
    strength: ZoneStrength
    swept: bool = False
    swept_at: Optional[int] = None
    count: int = 1  # تعداد نقاط هم‌قیمت


@dataclass
class MarketCondition:
    """شرایط کلی بازار"""
    trend: TrendDirection
    trend_strength: float  # 0-1
    current_price: float
    volatility: float  # انحراف معیار
    volume_status: Literal['HIGH', 'NORMAL', 'LOW']
    last_updated: pd.Timestamp


class SMCEngine:
    """
    موتور تحلیل Smart Money Concepts
    
    این موتور داده‌های OHLCV را تحلیل کرده و موارد زیر را شناسایی می‌کند:
    - ساختار بازار و روند
    - نقاط سوئینگ و شکست ساختار
    - نواحی سفارش (Order Blocks)
    - شکاف‌های ارزش منصفانه (FVG)
    - نواحی نقدینگی
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        swing_length: int = 5,
        fvg_threshold: float = 0.0005,
        liquidity_threshold: float = 0.0002,
        ob_lookback: int = 10
    ):
        """
        مقداردهی اولیه موتور SMC
        
        Args:
            df: دیتافریم با ستون‌های [timestamp, open, high, low, close, volume]
            swing_length: طول پنجره برای شناسایی سوئینگ‌ها
            fvg_threshold: حداقل نسبت اندازه FVG به میانگین قیمت
            liquidity_threshold: حداقل نسبت برای تشخیص هم‌قیمت‌ها
            ob_lookback: تعداد کندل‌های قبل از شکست برای جستجوی OB
        """
        # اعتبارسنجی داده‌های ورودی
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")
        
        self.df = df.copy()
        self.swing_length = swing_length
        self.fvg_threshold = fvg_threshold
        self.liquidity_threshold = liquidity_threshold
        self.ob_lookback = ob_lookback
        
        # اطمینان از وجود timestamp
        if 'timestamp' not in df.columns:
            self.df['timestamp'] = pd.date_range(start='2024-01-01', periods=len(df), freq='1h')
        
        # نتایج تحلیل (باید اول تعریف شوند)
        self.swing_points: List[SwingPoint] = []
        self.structures: List[StructureEvent] = []
        self.order_blocks: List[OrderBlock] = []
        self.fvgs: List[FairValueGap] = []
        self.liquidity_pools: List[LiquidityPool] = []
        self.market_condition: Optional[MarketCondition] = None
        
        # آخرین قیمت و میانگین
        self.current_price = self.df['close'].iloc[-1]
        self.average_price = self.df['close'].mean()
        
        # محاسبات اولیه
        self._calculate_body_and_wicks()
        self._calculate_volatility()
    
    def _calculate_body_and_wicks(self):
        """محاسبه بدنه و فتیله کندل‌ها"""
        self.df['body'] = self.df['close'] - self.df['open']
        self.df['body_top'] = self.df[['open', 'close']].max(axis=1)
        self.df['body_bottom'] = self.df[['open', 'close']].min(axis=1)
        self.df['upper_wick'] = self.df['high'] - self.df['body_top']
        self.df['lower_wick'] = self.df['body_bottom'] - self.df['low']
        self.df['is_bullish'] = self.df['body'] > 0
        self.df['is_bearish'] = self.df['body'] < 0
    
    def _calculate_volatility(self):
        """محاسبه نوسانات"""
        returns = self.df['close'].pct_change()
        self.df['volatility'] = returns.rolling(window=20).std()
        self.current_volatility = self.df['volatility'].iloc[-1] if 'volatility' in self.df else 0
        self.avg_volatility = self.df['close'].std() / self.average_price
    
    def _identify_swing_points(self) -> List[SwingPoint]:
        """
        شناسایی نقاط سوئینگ (فراکتال‌های های/لو)
        
        نقاط سوئینگ نقاطی هستند که قیمت در آن‌ها نسبت به N کندل
        قبل و بعد خود، بالاترین یا پایین‌ترین مقدار را دارد.
        """
        swings = []
        
        for i in range(self.swing_length, len(self.df) - self.swing_length):
            # بررسی سوئینگ های
            window_highs = self.df['high'].iloc[i - self.swing_length:i + self.swing_length + 1]
            if self.df['high'].iloc[i] == window_highs.max():
                # تعیین نوع سوئینگ
                swing_type = self._classify_swing(i)
                swings.append(SwingPoint(
                    index=i,
                    timestamp=self.df['timestamp'].iloc[i],
                    price=self.df['high'].iloc[i],
                    type=swing_type,
                    is_confirmed=True
                ))
            
            # بررسی سوئینگ لو
            window_lows = self.df['low'].iloc[i - self.swing_length:i + self.swing_length + 1]
            if self.df['low'].iloc[i] == window_lows.min():
                swing_type = self._classify_swing(i, is_low=True)
                swings.append(SwingPoint(
                    index=i,
                    timestamp=self.df['timestamp'].iloc[i],
                    price=self.df['low'].iloc[i],
                    type=swing_type,
                    is_confirmed=True
                ))
        
        self.swing_points = swings
        logger.info(f"{len(swings)} swing points identified")
        return swings
    
    def _classify_swing(
        self,
        index: int,
        is_low: bool = False
    ) -> Literal['HH', 'HL', 'LH', 'LL']:
        """
        طبقه‌بندی نوع سوئینگ بر اساس موقعیت نسبت به سوئینگ‌های قبل
        
        Args:
            index: ایندکس کندل جاری
            is_low: آیا این یک سوئینگ لو است؟
        """
        current_high = self.df['high'].iloc[index]
        current_low = self.df['low'].iloc[index]
        
        # یافتن آخرین سوئینگ هم‌نوع
        relevant_swings = [s for s in self.swing_points if s.is_confirmed]
        
        if is_low:
            higher_swings = [s for s in relevant_swings if s.price > current_low and s.type in ['HL', 'HH']]
            if higher_swings:
                if current_low > max(s.price for s in higher_swings):
                    return 'HL'  # Higher Low
            return 'LL'  # Lower Low
        else:
            higher_swings = [s for s in relevant_swings if s.price < current_high and s.type in ['HL', 'HH']]
            if higher_swings:
                if current_high > max(s.price for s in higher_swings):
                    return 'HH'  # Higher High
            return 'LH'  # Lower High
    
    def _analyze_market_structure(self) -> TrendDirection:
        """
        تحلیل ساختار بازار و شناسایی BOS و CHoCH
        
        BOS: شکست در جهت روند (ادامه)
        CHoCH: شکست در خلاف جهت روند (تغییر روند)
        """
        if not self.swing_points:
            self._identify_swing_points()
        
        trend = TrendDirection.NEUTRAL
        last_high = None
        last_low = None
        last_high_idx = None
        last_low_idx = None
        
        for swing in self.swing_points:
            if swing.type in ['HH', 'LH']:
                if last_high is None or swing.price > last_high:
                    last_high = swing.price
                    last_high_idx = swing.index
            
            if swing.type in ['HL', 'LL']:
                if last_low is None or swing.price < last_low:
                    last_low = swing.price
                    last_low_idx = swing.index
            
            # بررسی شکست‌ها
            current_close = self.df['close'].iloc[min(swing.index + 1, len(self.df) - 1)]
            
            # روند صعودی: قیمت بالاتر از آخرین لو می‌رود
            if trend == TrendDirection.BULLISH and last_low:
                if current_close < last_low:
                    # تغییر روند - CHoCH نزولی
                    self.structures.append(StructureEvent(
                        index=last_low_idx,
                        timestamp=self.df['timestamp'].iloc[last_low_idx],
                        structure_type=StructureType.CHoCH,
                        direction=TrendDirection.BEARISH,
                        price_level=last_low,
                        reference_level=last_low,
                        strength=self._calculate_structure_strength(last_low_idx),
                        description=f"Bearish CHoCH at {last_low}"
                    ))
                    trend = TrendDirection.BEARISH
                    logger.info(f"Bearish CHoCH detected at {last_low}")
            
            # روند نزولی: قیمت پایین‌تر از آخرین های می‌رود
            elif trend == TrendDirection.BEARISH and last_high:
                if current_close > last_high:
                    # تغییر روند - CHoCH صعودی
                    self.structures.append(StructureEvent(
                        index=last_high_idx,
                        timestamp=self.df['timestamp'].iloc[last_high_idx],
                        structure_type=StructureType.CHoCH,
                        direction=TrendDirection.BULLISH,
                        price_level=last_high,
                        reference_level=last_high,
                        strength=self._calculate_structure_strength(last_high_idx),
                        description=f"Bullish CHoCH at {last_high}"
                    ))
                    trend = TrendDirection.BULLISH
                    logger.info(f"Bullish CHoCH detected at {last_high}")
            
            # ادامه روند صعودی
            if trend == TrendDirection.BULLISH and last_low:
                if swing.type in ['HL', 'LL'] and swing.price > last_low:
                    self.structures.append(StructureEvent(
                        index=swing.index,
                        timestamp=swing.timestamp,
                        structure_type=StructureType.BOS,
                        direction=TrendDirection.BULLISH,
                        price_level=swing.price,
                        reference_level=last_low,
                        strength=ZoneStrength.STRONG,
                        description=f"Bullish BOS at {swing.price}"
                    ))
                    last_low = swing.price
                    logger.info(f"Bullish BOS detected at {swing.price}")
            
            # ادامه روند نزولی
            elif trend == TrendDirection.BEARISH and last_high:
                if swing.type in ['HH', 'LH'] and swing.price < last_high:
                    self.structures.append(StructureEvent(
                        index=swing.index,
                        timestamp=swing.timestamp,
                        structure_type=StructureType.BOS,
                        direction=TrendDirection.BEARISH,
                        price_level=swing.price,
                        reference_level=last_high,
                        strength=ZoneStrength.STRONG,
                        description=f"Bearish BOS at {swing.price}"
                    ))
                    last_high = swing.price
                    logger.info(f"Bearish BOS detected at {swing.price}")
            
            # تنظیم اولیه روند
            if trend == TrendDirection.NEUTRAL:
                if last_high and last_low:
                    if last_high > self.df['close'].iloc[0] and last_low > self.df['close'].iloc[0]:
                        trend = TrendDirection.BULLISH
                    elif last_high < self.df['close'].iloc[0] and last_low < self.df['close'].iloc[0]:
                        trend = TrendDirection.BEARISH
        
        return trend
    
    def _calculate_structure_strength(self, index: int) -> ZoneStrength:
        """محاسبه قدرت یک رویداد ساختاری"""
        if index < 3:
            return ZoneStrength.WEAK
        
        # بررسی حجم در ناحیه
        recent_volume = self.df['volume'].iloc[max(0, index-3):index+1].mean()
        avg_volume = self.df['volume'].mean()
        
        if recent_volume > avg_volume * 1.5:
            return ZoneStrength.STRONG
        elif recent_volume > avg_volume:
            return ZoneStrength.MEDIUM
        else:
            return ZoneStrength.WEAK
    
    def _identify_fair_value_gaps(self) -> List[FairValueGap]:
        """
        شناسایی شکاف‌های ارزش منصفانه (FVG)
        
        FVG صعودی: Low[i] > High[i-2]
        FVG نزولی: High[i] < Low[i-2]
        """
        fvgs = []
        
        for i in range(2, len(self.df)):
            current_low = self.df['low'].iloc[i]
            current_high = self.df['high'].iloc[i]
            prev_high = self.df['high'].iloc[i-2]
            prev_low = self.df['low'].iloc[i-2]
            
            # FVG صعودی
            if current_low > prev_high:
                gap_size = current_low - prev_high
                relative_size = gap_size / self.average_price
                
                if relative_size > self.fvg_threshold:
                    strength = self._calculate_fvg_strength(relative_size, i)
                    fvgs.append(FairValueGap(
                        index_start=i-1,
                        timestamp=self.df['timestamp'].iloc[i],
                        direction=TrendDirection.BULLISH,
                        top=current_low,
                        bottom=prev_high,
                        size=gap_size,
                        strength=strength
                    ))
            
            # FVG نزولی
            if current_high < prev_low:
                gap_size = prev_low - current_high
                relative_size = gap_size / self.average_price
                
                if relative_size > self.fvg_threshold:
                    strength = self._calculate_fvg_strength(relative_size, i)
                    fvgs.append(FairValueGap(
                        index_start=i-1,
                        timestamp=self.df['timestamp'].iloc[i],
                        direction=TrendDirection.BEARISH,
                        top=prev_low,
                        bottom=current_high,
                        size=gap_size,
                        strength=strength
                    ))
        
        self.fvgs = fvgs
        logger.info(f"{len(fvgs)} FVGs identified")
        return fvgs
    
    def _calculate_fvg_strength(self, relative_size: float, index: int) -> ZoneStrength:
        """محاسبه قدرت FVG"""
        if relative_size > 0.005:
            return ZoneStrength.VERY_STRONG
        elif relative_size > 0.002:
            return ZoneStrength.STRONG
        elif relative_size > 0.001:
            return ZoneStrength.MEDIUM
        else:
            return ZoneStrength.WEAK
    
    def _identify_order_blocks(self) -> List[OrderBlock]:
        """
        شناسایی نواحی سفارش (Order Blocks)
        
        ناحیه سفارش آخرین کندل مخالف روند قبل از یک حرکت قوی است.
        """
        if not self.structures:
            self._analyze_market_structure()
        
        order_blocks = []
        
        for structure in self.structures:
            if structure.index < self.ob_lookback:
                continue
            
            # محدوده جستجو
            start_idx = max(0, structure.index - self.ob_lookback)
            end_idx = structure.index
            
            window = self.df.iloc[start_idx:end_idx]
            
            if structure.direction == TrendDirection.BULLISH:
                # جستجوی آخرین کندل نزولی
                bearish_candles = window[window['is_bearish']]
                if not bearish_candles.empty:
                    # انتخاب آخرین کندل نزولی یا کندل با بیشترین حجم
                    last_bearish = bearish_candles.iloc[-1]
                    volume_ratio = last_bearish['volume'] / self.df['volume'].mean()
                    
                    # تعیین قدرت
                    if structure.structure_type == StructureType.CHoCH:
                        strength = ZoneStrength.VERY_STRONG
                    elif volume_ratio > 1.5:
                        strength = ZoneStrength.STRONG
                    else:
                        strength = ZoneStrength.MEDIUM
                    
                    order_blocks.append(OrderBlock(
                        index_start=int(last_bearish.name),
                        timestamp_start=last_bearish['timestamp'],
                        direction=TrendDirection.BULLISH,
                        top=last_bearish['high'],
                        bottom=last_bearish['low'],
                        body_top=last_bearish['body_top'],
                        body_bottom=last_bearish['body_bottom'],
                        strength=strength,
                        volume_profile=volume_ratio
                    ))
            
            elif structure.direction == TrendDirection.BEARISH:
                # جستجوی آخرین کندل صعودی
                bullish_candles = window[window['is_bullish']]
                if not bullish_candles.empty:
                    last_bullish = bullish_candles.iloc[-1]
                    volume_ratio = last_bullish['volume'] / self.df['volume'].mean()
                    
                    if structure.structure_type == StructureType.CHoCH:
                        strength = ZoneStrength.VERY_STRONG
                    elif volume_ratio > 1.5:
                        strength = ZoneStrength.STRONG
                    else:
                        strength = ZoneStrength.MEDIUM
                    
                    order_blocks.append(OrderBlock(
                        index_start=int(last_bullish.name),
                        timestamp_start=last_bullish['timestamp'],
                        direction=TrendDirection.BEARISH,
                        top=last_bullish['high'],
                        bottom=last_bullish['low'],
                        body_top=last_bullish['body_top'],
                        body_bottom=last_bullish['body_bottom'],
                        strength=strength,
                        volume_profile=volume_ratio
                    ))
        
        self.order_blocks = order_blocks
        logger.info(f"{len(order_blocks)} Order Blocks identified")
        return order_blocks
    
    def _identify_liquidity(self) -> List[LiquidityPool]:
        """
        شناسایی نواحی نقدینگی
        
        شامل:
        - EQH: Equal Highs (های هم‌قیمت)
        - EQL: Equal Lows (لو‌های هم‌قیمت)
        - HPS/LPS: High/Low Probability Sweep areas
        """
        if not self.swing_points:
            self._identify_swing_points()
        
        liquidity_pools = []
        threshold_price = self.average_price * self.liquidity_threshold
        
        # گروه‌بندی سوئینگ‌های های
        high_prices = [(s.index, s.price, s.type) for s in self.swing_points if s.type in ['HH', 'LH']]
        low_prices = [(s.index, s.price, s.type) for s in self.swing_points if s.type in ['HL', 'LL']]
        
        # یافتن هم‌قیمت‌ها (EQH/EQL)
        for i in range(len(high_prices)):
            for j in range(i+1, len(high_prices)):
                if abs(high_prices[i][1] - high_prices[j][1]) < threshold_price:
                    count = sum(1 for k in range(len(high_prices)) 
                               if abs(high_prices[k][1] - high_prices[i][1]) < threshold_price)
                    if count >= 2:
                        liquidity_pools.append(LiquidityPool(
                            type='EQH',
                            price=high_prices[i][1],
                            strength=ZoneStrength.STRONG if count >= 3 else ZoneStrength.MEDIUM,
                            count=count
                        ))
                        break
        
        for i in range(len(low_prices)):
            for j in range(i+1, len(low_prices)):
                if abs(low_prices[i][1] - low_prices[j][1]) < threshold_price:
                    count = sum(1 for k in range(len(low_prices)) 
                               if abs(low_prices[k][1] - low_prices[i][1]) < threshold_price)
                    if count >= 2:
                        liquidity_pools.append(LiquidityPool(
                            type='EQL',
                            price=low_prices[i][1],
                            strength=ZoneStrength.STRONG if count >= 3 else ZoneStrength.MEDIUM,
                            count=count
                        ))
                        break
        
        # بررسی سوئیپ‌های اخیر
        current_idx = len(self.df) - 1
        for pool in liquidity_pools:
            if pool.type == 'EQH':
                if self.current_price > pool.price:
                    pool.swept = True
                    pool.swept_at = current_idx
            else:  # EQL
                if self.current_price < pool.price:
                    pool.swept = True
                    pool.swept_at = current_idx
        
        self.liquidity_pools = liquidity_pools
        logger.info(f"{len(liquidity_pools)} liquidity pools identified")
        return liquidity_pools
    
    def _calculate_market_condition(self, trend: TrendDirection) -> MarketCondition:
        """محاسبه شرایط کلی بازار"""
        recent_volume = self.df['volume'].iloc[-5:].mean()
        avg_volume = self.df['volume'].mean()
        
        if recent_volume > avg_volume * 1.5:
            volume_status = 'HIGH'
        elif recent_volume < avg_volume * 0.7:
            volume_status = 'LOW'
        else:
            volume_status = 'NORMAL'
        
        # قدرت روند
        if trend == TrendDirection.NEUTRAL:
            trend_strength = 0.0
        else:
            highs = self.df['high'].rolling(window=20).max()
            lows = self.df['low'].rolling(window=20).min()
            if trend == TrendDirection.BULLISH:
                trend_strength = (self.current_price - lows.iloc[-1]) / (highs.iloc[-1] - lows.iloc[-1] + 0.001)
            else:
                trend_strength = (highs.iloc[-1] - self.current_price) / (highs.iloc[-1] - lows.iloc[-1] + 0.001)
        
        self.market_condition = MarketCondition(
            trend=trend,
            trend_strength=min(1.0, max(0.0, trend_strength)),
            current_price=self.current_price,
            volatility=self.current_volatility,
            volume_status=volume_status,
            last_updated=self.df['timestamp'].iloc[-1]
        )
        
        return self.market_condition
    
    def _check_mitigation(self):
        """بررسی mitigation نواحی"""
        # بررسی Order Blocks
        for ob in self.order_blocks:
            if ob.direction == TrendDirection.BULLISH:
                if self.current_price < ob.bottom:
                    ob.mitigated = True
            else:
                if self.current_price > ob.top:
                    ob.mitigated = True
        
        # بررسی FVGs
        for fvg in self.fvgs:
            if fvg.direction == TrendDirection.BULLISH:
                if self.current_price < fvg.bottom:
                    fvg.mitigated = True
            else:
                if self.current_price > fvg.top:
                    fvg.mitigated = True
    
    def analyze(self) -> Dict:
        """
        اجرای کامل تحلیل SMC
        
        Returns:
            دیکشنری حاوی تمام نتایج تحلیل به صورت ساختاریافته
        """
        logger.info("Starting SMC analysis...")
        
        # اجرای تمام مراحل تحلیل
        self._identify_swing_points()
        trend = self._analyze_market_structure()
        self._identify_fair_value_gaps()
        self._identify_order_blocks()
        self._identify_liquidity()
        self._check_mitigation()
        self._calculate_market_condition(trend)
        
        # فیلتر نواحی فعال (نزدیک به قیمت فعلی)
        active_obs = sorted(
            [ob for ob in self.order_blocks if not ob.mitigated],
            key=lambda x: abs((x.top + x.bottom) / 2 - self.current_price)
        )[:3]
        
        active_fvgs = sorted(
            [fvg for fvg in self.fvgs if not fvg.mitigated],
            key=lambda x: abs((x.top + x.bottom) / 2 - self.current_price)
        )[:3]
        
        # آماده‌سازی خروجی
        result = {
            "market_condition": {
                "trend": self.market_condition.trend.value if self.market_condition else "NEUTRAL",
                "trend_strength": round(self.market_condition.trend_strength, 2) if self.market_condition else 0,
                "current_price": round(self.current_price, 2),
                "volatility": "HIGH" if self.current_volatility > self.avg_volatility else "NORMAL",
                "volume_status": self.market_condition.volume_status if self.market_condition else "NORMAL",
                "timestamp": str(self.df['timestamp'].iloc[-1])
            },
            "recent_structures": [
                {
                    "type": s.structure_type.value,
                    "direction": s.direction.value,
                    "price_level": round(s.price_level, 2),
                    "strength": s.strength.value,
                    "description": s.description,
                    "time_ago": f"{(len(self.df) - s.index)} candles ago"
                }
                for s in self.structures[-5:]
            ],
            "key_levels": {
                "order_blocks": [
                    {
                        "type": "OB",
                        "direction": ob.direction.value,
                        "zone": f"{round(ob.bottom)} - {round(ob.top)}",
                        "top": round(ob.top, 2),
                        "bottom": round(ob.bottom, 2),
                        "strength": ob.strength.value,
                        "mitigated": ob.mitigated
                    }
                    for ob in active_obs
                ],
                "fair_value_gaps": [
                    {
                        "type": "FVG",
                        "direction": fvg.direction.value,
                        "zone": f"{round(fvg.bottom)} - {round(fvg.top)}",
                        "top": round(fvg.top, 2),
                        "bottom": round(fvg.bottom, 2),
                        "size": round(fvg.size, 2),
                        "strength": fvg.strength.value,
                        "mitigated": fvg.mitigated
                    }
                    for fvg in active_fvgs
                ],
                "liquidity": [
                    {
                        "type": lp.type,
                        "price": round(lp.price, 2),
                        "strength": lp.strength.value,
                        "swept": lp.swept
                    }
                    for lp in self.liquidity_pools[-4:]
                ]
            },
            "summary": self._generate_summary(active_obs, active_fvgs),
            "ai_context": self._generate_ai_context()
        }
        
        logger.info("SMC analysis completed successfully")
        return result
    
    def _generate_summary(
        self,
        active_obs: List[OrderBlock],
        active_fvgs: List[FairValueGap]
    ) -> str:
        """تولید خلاصه متنی"""
        trend_desc = f"بازار در روند {self.market_condition.trend.value.lower() if self.market_condition else 'خنثی'} قرار دارد"
        
        ob_count = len(active_obs)
        fvg_count = len(active_fvgs)
        
        if ob_count > 0:
            ob_zones = f"{ob_count} ناحیه سفارش فعال شناسایی شد"
        else:
            ob_zones = "هیچ ناحیه سفارش فعالی یافت نشد"
        
        if fvg_count > 0:
            fvg_zones = f"{fvg_count} شکاف FVG فعال یافت شد"
        else:
            fvg_zones = "هیچ FVG فعالی یافت نشد"
        
        return f"{trend_desc}. {ob_zones}. {fvg_zones}"
    
    def _generate_ai_context(self) -> str:
        """تولید متن خلاصه برای هوش مصنوعی"""
        if not self.structures:
            return "ساختار بازار به‌طور کامل شناسایی نشده است"
        
        last_struct = self.structures[-1]
        structures_count = len(self.structures)
        
        context = (
            f"آخرین رویداد ساختاری: {last_struct.direction.value} "
            f"{last_struct.structure_type.value} در قیمت {round(last_struct.price_level, 2)} "
            f"(قدرت: {last_struct.strength.value}). "
            f"مجموع {structures_count} رویداد ساختاری شناسایی شده است. "
            f"روند فعلی: {self.market_condition.trend.value if self.market_condition else 'NEUTRAL'}"
        )
        
        return context
    
    def get_trade_setup(self) -> Optional[Dict]:
        """
        استخراج تنظیم معاملاتی آماده
        
        Returns:
            دیکشنری تنظیم معاملاتی یا None
        """
        if not self.order_blocks or not self.fvgs:
            return None
        
        # یافتن بهترین ناحیه سفارش برای ورود
        valid_obs = [ob for ob in self.order_blocks if not ob.mitigated]
        if not valid_obs:
            return None
        
        best_ob = min(valid_obs, key=lambda x: abs((x.top + x.bottom) / 2 - self.current_price))
        
        # تعیین جهت معامله
        if self.market_condition and self.market_condition.trend == TrendDirection.BULLISH:
            direction = "LONG"
            entry_zone = f"{round(best_ob.bottom, 2)} - {round(best_ob.top, 2)}"
            stop_loss = round(best_ob.bottom - (best_ob.top - best_ob.bottom) * 1.5, 2)
        elif self.market_condition and self.market_condition.trend == TrendDirection.BEARISH:
            direction = "SHORT"
            entry_zone = f"{round(best_ob.bottom, 2)} - {round(best_ob.top, 2)}"
            stop_loss = round(best_ob.top + (best_ob.top - best_ob.bottom) * 1.5, 2)
        else:
            return None
        
        # محاسبه Risk/Reward
        risk = abs(self.current_price - stop_loss)
        reward_multipliers = [1.5, 2.0, 3.0]
        targets = [round(self.current_price + (risk * r) * (1 if direction == "LONG" else -1), 2) for r in reward_multipliers]
        
        return {
            "direction": direction,
            "entry_zone": entry_zone,
            "stop_loss": stop_loss,
            "current_price": round(self.current_price, 2),
            "take_profits": targets,
            "rr_ratios": ["1:1.5", "1:2", "1:3"],
            "confidence_based_on_smc": self._calculate_confidence(best_ob),
            "best_order_block": {
                "strength": best_ob.strength.value,
                "type": "Bullish OB" if best_ob.direction == TrendDirection.BULLISH else "Bearish OB"
            }
        }
    
    def _calculate_confidence(self, ob: OrderBlock) -> int:
        """محاسبه درصد اطمینان بر اساس SMC"""
        confidence = 50  # پایه
        
        # قدرت OB
        if ob.strength == ZoneStrength.VERY_STRONG:
            confidence += 20
        elif ob.strength == ZoneStrength.STRONG:
            confidence += 15
        elif ob.strength == ZoneStrength.MEDIUM:
            confidence += 10
        
        # تأیید روند
        if self.market_condition:
            if self.market_condition.trend.value == ob.direction.value:
                confidence += 15
            confidence += int(self.market_condition.trend_strength * 15)
        
        # حجم
        if ob.volume_profile > 1.5:
            confidence += 10
        elif ob.volume_profile > 1.0:
            confidence += 5
        
        return min(95, max(20, confidence))


def create_smc_analysis(df: pd.DataFrame) -> Dict:
    """
    تابع کمکی برای ایجاد سریع تحلیل SMC
    
    Args:
        df: دیتافریم OHLCV
        
    Returns:
        نتایج تحلیل SMC
    """
    engine = SMCEngine(df)
    return engine.analyze()


def get_trade_setup_from_data(df: pd.DataFrame) -> Optional[Dict]:
    """
    استخراج تنظیم معاملاتی از داده‌ها

    Args:
        df: دیتافریم OHLCV

    Returns:
        تنظیم معاملاتی آماده
    """
    engine = SMCEngine(df)
    engine.analyze()
    return engine.get_trade_setup()


def calculate_mtf_bias(results: Dict[str, Dict]) -> Dict:
    """
    محاسبه بایاس چندتایم فریم از نتایج تحلیل

    Args:
        results: دیکشنری نتایج تحلیل هر تایم فریم

    Returns:
        دیکشنری بایاس، قدرت روند و توصیه
    """
    trends = {}
    strengths = {}

    for tf, data in results.items():
        if data and 'market_condition' in data:
            market = data['market_condition']
            trends[tf] = market.get('trend', 'NEUTRAL')
            strengths[tf] = market.get('trend_strength', 0)

    # تعیین بایاس کلی
    daily_trend = trends.get('1d', 'NEUTRAL')
    h4_trend = trends.get('4h', 'NEUTRAL')
    h1_trend = trends.get('1h', 'NEUTRAL')

    bias = {
        'direction': 'NEUTRAL',
        'description': 'خنثی',
        'emoji': '⚖️',
        'risk_level': 'MEDIUM',
        'confidence': 0,
        'higher_tf_bias': daily_trend,
        'mid_tf_bias': h4_trend,
        'lower_tf_bias': h1_trend
    }

    # منطق تعیین بایاس
    if daily_trend == 'BULLISH':
        if h4_trend == 'BULLISH':
            if h1_trend == 'BULLISH':
                bias['direction'] = 'STRONG_BULLISH'
                bias['description'] = 'صعودی قوی (همه تایم‌فریم‌ها همسو)'
                bias['emoji'] = '🟢🔥'
                bias['risk_level'] = 'LOW'
                bias['confidence'] = 90
            elif h1_trend == 'BEARISH':
                bias['direction'] = 'BULLISH_PULLBACK'
                bias['description'] = 'فرصت خرید در پول‌بک (روند بالا تأیید شده)'
                bias['emoji'] = '🟢💎'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 75
            else:
                bias['direction'] = 'BULLISH'
                bias['description'] = 'صعودی (در انتظار تأیید 1 ساعته)'
                bias['emoji'] = '🟢'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 60
        elif h4_trend == 'BEARISH':
            if h1_trend == 'BULLISH':
                bias['direction'] = 'POTENTIAL_REVERSAL'
                bias['description'] = 'احتمال تغییر روند (واگرایی تایم‌فریم‌ها)'
                bias['emoji'] = '🟡⚠️'
                bias['risk_level'] = 'HIGH'
                bias['confidence'] = 40
            else:
                bias['direction'] = 'MIXED'
                bias['description'] = 'سیگنال متناقض (4h نزولی، 1d صعودی)'
                bias['emoji'] = '🟡'
                bias['risk_level'] = 'HIGH'
                bias['confidence'] = 30
        else:
            if h1_trend == 'BULLISH':
                bias['direction'] = 'EARLY_BULLISH'
                bias['description'] = 'شروع صعود از تایم‌فریم پایین'
                bias['emoji'] = '🟢📈'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 50
            else:
                bias['direction'] = 'BULLISH_WAITING'
                bias['description'] = 'در انتظار تأیید روند صعودی'
                bias['emoji'] = '🟡⏳'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 40

    elif daily_trend == 'BEARISH':
        if h4_trend == 'BEARISH':
            if h1_trend == 'BEARISH':
                bias['direction'] = 'STRONG_BEARISH'
                bias['description'] = 'نزولی قوی (همه تایم‌فریم‌ها همسو)'
                bias['emoji'] = '🔴🔥'
                bias['risk_level'] = 'LOW'
                bias['confidence'] = 90
            elif h1_trend == 'BULLISH':
                bias['direction'] = 'BEARISH_PULLBACK'
                bias['description'] = 'فرصت فروش در رالی (روند بالا تأیید شده)'
                bias['emoji'] = '🔴💎'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 75
            else:
                bias['direction'] = 'BEARISH'
                bias['description'] = 'نزولی (در انتظار تأیید 1 ساعته)'
                bias['emoji'] = '🔴'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 60
        elif h4_trend == 'BULLISH':
            if h1_trend == 'BEARISH':
                bias['direction'] = 'POTENTIAL_REVERSAL'
                bias['description'] = 'احتمال تغییر روند (واگرایی تایم‌فریم‌ها)'
                bias['emoji'] = '🟡⚠️'
                bias['risk_level'] = 'HIGH'
                bias['confidence'] = 40
            else:
                bias['direction'] = 'MIXED'
                bias['description'] = 'سیگنال متناقض (4h صعودی، 1d نزولی)'
                bias['emoji'] = '🟡'
                bias['risk_level'] = 'HIGH'
                bias['confidence'] = 30
        else:
            if h1_trend == 'BEARISH':
                bias['direction'] = 'EARLY_BEARISH'
                bias['description'] = 'شروع نزول از تایم‌فریم پایین'
                bias['emoji'] = '🔴📉'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 50
            else:
                bias['direction'] = 'BEARISH_WAITING'
                bias['description'] = 'در انتظار تأیید روند نزولی'
                bias['emoji'] = '🟡⏳'
                bias['risk_level'] = 'MEDIUM'
                bias['confidence'] = 40

    else:  # NEUTRAL
        if h4_trend == daily_trend:
            bias['direction'] = f'{h1_trend}_CONTINUATION'
            bias['description'] = f'ادامه روند {h1_trend.lower()}'
        else:
            bias['direction'] = 'RANGING'
            bias['description'] = 'بازار رنج (خنثی)'
            bias['emoji'] = '⚖️'

    return bias


def detect_confluence_zones(results: Dict[str, Dict]) -> Dict:
    """
    شناسایی نواحی همگرا (Confluence) در چند تایم فریم

    Args:
        results: دیکشنری نتایج تحلیل هر تایم فریم

    Returns:
        نواحی همگرا با قدرت
    """
    all_zones = {
        'support': [],
        'resistance': [],
        'confluence': []
    }

    # جمع‌آوری همه Order Blocks
    order_blocks_by_tf = {}
    for tf, data in results.items():
        if data and 'key_levels' in data:
            obs = data['key_levels'].get('order_blocks', [])
            for ob in obs:
                zone = {
                    'tf': tf,
                    'type': ob.get('type', 'OB'),
                    'direction': ob.get('direction'),
                    'top': ob.get('top', ob.get('zone', '').split('-')[1] if '-' in str(ob.get('zone', '')) else 0),
                    'bottom': ob.get('bottom', ob.get('zone', '').split('-')[0] if '-' in str(ob.get('zone', '')) else 0),
                    'strength': ob.get('strength', 'Medium'),
                    'zone_str': ob.get('zone', '')
                }
                if ob.get('direction') == 'BULLISH':
                    all_zones['support'].append(zone)
                else:
                    all_zones['resistance'].append(zone)

    # شناسایی همگرایی (overlap بین تایم‌فریم‌ها)
    tolerance = 0.005  # 0.5% tolerance برای همگرایی

    # بررسی همگرایی Support
    for i, sz1 in enumerate(all_zones['support']):
        for sz2 in all_zones['support'][i+1:]:
            if sz1['tf'] != sz2['tf']:
                # بررسی overlap
                overlap = min(sz1['top'], sz2['top']) - max(sz1['bottom'], sz2['bottom'])
                if overlap > 0:
                    confluence_zone = {
                        'type': 'STRONG_SUPPORT',
                        'tfs': [sz1['tf'], sz2['tf']],
                        'top': max(sz1['top'], sz2['top']),
                        'bottom': min(sz1['bottom'], sz2['bottom']),
                        'strength': 'VERY_STRONG' if sz1['strength'] in ['Strong', 'Very Strong'] else 'STRONG',
                        'description': f"{sz1['tf']} + {sz2['tf']} Order Block"
                    }
                    all_zones['confluence'].append(confluence_zone)

    # بررسی همگرایی Resistance
    for i, rz1 in enumerate(all_zones['resistance']):
        for rz2 in all_zones['resistance'][i+1:]:
            if rz1['tf'] != rz2['tf']:
                overlap = min(rz1['top'], rz2['top']) - max(rz1['bottom'], rz2['bottom'])
                if overlap > 0:
                    confluence_zone = {
                        'type': 'STRONG_RESISTANCE',
                        'tfs': [rz1['tf'], rz2['tf']],
                        'top': max(rz1['top'], rz2['top']),
                        'bottom': min(rz1['bottom'], rz2['bottom']),
                        'strength': 'VERY_STRONG' if rz1['strength'] in ['Strong', 'Very Strong'] else 'STRONG',
                        'description': f"{rz1['tf']} + {rz2['tf']} Order Block"
                    }
                    all_zones['confluence'].append(confluence_zone)

    # مرتب‌سازی نواحی همگرا بر اساس قدرت
    all_zones['confluence'].sort(key=lambda x: (
        0 if x['strength'] == 'VERY_STRONG' else 1,
        0 if 'STRONG' in x['strength'] else 1
    ))

    return all_zones


def calculate_volume_profile(df: pd.DataFrame, bins: int = 50) -> Dict:
    """
    محاسبه Volume Profile برای تحلیل حجم معاملات
    
    Volume Profile نشان می‌دهد که حجم معاملات در هر سطح قیمت چقدر است.
    POC (Point of Control) سطح قیمتی است که بیشترین حجم معامله شده.
    
    Args:
        df: دیتافریم OHLCV
        bins: تعداد سطوح قیمتی برای تقسیم‌بندی
        
    Returns:
        دیکشنری حاووانه POC, VAH, VAL و سایر اطلاعات
    """
    if df.empty or len(df) < 10:
        return {
            'poc': None,
            'vah': None,
            'val': None,
            'vp': [],
            'total_volume': 0
        }
    
    # محاسبه ATR برای تعیین اندازه bins
    high_low_range = df['high'].max() - df['low'].min()
    if high_low_range == 0:
        high_low_range = df['close'].max() * 0.02
    
    # اندازه هر bin
    bin_size = high_low_range / bins
    
    # ایجاد bins قیمتی
    min_price = df['low'].min()
    price_bins = []
    volumes = []
    
    for i in range(bins + 1):
        price_level = min_price + (i * bin_size)
        price_bins.append(price_level)
        volumes.append(0)
    
    # توزیع حجم در bins
    total_volume = 0
    for _, row in df.iterrows():
        # حجم هر کندل را به قیمت بسته شدن نسبت می‌دهیم
        close_price = row['close']
        volume = row['volume']
        
        # یافتن bin مربوطه
        bin_index = int((close_price - min_price) / bin_size)
        if 0 <= bin_index < len(volumes):
            volumes[bin_index] += volume
            total_volume += volume
    
    # یافتن POC (بالاترین حجم)
    poc_index = volumes.index(max(volumes))
    poc_price = price_bins[poc_index]
    
    # محاسبه Value Area (70% حجم کل)
    target_volume = total_volume * 0.70
    current_volume = 0
    poc_volume = volumes[poc_index]
    
    # گسترش از POC به بالا و پایین
    vah_index = poc_index
    val_index = poc_index
    
    # اضافه کردن volume بالای POC
    for i in range(poc_index + 1, len(volumes)):
        if current_volume + volumes[i] <= target_volume - poc_volume:
            current_volume += volumes[i]
            vah_index = i
        else:
            break
    
    # اضافه کردن volume پایین POC
    current_volume = 0
    for i in range(poc_index - 1, -1, -1):
        if current_volume + volumes[i] <= target_volume - poc_volume:
            current_volume += volumes[i]
            val_index = i
        else:
            break
    
    vah_price = price_bins[vah_index] if vah_index < len(price_bins) else poc_price
    val_price = price_bins[val_index] if val_index < len(price_bins) else poc_price
    
    # آماده‌سازی داده‌های VP برای نمایش
    vp_data = []
    for i, (price, vol) in enumerate(zip(price_bins[:-1], volumes)):
        normalized_vol = vol / max(volumes) if max(volumes) > 0 else 0
        vp_data.append({
            'price': price,
            'price_top': price + bin_size,
            'volume': vol,
            'normalized_volume': normalized_vol
        })
    
    # مرتب‌سازی بر اساس حجم
    vp_data.sort(key=lambda x: x['volume'], reverse=True)
    
    return {
        'poc': round(poc_price, 2),
        'vah': round(vah_price, 2),
        'val': round(val_price, 2),
        'poc_volume': max(volumes),
        'total_volume': total_volume,
        'bin_size': bin_size,
        'value_area_ratio': 0.70,
        'top_volumes': vp_data[:10],  # ۱۰ سطح پرحجم
        'description': f"POC: ${poc_price:,.0f} | VAH: ${vah_price:,.0f} | VAL: ${val_price:,.0f}"
    }


def calculate_trade_levels(
    symbol: str,
    current_price: float,
    bias: Dict,
    confluence: Dict,
    results: Dict[str, Dict]
) -> Dict:
    """
    محاسبه سطوح معاملاتی (ورود، حد ضرر، حد سود)

    Args:
        symbol: نماد ارز
        current_price: قیمت فعلی
        bias: بایاس تحلیل
        confluence: نواحی همگرا
        results: نتایج تحلیل هر تایم فریم

    Returns:
        دیکشنری سطوح معاملاتی
    """
    trade = {
        'direction': None,  # LONG, SHORT, یا None
        'entry_zone': None,
        'stop_loss': None,
        'take_profits': [],
        'rr_ratio': None,
        'confidence': bias.get('confidence', 50),
        'rationale': ''
    }

    direction = bias.get('direction', '')

    # استخراج نواحی پشتیبانی و مقاومت
    supports = confluence.get('support', [])
    resistances = confluence.get('resistance', [])
    confluences = confluence.get('confluence', [])

    # مرتب کردن بر اساس قدرت
    supports.sort(key=lambda x: (
        0 if x.get('strength') in ['Very Strong', 'Strong'] else 1,
        -x.get('bottom', 0)
    ), reverse=True)
    resistances.sort(key=lambda x: (
        0 if x.get('strength') in ['Very Strong', 'Strong'] else 1,
        x.get('top', 0)
    ))

    # منطق تعیین سطوح بر اساس بایاس
    if 'BULLISH' in direction and 'PULLBACK' in direction:
        # صعودی - ورود در ناحیه تقاضا
        trade['direction'] = 'LONG'

        # پیدا کردن بهترین ناحیه تقاضا
        best_support = None
        for s in supports:
            if s.get('bottom', 0) < current_price:
                best_support = s
                break

        if best_support:
            entry_bottom = best_support.get('bottom', current_price * 0.99)
            entry_top = best_support.get('top', current_price * 0.995)
            trade['entry_zone'] = f"${entry_bottom:,.4f} - ${entry_top:,.4f}"

            # حد ضرر: زیر ناحیه تقاضا
            trade['stop_loss'] = entry_bottom * 0.99

            # حد سودها: مقاومت‌های بالا
            for r in resistances[:2]:
                trade['take_profits'].append(r.get('top', current_price * 1.02))

            # اگر مقاومت نبود، از فیبوناچی استفاده کن
            if not trade['take_profits']:
                trade['take_profits'] = [
                    current_price * 1.02,
                    current_price * 1.05,
                    current_price * 1.08
                ]

            # محاسبه R:R
            if trade['stop_loss'] and trade['take_profits']:
                risk = current_price - trade['stop_loss']
                if risk > 0:
                    reward = trade['take_profits'][0] - current_price
                    trade['rr_ratio'] = reward / risk if risk > 0 else 0

            trade['rationale'] = f"ورود در ناحیه تقاضای {best_support.get('tf', '1h')}"

    elif 'BEARISH' in direction and 'PULLBACK' in direction:
        # نزولی - ورود در ناحیه عرضه
        trade['direction'] = 'SHORT'

        # پیدا کردن بهترین ناحیه عرضه
        best_resistance = None
        for r in resistances:
            if r.get('top', 0) > current_price:
                best_resistance = r
                break

        if best_resistance:
            entry_bottom = best_resistance.get('bottom', current_price * 1.005)
            entry_top = best_resistance.get('top', current_price * 1.01)
            trade['entry_zone'] = f"${entry_bottom:,.4f} - ${entry_top:,.4f}"

            # حد ضرر: بالای ناحیه عرضه
            trade['stop_loss'] = entry_top * 1.01

            # حد سودها: حمایت‌های پایین
            for s in supports[:2]:
                trade['take_profits'].append(s.get('bottom', current_price * 0.98))

            # اگر حمایت نبود، از فیبوناچی استفاده کن
            if not trade['take_profits']:
                trade['take_profits'] = [
                    current_price * 0.98,
                    current_price * 0.95,
                    current_price * 0.92
                ]

            # محاسبه R:R
            if trade['stop_loss'] and trade['take_profits']:
                risk = trade['stop_loss'] - current_price
                if risk > 0:
                    reward = current_price - trade['take_profits'][0]
                    trade['rr_ratio'] = reward / risk if risk > 0 else 0

            trade['rationale'] = f"ورود در ناحیه عرضه {best_resistance.get('tf', '1h')}"

    elif direction == 'STRONG_BULLISH':
        # روند صعودی قوی - ورود در هر پول‌بک
        trade['direction'] = 'LONG'
        trade['entry_zone'] = f"${current_price * 0.995:,.4f} - ${current_price:,.4f}"
        trade['stop_loss'] = current_price * 0.98
        trade['take_profits'] = [
            current_price * 1.03,
            current_price * 1.06,
            current_price * 1.10
        ]
        trade['rr_ratio'] = 2.0
        trade['rationale'] = 'روند صعودی قوی - ورود aggressive'

    elif direction == 'STRONG_BEARISH':
        # روند نزولی قوی - فروش در هر رالی
        trade['direction'] = 'SHORT'
        trade['entry_zone'] = f"${current_price:,.4f} - ${current_price * 1.005:,.4f}"
        trade['stop_loss'] = current_price * 1.02
        trade['take_profits'] = [
            current_price * 0.97,
            current_price * 0.94,
            current_price * 0.90
        ]
        trade['rr_ratio'] = 2.0
        trade['rationale'] = 'روند نزولی قوی - ورود aggressive'

    else:
        # بازار رنج یا نامشخص - سیگنال نده
        trade['rationale'] = 'بازار رنج - ورود risk defined'
        trade['entry_zone'] = f"${current_price * 0.99:,.4f} - ${current_price * 1.01:,.4f}"
        trade['stop_loss'] = current_price * 0.985
        trade['take_profits'] = [
            current_price * 1.015,
            current_price * 1.025
        ]
        if trade['stop_loss']:
            risk = abs(current_price - trade['stop_loss'])
            reward = trade['take_profits'][0] - current_price if trade['take_profits'] else 0
            trade['rr_ratio'] = reward / risk if risk > 0 else 0

    return trade


def format_mtf_analysis_message(
    symbol: str,
    price: float,
    bias: Dict,
    confluence: Dict,
    results: Dict[str, Dict],
    trade: Dict = None
) -> str:
    """
    فرمت‌بندی پیام تحلیل چندتایم فریم

    Args:
        symbol: نماد ارز
        price: قیمت فعلی
        bias: بایاس تحلیل
        confluence: نواحی همگرا
        results: نتایج تحلیل هر تایم فریم
        trade: سطوح معاملاتی (اختیاری)

    Returns:
        رشته فرمت‌شده پیام
    """
    # انتخاب ایموجی روند
    trend_emoji = {
        'BULLISH': '🟢',
        'BEARISH': '🔴',
        'NEUTRAL': '⚪'
    }

    # خط اول - بایاس و قیمت
    message = f"📊 تحلیل MTF SMC - {symbol}\n"
    message += f"{'─' * 30}\n\n"

    message += f"{bias['emoji']} بایاس کلی: {bias['description']}\n"
    message += f"💰 قیمت فعلی: ${price:,.4f}\n"
    message += f"📊 اعتماد تحلیل: {bias['confidence']}%\n\n"

    # روند هر تایم فریم
    message += f"{'─' * 30}\n"
    message += f"🕒 روند تایم‌فریم‌ها:\n"

    tf_names = {'1d': 'روزانه', '4h': '۴ ساعته', '1h': '۱ ساعته'}
    for tf in ['1d', '4h', '1h']:
        if tf in results and results[tf]:
            trend = results[tf].get('market_condition', {}).get('trend', 'NEUTRAL')
            strength = results[tf].get('market_condition', {}).get('trend_strength', 0)
            emoji = trend_emoji.get(trend, '⚪')
            name = tf_names.get(tf, tf)
            message += f"• {name}: {emoji} {trend} ({strength:.0%})\n"

    message += f"{'─' * 30}\n"

    # نواحی همگرا (مهم‌ترین بخش)
    if confluence['confluence']:
        message += f"\n💎 نواحی همگرا (با قدرت بالا):\n"
        for i, zone in enumerate(confluence['confluence'][:3], 1):
            zone_type = '🟢' if zone['type'] == 'STRONG_SUPPORT' else '🔴'
            top = zone['top']
            bottom = zone['bottom']
            message += f"{i}. {zone_type} ${bottom:,.4f} - ${top:,.4f}\n"
            message += f"   📌 {', '.join(zone['tfs'])} | قدرت: {zone['strength']}\n"
        message += "\n"
    else:
        # اگر همگرایی نیست، بهترین OB را نشان بده
        if confluence['support']:
            best_support = confluence['support'][0]
            message += f"\n🟢 بهترین ناحیه تقاضا: ${best_support['zone_str']}\n"
            message += f"   قدرت: {best_support['strength']} | تایم‌فریم: {best_support['tf']}\n\n"
        if confluence['resistance']:
            best_resistance = confluence['resistance'][0]
            message += f"🔴 بهترین ناحیه عرضه: ${best_resistance['zone_str']}\n"
            message += f"   قدرت: {best_resistance['strength']} | تایم‌فریم: {best_resistance['tf']}\n\n"

    # 📊 سطوح معاملاتی (اگر موجود باشد)
    if trade:
        direction = trade.get('direction')
        direction_emoji = '📈' if direction == 'LONG' else ('📉' if direction == 'SHORT' else '⚖️')
        direction_text = 'خرید (LONG)' if direction == 'LONG' else ('فروش (SHORT)' if direction == 'SHORT' else 'خنثی (NEUTRAL)')

        message += f"{'─' * 30}\n"
        message += f"\n💰 سطوح معاملاتی:\n\n"

        message += f"{direction_emoji} جهت: {direction_text}\n"
        message += f"📍 ناحیه ورود: {trade.get('entry_zone', 'در انتظار')}\n"
        message += f"🛑 حد ضرر (SL): ${trade.get('stop_loss', 0):,.4f}\n"
        message += f"🎯 حد سودها (TP):\n"

        for i, tp in enumerate(trade.get('take_profits', []), 1):
            message += f"   TP{i}: ${tp:,.4f}\n"

        rr = trade.get('rr_ratio')
        if rr:
            rr_stars = '⭐' * min(int(rr), 5)
            message += f"\n📊 ریسک به ریوارد: {rr:.2f} {rr_stars}\n"

        message += f"\n💡 منطق: {trade.get('rationale', '')}\n"

    # وضعیت فعلی قیمت
    message += f"{'─' * 30}\n"
    message += f"\n📍 وضعیت قیمت:\n"

    # پیدا کردن نزدیک‌ترین Support
    if confluence['support']:
        nearest_support = min(confluence['support'], key=lambda x: abs(price - x.get('top', 0)))
        distance_to_support = (price - nearest_support.get('top', 0)) / price * 100
        message += f"• نزدیک‌ترین تقاضا: ${nearest_support.get('zone_str', 'N/A')} ({distance_to_support:.1f}% پایین)\n"

    # پیدا کردن نزدیک‌ترین Resistance
    if confluence['resistance']:
        nearest_resistance = min(confluence['resistance'], key=lambda x: abs(x.get('bottom', 0) - price))
        distance_to_resistance = (nearest_resistance.get('bottom', 0) - price) / price * 100
        message += f"• نزدیک‌ترین عرضه: ${nearest_resistance.get('zone_str', 'N/A')} ({distance_to_resistance:.1f}% بالا)\n"

    # توصیه نهایی
    message += f"\n{'─' * 30}\n"
    message += f"\n🎯 توصیه معاملاتی:\n"

    if bias['direction'] in ['STRONG_BULLISH', 'BULLISH_PULLBACK', 'BULLISH']:
        risk_level = bias.get('risk_level', 'MEDIUM')
        message += f"📈 جهت: خرید (LONG)\n"
        if confluence['support']:
            entry_zone = f"${confluence['support'][0].get('zone_str', 'N/A')}"
            message += f"📍 ناحیه ورود: {entry_zone}\n"
        message += f"⚠️ ریسک: {risk_level}\n"
        message += f"💡 از اهرم مناسب استفاده کنید\n"

    elif bias['direction'] in ['STRONG_BEARISH', 'BEARISH_PULLBACK', 'BEARISH']:
        risk_level = bias.get('risk_level', 'MEDIUM')
        message += f"📉 جهت: فروش (SHORT)\n"
        if confluence['resistance']:
            entry_zone = f"${confluence['resistance'][0].get('zone_str', 'N/A')}"
            message += f"📍 ناحیه ورود: {entry_zone}\n"
        message += f"⚠️ ریسک: {risk_level}\n"
        message += f"💡 از اهرم مناسب استفاده کنید\n"

    else:
        message += f"⚖️ توصیه: صبر برای وضوح بیشتر روند\n"
        message += f"💡 منتظر شکست ساختار بمانید\n"

    message += f"\n{'─' * 30}\n"
    message += f"\n⚠️ مدیریت ریسک:\n"
    message += f"• بیش از 2% سرمایه ریسک نکنید\n"
    message += f"• حد ضرر را حتماً تعیین کنید\n"
    message += f"• تایم‌فریم بالاتر را در نظر بگیرید"

    return message
