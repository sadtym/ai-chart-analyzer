# -*- coding: utf-8 -*-
"""
ماژول تولید سیگنال معاملاتی
Trading Signal Generator Module

این ماژول سیگنال‌های معاملاتی واضح و عملیاتی تولید می‌کند
شامل: ورود، حد ضرر، اهداف قیمتی و نسبت ریسک/پاداش

قابلیت‌ها:
- تولید سیگنال‌های خرید/فروش/نگهداری
- محاسبه سطوح معاملاتی
- ارزیابی ریسک و پاداش
- خلاصه‌سازی دلایل سیگنال
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# تنظیم لاگینگ
logger = logging.getLogger(__name__)


class SignalDirection(Enum):
    """جهت سیگنال"""
    STRONG_BUY = "🔴 خرید قوی"
    BUY = "🟢 خرید"
    NEUTRAL = "🟡 خنثی"
    SELL = "🔴 فروش"
    STRONG_SELL = "🔴 فروش قوی"


class SignalStrength(Enum):
    """قدرت سیگنال"""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class TradingSignal:
    """ساختار داده سیگنال معاملاتی"""
    # اطلاعات پایه
    symbol: str = ""
    direction: SignalDirection = SignalDirection.NEUTRAL
    strength: SignalStrength = SignalStrength.MODERATE
    confidence: int = 50  # 0-100
    
    # سطوح معاملاتی
    current_price: float = 0.0
    entry_zone: Tuple[float, float] = (0.0, 0.0)  # محدوده ورود
    stop_loss: float = 0.0
    take_profit_1: float = 0.0  # هدف اول
    take_profit_2: float = 0.0  # هدف دوم
    take_profit_3: float = 0.0  # هدف سوم
    
    # نسبت ریسک/پاداش
    risk_reward_ratio: float = 0.0
    risk_amount: float = 0.0  # درصد ریسک
    reward_amount: float = 0.0  # درصد پاداش
    
    # احساسات بازار
    sentiment_technical: str = "خنثی"
    sentiment_fundamental: str = "خنثی"
    sentiment_macro: str = "خنثی"
    
    # دلایل سیگنال
    bullish_reasons: list = field(default_factory=list)
    bearish_reasons: list = field(default_factory=list)
    neutral_reasons: list = field(default_factory=list)
    
    # اطلاعات تکمیلی
    key_levels: Dict[str, float] = field(default_factory=dict)
    market_context: str = ""
    outlook: str = ""
    timestamp: str = ""
    
    # اطلاعات فاندامنتال
    market_cap: float = 0.0
    tvl: float = 0.0
    volume_24h: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")


class SignalGenerator:
    """
    تولیدکننده سیگنال معاملاتی
    
    این کلاس با ترکیب تحلیل‌های تکنیکال، فاندامنتال و کلان
    سیگنال‌های معاملاتی واضح و عملیاتی تولید می‌کند.
    """
    
    def __init__(self):
        """راه‌اندازی تولیدکننده سیگنال"""
        logger.info("📊 Signal Generator راه‌اندازی شد")
    
    def generate_signal(
        self,
        symbol: str,
        current_price: float,
        smc_result: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        fundamental_data: Optional[Dict] = None
    ) -> TradingSignal:
        """
        تولید سیگنال معاملاتی کامل
        
        Args:
            symbol: نماد معاملاتی
            current_price: قیمت فعلی
            smc_result: نتیجه تحلیل SMC
            macro_data: داده‌های کلان اقتصادی
            fundamental_data: داده‌های فاندامنتال
        
        Returns:
            TradingSignal: سیگنال معاملاتی کامل
        """
        try:
            signal = TradingSignal(
                symbol=symbol,
                current_price=current_price
            )
            
            # ═══════════════════════════════════════════════════════
            # مرحله 1: تحلیل تکنیکال (SMC)
            # ═══════════════════════════════════════════════════════
            
            tech_score = self._analyze_technical(smc_result, signal)
            
            # ═══════════════════════════════════════════════════════
            # مرحله 2: تحلیل فاندامنتال
            # ═══════════════════════════════════════════════════════
            
            fund_score = self._analyze_fundamental(fundamental_data, signal)
            
            # ═══════════════════════════════════════════════════════
            # مرحله 3: تحلیل کلان اقتصادی
            # ═══════════════════════════════════════════════════════
            
            macro_score = self._analyze_macro(macro_data, signal)
            
            # ═══════════════════════════════════════════════════════
            # مرحله 4: محاسبه سیگنال نهایی
            # ═══════════════════════════════════════════════════════
            
            self._calculate_final_signal(signal, tech_score, fund_score, macro_score)
            
            # ═══════════════════════════════════════════════════════
            # مرحله 5: محاسبه سطوح معاملاتی
            # ═══════════════════════════════════════════════════════
            
            self._calculate_trade_levels(signal)
            
            # ═══════════════════════════════════════════════════════
            # مرحله 6: تولید زمینه بازار و چشم‌انداز
            # ═══════════════════════════════════════════════════════
            
            self._generate_market_context(signal)
            
            logger.info(f"✅ سیگنال تولید شد: {symbol} - {signal.direction.value}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ خطا در تولید سیگنال: {e}")
            return self._create_default_signal(symbol, current_price, str(e))
    
    def _analyze_technical(self, smc_result: Optional[Dict], signal: TradingSignal) -> float:
        """تحلیل تکنیکال و امتیازدهی"""
        score = 0
        
        if smc_result:
            bias = smc_result.get('bias', 'NEUTRAL').upper()
            confidence = smc_result.get('confidence', 50)
            
            signal.sentiment_technical = bias
            
            # امتیازدهی بر اساس بایاس
            if 'BULLISH' in bias:
                score += 30
                signal.bullish_reasons.append(f"ساختار تکنیکال صعودی ({bias})")
            elif 'BEARISH' in bias:
                score -= 30
                signal.bearish_reasons.append(f"ساختار تکنیکال نزولی ({bias})")
            else:
                signal.neutral_reasons.append("ساختار تکنیکال خنثی")
            
            # امتیاز اعتماد
            if confidence >= 80:
                score += 20
                signal.bullish_reasons.append(f"اعتماد تکنیکال بسیار بالا ({confidence}%)")
            elif confidence >= 60:
                score += 10
            elif confidence < 30:
                score -= 10
                signal.bearish_reasons.append(f"اعتماد تکنیکال پایین ({confidence}%)")
            
            # بررسی شاخص‌های SMC
            swing_points = smc_result.get('swing_points', 0)
            fvgs = smc_result.get('fvgs', 0)
            
            if swing_points > 20:
                signal.bullish_reasons.append(f"تعداد نقاط سوئینگ مناسب ({swing_points})")
            
            if fvgs > 30:
                signal.bullish_reasons.append(f"تعداد FVGs مناسب برای ورود ({fvgs})")
        
        return score
    
    def _analyze_fundamental(self, fundamental_data: Optional[Dict], signal: TradingSignal) -> float:
        """تحلیل فاندامنتال و امتیازدهی"""
        score = 0
        
        if fundamental_data:
            # Market Cap
            mcap = fundamental_data.get('market_cap', 0)
            if mcap > 1e9:  # > 1B
                score += 5
                signal.bullish_reasons.append(f"ارزش بازار بالا (${mcap/1e9:.1f}B)")
            
            # TVL
            tvl = fundamental_data.get('tvl', 0)
            signal.tvl = tvl
            if tvl > 1e11:  # > 100B
                score += 15
                signal.bullish_reasons.append(f"TVL بسیار قوی (${tvl/1e9:.1f}B)")
            elif tvl > 1e10:  # > 10B
                score += 10
                signal.bullish_reasons.append(f"TVL مناسب (${tvl/1e9:.1f}B)")
            
            # TVL/Market Cap Ratio
            if mcap > 0 and tvl > 0:
                ratio = tvl / mcap
                if ratio > 0.5:
                    score += 10
                    signal.bullish_reasons.append("نسبت TVL به Market Cap بالا")
                elif ratio < 0.1:
                    signal.bearish_reasons.append("نسبت TVL به Market Cap پایین")
            
            # Market Cap
            signal.market_cap = mcap
            mcap_change = fundamental_data.get('market_cap_change_24h', 0)
            if mcap_change > 5:
                score += 5
                signal.bullish_reasons.append(f"رشد 24h قابل توجه ({mcap_change:+.1f}%)")
            elif mcap_change < -5:
                score -= 5
                signal.bearish_reasons.append(f"کاهش 24h قابل توجه ({mcap_change:+.1f}%)")
            
            signal.sentiment_fundamental = "صعودی" if score > 0 else "نزولی" if score < 0 else "خنثی"
        
        return score
    
    def _analyze_macro(self, macro_data: Optional[Dict], signal: TradingSignal) -> float:
        """تحلیل کلان اقتصادی و امتیازدهی"""
        score = 0
        
        if macro_data:
            # Interest Rate
            interest_rate = macro_data.get('interest_rate', 0)
            if interest_rate > 5:
                signal.bearish_reasons.append(f"نرخ بهره بالا ({interest_rate:.2f}%)")
                score -= 10
            elif interest_rate < 3:
                signal.bullish_reasons.append(f"نرخ بهره پایین ({interest_rate:.2f}%)")
                score += 10
            
            # DXY (Dollar Index)
            dxy = macro_data.get('dxy', 0)
            if dxy > 105:
                signal.bearish_reasons.append(f"DXY قوی ({dxy:.2f}) - فشار بر کریپتو")
                score -= 15
            elif dxy < 95:
                signal.bullish_reasons.append(f"DXY ضعیف ({dxy:.2f}) - مساعد برای کریپتو")
                score += 10
            
            # M2 Money Supply
            m2_change = macro_data.get('m2_change', 0)
            if m2_change > 1:
                signal.bullish_reasons.append(f"رشد M2 ({m2_change:+.2f}%) - محیط نقدینگی مثبت")
                score += 10
            elif m2_change < -1:
                signal.bearish_reasons.append(f"کاهش M2 ({m2_change:+.2f}%) - کاهش نقدینگی")
                score -= 10
            
            # CPI/Inflation
            cpi_change = macro_data.get('cpi_change', 0)
            if cpi_change > 3:
                signal.bearish_reasons.append(f"تورم بالا ({cpi_change:+.1f}%)")
                score -= 5
            elif cpi_change < 0:
                signal.bullish_reasons.append(f"تورم پایین ({cpi_change:+.1f}%)")
                score += 5
            
            signal.sentiment_macro = "صعودی" if score > 0 else "نزولی" if score < 0 else "خنثی"
        
        return score
    
    def _calculate_final_signal(
        self,
        signal: TradingSignal,
        tech_score: float,
        fund_score: float,
        macro_score: float
    ):
        """محاسبه سیگنال نهایی"""
        # وزن‌دهی به شاخص‌ها
        # تکنیکال: 50%، فاندامنتال: 25%، کلان: 25%
        total_score = (tech_score * 0.5) + (fund_score * 0.25) + (macro_score * 0.25)
        
        # تعیین جهت سیگنال
        if total_score >= 25:
            signal.direction = SignalDirection.STRONG_BUY
            signal.strength = SignalStrength.VERY_STRONG
        elif total_score >= 10:
            signal.direction = SignalDirection.BUY
            signal.strength = SignalStrength.STRONG
        elif total_score > -10:
            signal.direction = SignalDirection.NEUTRAL
            signal.strength = SignalStrength.MODERATE
        elif total_score > -25:
            signal.direction = SignalDirection.SELL
            signal.strength = SignalStrength.WEAK
        else:
            signal.direction = SignalDirection.STRONG_SELL
            signal.strength = SignalStrength.VERY_WEAK
        
        # محاسبه اعتماد (0-100)
        # میانگین وزنی شاخص‌ها
        tech_conf = 50 + min(tech_score * 1.5, 25) - max(tech_score * 0.5, -25)
        fund_conf = 50 + min(fund_score * 2, 25) - max(fund_score * 1, -25)
        macro_conf = 50 + min(macro_score * 2, 25) - max(macro_score * 1, -25)
        
        signal.confidence = int((tech_conf * 0.5 + fund_conf * 0.25 + macro_conf * 0.25))
        signal.confidence = max(10, min(95, signal.confidence))
    
    def _calculate_trade_levels(self, signal: TradingSignal):
        """محاسبه سطوح معاملاتی"""
        price = signal.current_price
        
        if price <= 0:
            return
        
        # تعیین درصدها بر اساس جهت سیگنال
        if signal.direction in [SignalDirection.BUY, SignalDirection.STRONG_BUY]:
            # سیگنال صعودی
            signal.entry_zone = (price * 0.995, price * 1.01)  # 0.5% زیر تا 1% بالای قیمت
            signal.stop_loss = price * 0.96  # 4% زیر قیمت
            signal.take_profit_1 = price * 1.03  # 3% بالا
            signal.take_profit_2 = price * 1.06  # 6% بالا
            signal.take_profit_3 = price * 1.10  # 10% بالا
            
        elif signal.direction in [SignalDirection.SELL, SignalDirection.STRONG_SELL]:
            # سیگنال نزولی
            signal.entry_zone = (price * 0.99, price * 1.005)  # 1% زیر تا 0.5% بالای قیمت
            signal.stop_loss = price * 1.04  # 4% بالای قیمت
            signal.take_profit_1 = price * 0.97  # 3% پایین
            signal.take_profit_2 = price * 0.94  # 6% پایین
            signal.take_profit_3 = price * 0.90  # 10% پایین
            
        else:
            # سیگنال خنثی - محدوده ورود وسیع‌تر
            signal.entry_zone = (price * 0.98, price * 1.02)
            signal.stop_loss = price * 0.95
            signal.take_profit_1 = price * 1.025
            signal.take_profit_2 = price * 1.05
            signal.take_profit_3 = price * 0.975
        
        # محاسبه نسبت ریسک/پاداش
        if signal.stop_loss > 0:
            risk = abs(signal.stop_loss - signal.entry_zone[1]) / signal.entry_zone[1] * 100
            reward = abs(signal.take_profit_1 - signal.entry_zone[0]) / signal.entry_zone[0] * 100
            if risk > 0:
                signal.risk_reward_ratio = reward / risk
                signal.risk_amount = risk
                signal.reward_amount = reward
        
        # سطوح کلیدی
        signal.key_levels = {
            "current": price,
            "entry_avg": (signal.entry_zone[0] + signal.entry_zone[1]) / 2,
            "stop_loss": signal.stop_loss,
            "tp1": signal.take_profit_1,
            "tp2": signal.take_profit_2,
            "tp3": signal.take_profit_3,
        }
    
    def _generate_market_context(self, signal: TradingSignal):
        """تولید زمینه بازار و چشم‌انداز"""
        # زمینه بازار
        contexts = []
        
        if signal.direction in [SignalDirection.BUY, SignalDirection.STRONG_BUY]:
            contexts.append("🚀 بازار در فاز صعودی")
            if signal.confidence >= 70:
                contexts.append("✅ همه شاخص‌ها همسو هستند")
            else:
                contexts.append("⚠️ برخی شاخص‌ها نیاز به تایید دارند")
        elif signal.direction in [SignalDirection.SELL, SignalDirection.STRONG_SELL]:
            contexts.append("📉 بازار در فاز نزولی")
            if signal.confidence >= 70:
                contexts.append("✅ فشار فروش قوی")
            else:
                contexts.append("⚠️ احتمال بازگشت وجود دارد")
        else:
            contexts.append("⚖️ بازار در فاز تثبیت")
            contexts.append("🔍 نیاز به شکست سطح برای جهت‌گیری")
        
        signal.market_context = " | ".join(contexts)
        
        # چشم‌انداز
        if signal.direction in [SignalDirection.STRONG_BUY, SignalDirection.BUY]:
            if signal.confidence >= 70:
                signal.outlook = "🟢 چشم‌انداز صعودی - فرصت خرید قوی"
            else:
                signal.outlook = "🟡 چشم‌انداز صعودی با احتیاط"
        elif signal.direction in [SignalDirection.STRONG_SELL, SignalDirection.SELL]:
            if signal.confidence >= 70:
                signal.outlook = "🔴 چشم‌انداز نزولی - احتیاط در خرید"
            else:
                signal.outlook = "🟡 چشم‌انداز نزولی -监控 سطح حمایت"
        else:
            signal.outlook = "⚪ چشم‌انداز خنثی - صبر برای سیگنال واضح"
    
    def _create_default_signal(self, symbol: str, price: float, error: str) -> TradingSignal:
        """ایجاد سیگنال پیش‌فرض در صورت خطا"""
        return TradingSignal(
            symbol=symbol,
            current_price=price,
            direction=SignalDirection.NEUTRAL,
            confidence=50,
            market_context=f"❌ خطا در تحلیل: {error}",
            outlook="⚠️ تحلیل با مشکل مواجه شد"
        )
    
    def format_signal_message(self, signal: TradingSignal) -> str:
        """فرمت‌بندی پیام سیگنال"""
        # انتخاب ایموجی بر اساس جهت
        direction_emoji = {
            SignalDirection.STRONG_BUY: "🔴",
            SignalDirection.BUY: "🟢",
            SignalDirection.NEUTRAL: "🟡",
            SignalDirection.SELL: "🔴",
            SignalDirection.STRONG_SELL: "🔴",
        }
        
        emoji = direction_emoji.get(signal.direction, "⚪")
        
        # فرمت‌بندی قیمت‌ها
        def fmt_price(p: float) -> str:
            if p >= 1000:
                return f"${p:,.0f}"
            elif p >= 1:
                return f"${p:,.2f}"
            else:
                return f"${p:,.4f}"
        
        # فرمت‌بندی درصد
        def fmt_pct(p: float) -> str:
            return f"{p:+.2f}%"
        
        # ساخت پیام
        message = f"""
{emoji} **{signal.direction.value.split()[1]} - {signal.symbol}**

{'─' * 40}

🎯 **وضعیت سیگنال:**
📊 **قدرت:** {"⭐" * signal.strength.value}
📈 **اعتماد:** {signal.confidence}%
⚖️ **نسبت R/R:** 1:{signal.risk_reward_ratio:.1f}

💰 **قیمت فعلی:** {fmt_price(signal.current_price)}

{'─' * 40}

📋 **سطوح معاملاتی:**

🔵 **محدوده ورود:**
   {fmt_price(signal.entry_zone[0])} - {fmt_price(signal.entry_zone[1])}

🔴 **حد ضرر (SL):**
   {fmt_price(signal.stop_loss)}

🟢 **اهداف قیمتی:**
   TP1: {fmt_price(signal.take_profit_1)} ({fmt_pct((signal.take_profit_1/signal.current_price-1)*100)})
   TP2: {fmt_price(signal.take_profit_2)} ({fmt_pct((signal.take_profit_2/signal.current_price-1)*100)})
   TP3: {fmt_price(signal.take_profit_3)} ({fmt_pct((signal.take_profit_3/signal.current_price-1)*100)})

{'─' * 40}

📊 **تحلیل شاخص‌ها:**

🏦 **کلان:** {signal.sentiment_macro}
💎 **فاندامنتال:** {signal.sentiment_fundamental}
📈 **تکنیکال:** {signal.sentiment_technical}

{'─' * 40}

💡 **زمینه بازار:**
{signal.market_context}

🎯 **چشم‌انداز:**
{signal.outlook}

{'─' * 40}

📝 **دلایل سیگنال:**

**صعودی ({len(signal.bullish_reasons)}):**
{chr(10).join([f"   • {r}" for r in signal.bullish_reasons[:5]]) if signal.bullish_reasons else "   • ندارد"}

**نزولی ({len(signal.bearish_reasons)}):**
{chr(10).join([f"   • {r}" for r in signal.bearish_reasons[:5]]) if signal.bearish_reasons else "   • ندارد"}

{'─' * 40}

🕐 به‌روزرسانی: {signal.timestamp}

⚠️ **هشدار:** این سیگنال صرفاً جنبه اطلاعاتی دارد.
همیشه مدیریت ریسک را رعایت کنید.
        """
        
        return message.strip()
    
    def format_short_signal(self, signal: TradingSignal) -> str:
        """فرمت‌بندی سیگنال کوتاه"""
        def fmt_price(p: float) -> str:
            if p >= 1000:
                return f"${p:,.0f}"
            else:
                return f"${p:,.2f}"
        
        emoji = "🟢" if signal.direction in [SignalDirection.BUY, SignalDirection.STRONG_BUY] else \
                "🔴" if signal.direction in [SignalDirection.SELL, SignalDirection.STRONG_SELL] else "🟡"
        
        direction_text = signal.direction.value.split()[1]
        
        return f"""
{emoji} **{signal.symbol} Signal**

🎯 {direction_text} | 📊 {signal.confidence}% اعتماد
💰 قیمت: {fmt_price(signal.current_price)}

📋 Entry: {fmt_price(signal.entry_zone[0])}-{fmt_price(signal.entry_zone[1])}
🔴 SL: {fmt_price(signal.stop_loss)}
🟢 TP: {fmt_price(signal.take_profit_1)}/TP2/TP3

⚖️ R/R: 1:{signal.risk_reward_ratio:.1f}
{signal.outlook}
        """.strip()


# نمونه واحد (Singleton)
signal_generator = SignalGenerator()

# لیست خروجی
__all__ = [
    'SignalDirection',
    'SignalStrength', 
    'TradingSignal',
    'SignalGenerator',
    'signal_generator'
]


# ═══════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    
    # تنظیم لاگینگ
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("📊 تست ماژول Signal Generator")
    print("=" * 60)
    
    generator = SignalGenerator()
    
    # تست با داده‌های نمونه
    smc_data = {
        'bias': 'BULLISH',
        'confidence': 75,
        'swing_points': 30,
        'fvgs': 45
    }
    
    macro_data = {
        'interest_rate': 4.25,
        'dxy': 103.5,
        'm2_change': 0.5,
        'cpi_change': 2.8
    }
    
    fund_data = {
        'market_cap': 260e9,
        'tvl': 112e9,
        'market_cap_change_24h': 1.5
    }
    
    # تولید سیگنال
    signal = generator.generate_signal(
        symbol="ETH",
        current_price=2150.0,
        smc_result=smc_data,
        macro_data=macro_data,
        fundamental_data=fund_data
    )
    
    # نمایش سیگنال
    print(f"\n📊 سیگنال تولید شده:")
    print(f"   نماد: {signal.symbol}")
    print(f"   جهت: {signal.direction.value}")
    print(f"   اعتماد: {signal.confidence}%")
    print(f"   R/R: 1:{signal.risk_reward_ratio:.2f}")
    
    print("\n" + "=" * 60)
    print("📝 پیام کامل سیگنال:")
    print("=" * 60)
    print(generator.format_signal_message(signal))
