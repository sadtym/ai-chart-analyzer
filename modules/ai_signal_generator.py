# -*- coding: utf-8 -*-
"""
ماژول سیگنال‌دهی هوشمند با AI
AI-Powered Smart Signal Generator

این ماژول با استفاده از Google Gemini سیگنال‌های معاملاتی هوشمند تولید می‌کند
که ترکیبی از تحلیل‌های تکنیکال، فاندامنتال و کلان است.

قابلیت‌ها:
- تولید سیگنال با Gemini AI
- محاسبه سطوح معاملاتی هوشمند
- ارزیابی ریسک و پاداش
- ارائه دلایل منطقی برای سیگنال
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# ═══════════════════════════════════════════════════════
# 📦 وارد کردن وابستگی‌ها
# ═══════════════════════════════════════════════════════

try:
    from config import GEMINI_API_KEY, GEMINI_MODEL
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GEMINI_MODEL = "gemini-1.5-flash"

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
    
    # دلایل سیگنال (تولید شده توسط AI)
    ai_reasoning: str = ""
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
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")


class AISignalGenerator:
    """
    تولیدکننده سیگنال معاملاتی هوشمند با AI
    
    این کلاس از Google Gemini برای تولید سیگنال‌های معاملاتی استفاده می‌کند
    که ترکیبی از تحلیل‌های تکنیکال، فاندامنتال و کلان است.
    """
    
    def __init__(self):
        """راه‌اندازی تولیدکننده سیگنال AI"""
        self.model = None
        self.gemini_available = False
        
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                self.model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    system_instruction="تو یک تحلیلگر حرفه‌ای و معامله‌گر با تجربه بازارهای مالی هستی. تحلیل‌هایت دقیق، مختصر و عملیاتی هستند. همیشه ریسک را مدیریت کن و هشدارهای لازم را بده."
                )
                self.gemini_available = True
                logger.info("✅ Gemini AI برای سیگنال‌دهی فعال شد")
            except Exception as e:
                logger.error(f"❌ خطا در راه‌اندازی Gemini: {e}")
        else:
            logger.warning("⚠️ Gemini در دسترس نیست - استفاده از حالت محلی")
    
    async def generate_ai_signal(
        self,
        symbol: str,
        current_price: float,
        smc_result: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        fundamental_data: Optional[Dict] = None
    ) -> TradingSignal:
        """
        تولید سیگنال معاملاتی هوشمند با AI
        
        Args:
            symbol: نماد معاملاتی
            current_price: قیمت فعلی
            smc_result: نتیجه تحلیل SMC
            macro_data: داده‌های کلان اقتصادی
            fundamental_data: داده‌های فاندامنتال
        
        Returns:
            TradingSignal: سیگنال معاملاتی هوشمند
        """
        try:
            signal = TradingSignal(
                symbol=symbol,
                current_price=current_price
            )
            
            # ═══════════════════════════════════════════════════════
            # مرحله 1: اگر Gemini در دسترس است، از AI استفاده کن
            # ═══════════════════════════════════════════════════════
            
            if self.gemini_available and self.model:
                return await self._generate_with_gemini(
                    signal, symbol, current_price, smc_result, macro_data, fundamental_data
                )
            else:
                # ═══════════════════════════════════════════════════════
                # مرحله 2: حالت محلی (fallback)
                # ═══════════════════════════════════════════════════════
                return self._generate_local_fallback(
                    signal, symbol, current_price, smc_result, macro_data, fundamental_data
                )
                
        except Exception as e:
            logger.error(f"❌ خطا در تولید سیگنال AI: {e}")
            return self._create_default_signal(symbol, current_price, str(e))
    
    async def _generate_with_gemini(
        self,
        signal: TradingSignal,
        symbol: str,
        current_price: float,
        smc_result: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        fundamental_data: Optional[Dict] = None
    ) -> TradingSignal:
        """تولید سیگنال با استفاده از Gemini AI"""
        
        # ساخت پرامپت جامع برای AI
        prompt = self._build_signal_prompt(
            symbol, current_price, smc_result, macro_data, fundamental_data
        )
        
        try:
            # ارسال به Gemini
            response = self.model.generate_content(prompt)
            content = response.text.strip()
            
            # حذف علامت‌های markdown
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # پارس JSON
            ai_data = json.loads(content)
            
            # پر کردن سیگنال از داده‌های AI
            signal = self._parse_ai_response(signal, ai_data, current_price)
            
            logger.info(f"✅ سیگنال AI تولید شد: {symbol} - {signal.direction.value}")
            return signal
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ خطا در پارس JSON سیگنال: {e}")
            logger.error(f"پاسخ Gemini: {content[:500]}")
            # fallback به حالت محلی
            return self._generate_local_fallback(
                signal, symbol, current_price, smc_result, macro_data, fundamental_data
            )
        
        except Exception as e:
            logger.error(f"❌ خطا در تولید سیگنال Gemini: {e}")
            return self._generate_local_fallback(
                signal, symbol, current_price, smc_result, macro_data, fundamental_data
            )
    
    def _build_signal_prompt(
        self,
        symbol: str,
        current_price: float,
        smc_result: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        fundamental_data: Optional[Dict] = None
    ) -> str:
        """ساخت پرامپت جامع برای تولید سیگنال با قوانین دقیق R/R"""
        
        # ═══════════════════════════════════════════════════════════
        # 📊 تشخیص دارایی پرنوسان
        # ═══════════════════════════════════════════════════════════
        is_volatile = False
        volatility_level = ""
        volatility_note = ""
        
        if fundamental_data:
            mcap_change = abs(fundamental_data.get('market_cap_change_24h', 0))
            is_volatile = mcap_change > 8.0
            
            if is_volatile:
                volatility_level = f"""
⚡ **⚠️ هشدار: دارایی پرنوسان ({symbol})!**
تغییر 24 ساعته: {mcap_change:+.2f}%
"""
                volatility_note = """
برای دارایی‌های پرنوسان:
- SL را 4-6% از ورود بگذار
- TP1 را 3-5% از ورود بگذار
- R/R حداقل 1:1.2 برایشان کافی است
"""
        
        # ═══════════════════════════════════════════════════════════
        # 📈 داده‌های تکنیکال (SMC)
        # ═══════════════════════════════════════════════════════════
        tech_info = ""
        if smc_result:
            bias = smc_result.get('bias', 'NEUTRAL')
            confidence = smc_result.get('confidence', 0)
            swing_points = smc_result.get('swing_points', 0)
            fvgs = smc_result.get('fvgs', 0)
            tech_info = f"""
📈 **تحلیل تکنیکال (SMC):**
- بایاس: {bias}
- اعتماد: {confidence}%
- نقاط سوئینگ: {swing_points}
- FVGs: {fvgs}
"""
        
        # ═══════════════════════════════════════════════════════════
        # 💎 داده‌های فاندامنتال
        # ═══════════════════════════════════════════════════════════
        fund_info = ""
        if fundamental_data:
            mcap = fundamental_data.get('market_cap', 0)
            tvl = fundamental_data.get('tvl', 0)
            mcap_change = fundamental_data.get('market_cap_change_24h', 0)
            fund_info = f"""
💎 **تحلیل فاندامنتال:**
- ارزش بازار: ${mcap/1e9:.1f}B
- TVL: ${tvl/1e9:.1f}B
- تغییر 24h: {mcap_change:+.2f}%
"""
        
        # ═══════════════════════════════════════════════════════════
        # 🏦 داده‌های کلان اقتصادی
        # ═══════════════════════════════════════════════════════════
        macro_info = ""
        dxy_weight = ""
        if macro_data:
            interest = macro_data.get('interest_rate', 0)
            dxy = macro_data.get('dxy', 0)
            m2_change = macro_data.get('m2_change', 0)
            cpi_change = macro_data.get('cpi_change', 0)
            macro_info = f"""
🏦 **تحلیل کلان اقتصادی:**
- نرخ بهره فدرال رزرو: {interest:.2f}%
- شاخص دلار (DXY): {dxy:.2f}
- تغییر M2: {m2_change:+.2f}%
- تورم (CPI): {cpi_change:+.2f}%
"""
            
            # وزن‌دهی DXY
            if dxy > 115:
                dxy_weight = "DXY بالای 115 → فشار شدید نزولی روی کریپتو"
            elif dxy < 100:
                dxy_weight = "DXY زیر 100 → محیط مساعد برای ریسک"
            else:
                dxy_weight = "DXY بین 100-115 → خنثی"
        
        # ═══════════════════════════════════════════════════════════
        # 🎯 پرامپت نهایی با قوانین دقیق R/R
        # ═══════════════════════════════════════════════════════════
        
        prompt = f"""
📊 **تحلیل جامع و سیگنال معاملاتی برای {symbol}**
💰 قیمت فعلی: ${current_price:,.2f}

{tech_info}
{fund_info}
{volatility_level}
{macro_info}
- **وزن DXY:** {dxy_weight}

═══════════════════════════════════════════════════════════
🔴 **قوانین حیاتی محاسبه نسبت ریسک/پاداش (R/R)**
═══════════════════════════════════════════════════════════

**تعریف:**
- ریسک = |ورود - SL| (فاصله از ورود تا حد ضرر)
- پاداش = |TP1 - ورود| (فاصله از ورود تا اولین هدف)
- R/R = پاداش / ریسک

**قانون اصلی:**
⚠️ حداقل R/R باید 1:1.5 باشد!
اگر نمی‌توانی R/R مناسب بسازی → سیگنال را NEUTRAL بده

═══════════════════════════════════════════════════════════
🟢 **قوانین سیگنال BUY (خرید)**
═══════════════════════════════════════════════════════════

**ورود:**
- محدوده ورود: current_price - 2% تا current_price + 0.5%
- یعنی: ${current_price * 0.98:,.2f} - ${current_price * 1.005:,.2f}
- نکته: ورود باید کمتر یا نزدیک قیمت فعلی باشد!

**حد ضرر (SL):**
- زیر ورود قرار می‌گیرد
- حداکثر 2-4% پایین‌تر از ورود
- ریسک نباید بیشتر از 4% باشد!

**TP1 (هدف اول):**
- بالای ورود قرار می‌گیرد
- باید حداقل 1.5 برابر ریسک باشد
- یعنی اگر ریسک 2% است، TP1 باید 3%+ بالاتر از ورود باشد

**مثال صحیح BUY در قیمت $100:**
- ورود: $98 - $101
- SL: $95 (ریسک = 3%)
- TP1: $100.5 (پاداش = 1.5%) → R/R = 1:0.5 ❌ اشتباه!
- TP1: $105 (پاداش = 5%) → R/R = 1:1.67 ✅ درست!

═══════════════════════════════════════════════════════════
🔴 **قوانین سیگنال SELL (فروش)**
═══════════════════════════════════════════════════════════

**ورود:**
- محدوده ورود: current_price - 0.5% تا current_price + 2%
- یعنی: ${current_price * 0.995:,.2f} - ${current_price * 1.02:,.2f}
- نکته: ورود باید بالاتر یا نزدیک قیمت فعلی باشد!

**حد ضرر (SL):**
- بالای ورود قرار می‌گیرد
- حداکثر 2-4% بالاتر از ورود
- ریسک نباید بیشتر از 4% باشد!

**TP1 (هدف اول):**
- زیر ورود قرار می‌گیرد
- باید حداقل 1.5 برابر ریسک باشد
- یعنی اگر ریسک 2% است، TP1 باید 3%+ پایین‌تر از ورود باشد

**مثال صحیح SELL در قیمت $100:**
- ورود: $99 - $102
- SL: $105 (ریسک = 3%)
- TP1: $98 (پاداش = 1%) → R/R = 1:0.33 ❌ اشتباه!
- TP1: $93 (پاداش = 6%) → R/R = 1:2 ✅ درست!

═══════════════════════════════════════════════════════════
❌ **اشتباهات رایج که باید اجتناب کنی**
═══════════════════════════════════════════════════════════

1. **ورود بسیار دور از قیمت فعلی:**
   - ❌ ورود: $110 در حالیکه قیمت فعلی $100 است
   - ✅ ورود: $99-$102 برای SELL، $98-$101 برای BUY

2. **TP1 خیلی نزدیک به ورود:**
   - ❌ ریسک 3% و پاداش 1% → R/R = 1:0.33
   - ✅ ریسک 3% و پاداش 5% → R/R = 1:1.67

3. **TP1 خیلی دور از ورود (غیر واقعی):**
   - ❌ TP1: $150 وقتی ریسک فقط 2% است
   - ✅ TP1 واقع‌بینانه: حداکثر 3-5 برابر ریسک

4. **فراموش کردن جهت سیگنال:**
   - برای BUY: SL < ورود < TP1
   - برای SELL: TP1 < ورود < SL

{volatility_note}

═══════════════════════════════════════════════════════════
📊 **چک‌لیست قبل از ارسال سیگنال**
═══════════════════════════════════════════════════════════

✅ آیا R/R >= 1.5 است؟
✅ آیا ورود نزدیک قیمت فعلی است (±2%)؟
✅ آیا ریسک <= 4% است؟
✅ آیا TP1 واقع‌بینانه است؟
✅ آیا جهت سطوح درست است (BUY: SL<ورود<TP1)؟
✅ آیا سیگنال با تغییر 24h همخوانی دارد؟

═══════════════════════════════════════════════════════════
📝 **فرمت پاسخ (فقط JSON):**
═══════════════════════════════════════════════════════════

```json
{{
    "signal": "BUY",
    "confidence": 75,
    "entry_low": 98.0,
    "entry_high": 101.0,
    "stop_loss": 95.0,
    "take_profit_1": 105.0,
    "take_profit_2": 110.0,
    "take_profit_3": 115.0,
    "bullish_reasons": ["دلیل 1", "دلیل 2"],
    "bearish_reasons": ["دلیل 1"],
    "market_context": "توضیح وضعیت بازار",
    "outlook": "چشم‌انداز آینده"
}}
```

⚠️ **هشدار مهم:**
- بیش از 1-2% سرمایه را در هر معامله ریسک نکن
- این سیگنال فقط جنبه اطلاعاتی دارد

⚡ فقط JSON برگردان، هیچ توضیح اضافی نده!
"""
        
        return prompt
    
    def _parse_ai_response(
        self,
        signal: TradingSignal,
        ai_data: Dict[str, Any],
        current_price: float
    ) -> TradingSignal:
        """پارس کردن پاسخ AI و پر کردن سیگنال"""
        
        # جهت سیگنال
        signal_str = ai_data.get('signal', 'NEUTRAL').upper()
        if signal_str == 'STRONG_BUY':
            signal.direction = SignalDirection.STRONG_BUY
            signal.strength = SignalStrength.VERY_STRONG
        elif signal_str == 'BUY':
            signal.direction = SignalDirection.BUY
            signal.strength = SignalStrength.STRONG
        elif signal_str == 'SELL':
            signal.direction = SignalDirection.SELL
            signal.strength = SignalStrength.WEAK
        elif signal_str == 'STRONG_SELL':
            signal.direction = SignalDirection.STRONG_SELL
            signal.strength = SignalStrength.VERY_WEAK
        else:
            signal.direction = SignalDirection.NEUTRAL
            signal.strength = SignalStrength.MODERATE
        
        # اعتماد
        signal.confidence = ai_data.get('confidence', 50)
        signal.confidence = max(10, min(95, signal.confidence))
        
        # سطوح معاملاتی
        signal.entry_zone = (
            ai_data.get('entry_low', current_price * 0.99),
            ai_data.get('entry_high', current_price * 1.01)
        )
        signal.stop_loss = ai_data.get('stop_loss', current_price * 0.96)
        signal.take_profit_1 = ai_data.get('take_profit_1', current_price * 1.03)
        signal.take_profit_2 = ai_data.get('take_profit_2', current_price * 1.06)
        signal.take_profit_3 = ai_data.get('take_profit_3', current_price * 1.10)
        
        # دلایل
        signal.bullish_reasons = ai_data.get('bullish_reasons', [])
        signal.bearish_reasons = ai_data.get('bearish_reasons', [])
        signal.neutral_reasons = ai_data.get('neutral_reasons', [])
        
        # زمینه و چشم‌انداز
        signal.market_context = ai_data.get('market_context', '')
        signal.outlook = ai_data.get('outlook', '')
        
        # محاسبه نسبت ریسک/پاداش
        entry_avg = (signal.entry_zone[0] + signal.entry_zone[1]) / 2
        if signal.stop_loss > 0 and entry_avg > 0:
            risk = abs(signal.stop_loss - entry_avg) / entry_avg * 100
            reward = abs(signal.take_profit_1 - entry_avg) / entry_avg * 100
            if risk > 0:
                signal.risk_reward_ratio = reward / risk
                signal.risk_amount = risk
                signal.reward_amount = reward
        
        # سطوح کلیدی
        signal.key_levels = {
            "current": current_price,
            "entry_avg": entry_avg,
            "stop_loss": signal.stop_loss,
            "tp1": signal.take_profit_1,
            "tp2": signal.take_profit_2,
            "tp3": signal.take_profit_3,
        }
        
        return signal
    
    def _generate_local_fallback(
        self,
        signal: TradingSignal,
        symbol: str,
        current_price: float,
        smc_result: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        fundamental_data: Optional[Dict] = None
    ) -> TradingSignal:
        """تولید سیگنال در حالت محلی (fallback)"""
        
        # محاسبه امتیاز
        score = 0
        
        # تحلیل تکنیکال
        if smc_result:
            bias = smc_result.get('bias', 'NEUTRAL').upper()
            confidence = smc_result.get('confidence', 50)
            signal.sentiment_technical = bias
            
            if 'BULLISH' in bias:
                score += 30
                signal.bullish_reasons.append(f"ساختار تکنیکال صعودی ({bias})")
            elif 'BEARISH' in bias:
                score -= 30
                signal.bearish_reasons.append(f"ساختار تکنیکال نزولی ({bias})")
            else:
                signal.neutral_reasons.append("ساختار تکنیکال خنثی")
            
            if confidence >= 80:
                score += 20
            elif confidence < 30:
                score -= 10
        
        # تحلیل فاندامنتال
        if fundamental_data:
            tvl = fundamental_data.get('tvl', 0)
            signal.tvl = tvl
            if tvl > 1e11:
                score += 15
                signal.bullish_reasons.append(f"TVL بسیار قوی (${tvl/1e9:.1f}B)")
            elif tvl > 1e10:
                score += 10
                signal.bullish_reasons.append(f"TVL مناسب (${tvl/1e9:.1f}B)")
        
        # تحلیل کلان
        if macro_data:
            dxy = macro_data.get('dxy', 0)
            if dxy > 105:
                score -= 15
                signal.bearish_reasons.append(f"DXY قوی ({dxy:.2f}) - فشار بر کریپتو")
            elif dxy < 95:
                score += 10
                signal.bullish_reasons.append(f"DXY ضعیف ({dxy:.2f}) - مساعد برای کریپتو")
        
        # تعیین جهت
        if score >= 25:
            signal.direction = SignalDirection.STRONG_BUY
            signal.strength = SignalStrength.VERY_STRONG
        elif score >= 10:
            signal.direction = SignalDirection.BUY
            signal.strength = SignalStrength.STRONG
        elif score > -10:
            signal.direction = SignalDirection.NEUTRAL
            signal.strength = SignalStrength.MODERATE
        elif score > -25:
            signal.direction = SignalDirection.SELL
            signal.strength = SignalStrength.WEAK
        else:
            signal.direction = SignalDirection.STRONG_SELL
            signal.strength = SignalStrength.VERY_WEAK
        
        signal.confidence = max(30, min(80, 50 + score))
        
        # سطوح معاملاتی
        if signal.direction in [SignalDirection.BUY, SignalDirection.STRONG_BUY]:
            signal.entry_zone = (current_price * 0.995, current_price * 1.01)
            signal.stop_loss = current_price * 0.96
            signal.take_profit_1 = current_price * 1.03
            signal.take_profit_2 = current_price * 1.06
            signal.take_profit_3 = current_price * 1.10
        elif signal.direction in [SignalDirection.SELL, SignalDirection.STRONG_SELL]:
            signal.entry_zone = (current_price * 0.99, current_price * 1.005)
            signal.stop_loss = current_price * 1.04
            signal.take_profit_1 = current_price * 0.97
            signal.take_profit_2 = current_price * 0.94
            signal.take_profit_3 = current_price * 0.90
        else:
            signal.entry_zone = (current_price * 0.98, current_price * 1.02)
            signal.stop_loss = current_price * 0.95
            signal.take_profit_1 = current_price * 1.025
            signal.take_profit_2 = current_price * 1.05
            signal.take_profit_3 = current_price * 0.975
        
        # نسبت R/R
        entry_avg = (signal.entry_zone[0] + signal.entry_zone[1]) / 2
        risk = abs(signal.stop_loss - entry_avg) / entry_avg * 100
        reward = abs(signal.take_profit_1 - entry_avg) / entry_avg * 100
        if risk > 0:
            signal.risk_reward_ratio = reward / risk
            signal.risk_amount = risk
            signal.reward_amount = reward
        
        signal.key_levels = {
            "current": current_price,
            "entry_avg": entry_avg,
            "stop_loss": signal.stop_loss,
            "tp1": signal.take_profit_1,
            "tp2": signal.take_profit_2,
            "tp3": signal.take_profit_3,
        }
        
        signal.market_context = "📊 تحلیل محلی (GEMINI در دسترس نیست)"
        signal.outlook = f"🟡 امتیاز کلی: {score}"
        
        return signal
    
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
   {fmt_price(signal.stop_loss)} ({fmt_pct((signal.stop_loss/signal.current_price-1)*100)})

🟢 **اهداف قیمتی:**
   TP1: {fmt_price(signal.take_profit_1)} ({fmt_pct((signal.take_profit_1/signal.current_price-1)*100)})
   TP2: {fmt_price(signal.take_profit_2)} ({fmt_pct((signal.take_profit_2/signal.current_price-1)*100)})
   TP3: {fmt_price(signal.take_profit_3)} ({fmt_pct((signal.take_profit_3/signal.current_price-1)*100)})

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


# نمونه واحد (Singleton)
ai_signal_generator = AISignalGenerator()

# لیست خروجی
__all__ = [
    'SignalDirection',
    'SignalStrength', 
    'TradingSignal',
    'AISignalGenerator',
    'ai_signal_generator'
]


# ═══════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    
    # تنظیم لاگینگ
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("📊 تست ماژول AI Signal Generator")
    print("=" * 60)
    
    generator = AISignalGenerator()
    
    # داده‌های نمونه
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
    
    async def test():
        # تولید سیگنال
        signal = await generator.generate_ai_signal(
            symbol="ETH",
            current_price=2150.0,
            smc_result=smc_data,
            macro_data=macro_data,
            fundamental_data=fund_data
        )
        
        print(f"\n📊 سیگنال تولید شده:")
        print(f"   نماد: {signal.symbol}")
        print(f"   جهت: {signal.direction.value}")
        print(f"   اعتماد: {signal.confidence}%")
        print(f"   R/R: 1:{signal.risk_reward_ratio:.2f}")
        
        print("\n" + "=" * 60)
        print("📝 پیام کامل سیگنال:")
        print("=" * 60)
        print(generator.format_signal_message(signal))
    
    # اجرای تست
    asyncio.run(test())
