# -*- coding: utf-8 -*-
"""
ماژول تحلیل هوشمند ترکیبی با هوش مصنوعی
Smart AI Integration Module

این ماژول تمام داده‌های کلان، فاندامنتال و تکنیکال را با AI ترکیب می‌کند
و سیگنال‌های معاملاتی هوشمند ارائه می‌دهد.

قابلیت‌ها:
- تحلیل همزمان چندین منبع داده
- تولید سیگنال معاملاتی هوشمند
- ارزیابی ریسک و پاداش
- خلاصه‌سازی شرایط بازار
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 📦 وارد کردن وابستگی‌ها
# ═══════════════════════════════════════════════════════════════

try:
    from config import GEMINI_API_KEY, GEMINI_MODEL, AI_PROVIDER
    from modules.fundamental_data import (
        FundamentalDataManager, MacroData, CryptoFundamentals, FullAnalysisData
    )
except ImportError as e:
    logger.warning(f"⚠️ خطا در وارد کردن ماژول‌ها: {e}")
    # حالت تست
    GEMINI_API_KEY = None
    GEMINI_MODEL = "gemini-1.5-flash"
    AI_PROVIDER = "gemini"


# ═══════════════════════════════════════════════════════════════
# 📊 Data Classes
# ═══════════════════════════════════════════════════════════════

class SignalType(Enum):
    """انواع سیگنال معاملاتی"""
    STRONG_BUY = "🟢 خرید قوی"
    BUY = "🟢 خرید"
    NEUTRAL = "🟡 خنثی"
    SELL = "🔴 فروش"
    STRONG_SELL = "🔴 فروش قوی"


class RiskLevel(Enum):
    """سطوح ریسک"""
    LOW = "کم"
    MEDIUM = "متوسط"
    HIGH = "بالا"
    VERY_HIGH = "بسیار بالا"


@dataclass
class CombinedAnalysisResult:
    """نتیجه تحلیل ترکیبی"""
    symbol: str = ""
    signal: SignalType = SignalType.NEUTRAL
    confidence: int = 50
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_reward_ratio: float = 0.0
    
    # داده‌های تحلیل
    macro_sentiment: str = ""
    fundamental_sentiment: str = ""
    technical_sentiment: str = ""
    ai_sentiment: str = ""
    
    # امتیاز همگرایی
    confluence_score: int = 50
    
    # توضیحات AI
    ai_summary: str = ""
    trading_recommendation: str = ""
    risk_warning: str = ""
    
    # فاکتورهای همگرایی
    bullish_factors: list = field(default_factory=list)
    bearish_factors: list = field(default_factory=list)
    neutral_factors: list = field(default_factory=list)
    
    # اطلاعات تکمیلی
    current_price: float = 0.0
    market_cap: float = 0.0
    tvl: float = 0.0
    interest_rate: float = 0.0
    dxy: float = 0.0


# ═══════════════════════════════════════════════════════════════
# 🧠 کلاس تحلیلگر ترکیبی AI
# ═══════════════════════════════════════════════════════════════

class AIIntegratedAnalyzer:
    """
    تحلیلگر هوشمند ترکیبی
    
    این کلاس تمام منابع داده را ترکیب کرده و با استفاده از AI
    تحلیل جامعی ارائه می‌دهد.
    """
    
    def __init__(self):
        """راه‌اندازی تحلیلگر ترکیبی"""
        self.fundamental_manager = FundamentalDataManager()
        self.gemini_client = None
        self.model = GEMINI_MODEL
        
        # تنظیم Gemini
        if GEMINI_API_KEY:
            self._init_gemini()
        
        logger.info("✅ تحلیلگر ترکیبی AI راه‌اندازی شد")
    
    def _init_gemini(self):
        """راه‌اندازی Google Gemini"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_client = genai
            logger.info(f"✅ Gemini برای تحلیل ترکیبی تنظیم شد: {self.model}")
        except ImportError:
            logger.warning("⚠️ کتابخانه google-generativeai نصب نیست")
            self.gemini_client = None
    
    async def analyze_combined(
        self,
        symbol: str,
        smc_result: Optional[Dict] = None,
        current_price: float = 0.0
    ) -> CombinedAnalysisResult:
        """
        تحلیل ترکیبی کامل
        
        Args:
            symbol: نماد معاملاتی
            smc_result: نتیجه تحلیل SMC (اختیاری)
            current_price: قیمت فعلی
        
        Returns:
            CombinedAnalysisResult: نتیجه تحلیل ترکیبی
        """
        try:
            logger.info(f"🚀 شروع تحلیل ترکیبی برای {symbol}")
            
            # مرحله 1: دریافت داده‌های فاندامنتال و کلان
            full_data = await self.fundamental_manager.get_full_analysis(
                symbol=symbol,
                smc_results=smc_result if smc_result else {},
                current_price=current_price
            )
            
            # مرحله 2: تحلیل محلی (Local Analysis)
            local_result = self._local_analysis(full_data, smc_result)
            
            # مرحله 3: تحلیل با AI (در صورت موجود بودن)
            if self.gemini_client:
                ai_result = await self._ai_analysis(local_result, full_data, smc_result)
                # ترکیب نتایج محلی و AI
                final_result = self._merge_results(local_result, ai_result)
            else:
                final_result = local_result
            
            logger.info(f"✅ تحلیل ترکیبی {symbol}: سیگنال={final_result.signal.value}")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ خطا در تحلیل ترکیبی: {e}")
            return self._create_default_result(symbol, str(e))
    
    def _local_analysis(
        self,
        full_data: FullAnalysisData,
        smc_result: Optional[Dict]
    ) -> CombinedAnalysisResult:
        """
        تحلیل محلی بدون نیاز به AI
        ترکیب تمام شاخص‌ها برای تولید سیگنال
        """
        result = CombinedAnalysisResult(symbol=full_data.symbol)
        result.current_price = full_data.current_price
        
        # ═══════════════════════════════════════════════════════
        # 🎯 تحلیل کلان اقتصادی
        # ═══════════════════════════════════════════════════════
        
        if full_data.macro:
            macro_sentiment, macro_desc = full_data.macro.get_sentiment()
            result.macro_sentiment = macro_sentiment
            result.interest_rate = full_data.macro.interest_rate
            result.dxy = full_data.macro.dxy
            
            # فاکتورهای کلان
            if full_data.macro.interest_rate > 4.5:
                result.bearish_factors.append("نرخ بهره بالا (>4.5%)")
            elif full_data.macro.interest_rate < 3.0:
                result.bullish_factors.append("نرخ بهره پایین (<3.0%)")
            
            if full_data.macro.dxy > 105:
                result.bearish_factors.append("DXY قوی (>105) - فشار بر کریپتو")
            elif full_data.macro.dxy < 95:
                result.bullish_factors.append("DXY ضعیف (<95) - مساعد برای کریپتو")
            
            if full_data.macro.m2_change > 1:
                result.bullish_factors.append("رشد M2 (+1%) - محیط نقدینگی مثبت")
            elif full_data.macro.m2_change < -1:
                result.bearish_factors.append("کاهش M2 (-1%) - کاهش نقدینگی")
        
        # ═══════════════════════════════════════════════════════
        # 💎 تحلیل فاندامنتال
        # ═══════════════════════════════════════════════════════
        
        if full_data.crypto_fundamentals:
            fund = full_data.crypto_fundamentals
            result.fundamental_sentiment = fund.get_market_sentiment()
            result.market_cap = fund.market_cap
            result.tvl = fund.tvl
            
            # فاکتورهای فاندامنتال
            if fund.tvl > 0:
                if fund.tvl > 1e11:  # > 100B
                    result.bullish_factors.append(f"TVL قوی (${fund.tvl/1e9:.1f}B)")
                elif fund.tvl > 1e10:  # > 10B
                    result.bullish_factors.append(f"TVL مناسب (${fund.tvl/1e9:.1f}B)")
            
            if fund.defi_tvl > fund.market_cap * 0.5:
                result.bullish_factors.append("DeFi TVL بالا نسبت به Market Cap")
            
            # نرخ‌های وام‌دهی
            lending_rates = fund.lending_rates or {}
            for protocol, rate in lending_rates.items():
                if 'USDC' in protocol and rate > 5:
                    result.bearish_factors.append(f"نرخ وام‌دهی {protocol} بالا ({rate:.1f}%)")
        
        # ═══════════════════════════════════════════════════════
        # 📈 تحلیل تکنیکال (SMC)
        # ═══════════════════════════════════════════════════════
        
        if smc_result:
            bias = smc_result.get('bias', 'NEUTRAL').upper()
            result.technical_sentiment = bias
            
            if bias in ['BULLISH', 'STRONG_BULLISH']:
                result.bullish_factors.append("ساختار تکنیکال صعودی (SMC)")
            elif bias in ['BEARISH', 'STRONG_BEARISH']:
                result.bearish_factors.append("ساختار تکنیکال نزولی (SMC)")
            
            # اعتماد تکنیکال
            confidence = smc_result.get('confidence', 50)
            if confidence > 70:
                result.bullish_factors.append(f"اعتماد تکنیکال بالا ({confidence}%)")
            elif confidence < 30:
                result.bearish_factors.append(f"اعتماد تکنیکال پایین ({confidence}%)")
        
        # ═══════════════════════════════════════════════════════
        # 🎯 محاسبه سیگنال نهایی
        # ═══════════════════════════════════════════════════════
        
        score = 0
        
        # امتیاز کلان
        if result.macro_sentiment == "صعودی":
            score += 15
        elif result.macro_sentiment == "نزولی":
            score -= 15
        
        # امتیاز فاندامنتال
        if result.fundamental_sentiment == "صعودی":
            score += 15
        elif result.fundamental_sentiment == "نزولی":
            score -= 15
        
        # امتیاز تکنیکال
        if result.technical_sentiment in ['BULLISH', 'STRONG_BULLISH']:
            score += 25
        elif result.technical_sentiment in ['BEARISH', 'STRONG_BEARISH']:
            score -= 25
        
        # تنظیم سیگنال
        if score >= 40:
            result.signal = SignalType.STRONG_BUY
        elif score >= 15:
            result.signal = SignalType.BUY
        elif score <= -40:
            result.signal = SignalType.STRONG_SELL
        elif score <= -15:
            result.signal = SignalType.SELL
        else:
            result.signal = SignalType.NEUTRAL
        
        # ═══════════════════════════════════════════════════════
        # 📊 محاسبه اعتماد و ریسک
        # ═══════════════════════════════════════════════════════
        
        # اعتماد بر اساس تعداد فاکتورها
        bullish_count = len(result.bullish_factors)
        bearish_count = len(result.bearish_factors)
        total_factors = bullish_count + bearish_count
        
        if total_factors > 0:
            confidence = 50 + (bullish_count - bearish_count) * 10
            result.confidence = max(20, min(95, confidence))
        else:
            result.confidence = 50
        
        # سطح ریسک
        if result.signal in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
            if result.confidence > 70:
                result.risk_level = RiskLevel.LOW
            elif result.confidence > 50:
                result.risk_level = RiskLevel.MEDIUM
            else:
                result.risk_level = RiskLevel.HIGH
        else:
            result.risk_level = RiskLevel.MEDIUM
        
        # ═══════════════════════════════════════════════════════
        # 💡 خلاصه‌سازی محلی
        # ═══════════════════════════════════════════════════════
        
        result.confluence_score = full_data.get_confluence_score()
        
        # ساخت خلاصه
        summary_parts = []
        if result.macro_sentiment:
            summary_parts.append(f"کلان: {result.macro_sentiment}")
        if result.fundamental_sentiment:
            summary_parts.append(f"فاندامنتال: {result.fundamental_sentiment}")
        if result.technical_sentiment:
            summary_parts.append(f"تکنیکال: {result.technical_sentiment}")
        
        result.ai_summary = " | ".join(summary_parts)
        
        # توصیه معاملاتی
        if result.signal == SignalType.STRONG_BUY:
            result.trading_recommendation = "✅ سیگنال قوی خرید - فرصت معاملاتی مناسب"
        elif result.signal == SignalType.BUY:
            result.trading_recommendation = "🟢 سیگنال خرید - بررسی نقطه ورود مناسب"
        elif result.signal == SignalType.STRONG_SELL:
            result.trading_recommendation = "❌ سیگنال قوی فروش - احتیاط در خرید"
        elif result.signal == SignalType.SELL:
            result.trading_recommendation = "🔴 سیگنال فروش - محدوده مناسب برای فروش"
        else:
            result.trading_recommendation = "⚖️ سیگنال خنثی - صبر برای فرصت بهتر"
        
        # هشدار ریسک
        if result.risk_level == RiskLevel.HIGH:
            result.risk_warning = "⚠️ ریسک بالا - مدیریت سرمایه ضروری است"
        elif result.risk_level == RiskLevel.VERY_HIGH:
            result.risk_warning = "🚨 ریسک بسیار بالا - معامله با احتیاط کامل"
        else:
            result.risk_warning = "ℹ️ ریسک متوسط - حد ضرر تعیین کنید"
        
        return result
    
    async def _ai_analysis(
        self,
        local_result: CombinedAnalysisResult,
        full_data: FullAnalysisData,
        smc_result: Optional[Dict]
    ) -> CombinedAnalysisResult:
        """
        تحلیل با استفاده از Google Gemini
        """
        try:
            # ساخت پرامپت جامع
            prompt = self._build_ai_prompt(local_result, full_data, smc_result)
            
            # ارسال به Gemini
            model = self.gemini_client.GenerativeModel(
                model_name=self.model,
                system_instruction="تو یک تحلیلگر حرفه‌ای بازارهای مالی هستی. تحلیل‌هایت دقیق، مختصر و عملیاتی هستند."
            )
            
            response = model.generate_content(prompt)
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
            ai_result = json.loads(content)
            
            logger.info("✅ تحلیل AI دریافت شد")
            return ai_result
            
        except Exception as e:
            logger.error(f"❌ خطا در تحلیل AI: {e}")
            return local_result
    
    def _build_ai_prompt(
        self,
        local_result: CombinedAnalysisResult,
        full_data: FullAnalysisData,
        smc_result: Optional[Dict]
    ) -> str:
        """
        ساخت پرامپت جامع برای AI
        """
        # ساخت داده‌های کلان
        macro_info = ""
        if full_data.macro:
            macro_info = f"""
🎯 داده‌های کلان اقتصادی:
- نرخ بهره فدرال رزرو: {full_data.macro.interest_rate:.2f}% (تغییر: {full_data.macro.interest_rate_change:+.2f}%)
- شاخص CPI: {full_data.macro.cpi:.2f} (تورم سالانه: {full_data.macro.cpi_change:+.2f}%)
- شاخص دلار (DXY): {full_data.macro.dxy:.2f} (تغییر: {full_data.macro.dxy_change:+.2f}%)
- عرضه پول M2: ${full_data.macro.m2_money_supply/1000:.1f}T (تغییر: {full_data.macro.m2_change:+.2f}%)
- احساس کلان: {local_result.macro_sentiment}
"""
        
        # ساخت داده‌های فاندامنتال
        fund_info = ""
        if full_data.crypto_fundamentals:
            fund = full_data.crypto_fundamentals
            fund_info = f"""
💎 داده‌های فاندامنتال:
- ارزش بازار: ${fund.market_cap/1e9:.2f}B (تغییر 24h: {fund.market_cap_change_24h:+.2f}%)
- TVL اتریوم: ${fund.tvl/1e9:.2f}B
- TVL کل DeFi: ${fund.defi_tvl/1e9:.2f}B
- ارزش استیبل‌کوین‌ها: ${fund.stablecoin_mcap/1e9:.2f}B
- نرخ‌های وام‌دهی: {', '.join([f'{k}: {v:.1f}%' for k, v in (fund.lending_rates or {}).items()])}
- احساس فاندامنتال: {local_result.fundamental_sentiment}
"""
        
        # ساخت داده‌های تکنیکال
        tech_info = ""
        if smc_result:
            bias = smc_result.get('bias', 'NEUTRAL')
            confidence = smc_result.get('confidence', 0)
            tech_info = f"""
📈 داده‌های تکنیکال (SMC):
- بایاس: {bias}
- اعتماد: {confidence}%
- نقاط سوئینگ: {smc_result.get('swing_points', 0)}
- FVGs شناسایی شده: {smc_result.get('fvgs', 0)}
- احساس تکنیکال: {local_result.technical_sentiment}
"""
        
        # فاکتورهای همگرایی
        factors_info = f"""
🔗 فاکتورهای همگرایی:
فاکتورهای صعودی ({len(local_result.bullish_factors)}):
{', '.join(local_result.bullish_factors) if local_result.bullish_factors else 'ندارد'}

فاکتورهای نزولی ({len(local_result.bearish_factors)}):
{', '.join(local_result.bearish_factors) if local_result.bearish_factors else 'ندارد'}

فاکتورهای خنثی ({len(local_result.neutral_factors)}):
{', '.join(local_result.neutral_factors) if local_result.neutral_factors else 'ندارد'}

امتیاز همگرایی: {local_result.confluence_score}/100
"""
        
        # پرامپت کامل
        prompt = f"""
تحلیل جامع ترکیبی برای {local_result.symbol} را انجام بده.

📊 اطلاعات فعلی:
قیمت فعلی: ${local_result.current_price:.2f}

{tech_info}

{fund_info}

{macro_info}

{factors_info}

🎯 لطفاً تحلیل کاملی ارائه بده که شامل موارد زیر باشد (در فرمت JSON):

{{
    "signal": "BUY/SELL/HOLD",
    "confidence": 50-95,
    "risk_level": "LOW/MEDIUM/HIGH",
    "risk_reward_ratio": 1.5,
    "ai_sentiment": "خلاصه احساس AI",
    "ai_summary": "خلاصه جامع تحلیل",
    "trading_recommendation": "توصیه معاملاتی دقیق",
    "key_levels": {{
        "entry": "محدوده ورود",
        "sl": "حد ضرر",
        "tp": "اهداف قیمتی"
    }},
    "risk_warning": "هشدار ریسک",
    "bullish_factors": ["فاکتورهای صعودی"],
    "bearish_factors": ["فاکتورهای نزولی"],
    "market_context": "زمینه کلی بازار",
    "outlook": "چشم‌انداز آینده"
}}

نکات مهم:
1. همه اطلاعات (کلان، فاندامنتال، تکنیکال) را ترکیب کن
2. به همگرایی یا واگرایی شاخص‌ها توجه کن
3. توصیه‌های عملیاتی و قابل اجرا بده
4. ریسک‌ها را شفاف بیان کن
5. پاسخ را فقط در فرمت JSON بده
"""

        return prompt
    
    def _merge_results(
        self,
        local_result: CombinedAnalysisResult,
        ai_result: Dict[str, Any]
    ) -> CombinedAnalysisResult:
        """
        ترکیب نتایج محلی و AI
        """
        # اگر AI نتیجه معتبر داد، از آن استفاده کن
        if ai_result and isinstance(ai_result, dict):
            # تنظیم سیگنال
            signal = ai_result.get('signal', '').upper()
            if signal == 'BUY':
                local_result.signal = SignalType.BUY
            elif signal == 'STRONG_BUY':
                local_result.signal = SignalType.STRONG_BUY
            elif signal == 'SELL':
                local_result.signal = SignalType.SELL
            elif signal == 'STRONG_SELL':
                local_result.signal = SignalType.STRONG_SELL
            elif signal == 'HOLD':
                local_result.signal = SignalType.NEUTRAL
            
            # تنظیم اعتماد
            ai_confidence = ai_result.get('confidence', local_result.confidence)
            if isinstance(ai_confidence, (int, float)):
                # میانگین‌گیری بین تحلیل محلی و AI
                local_result.confidence = int((local_result.confidence + ai_confidence) / 2)
            
            # تنظیم ریسک
            risk = ai_result.get('risk_level', '').upper()
            if risk == 'LOW':
                local_result.risk_level = RiskLevel.LOW
            elif risk == 'HIGH':
                local_result.risk_level = RiskLevel.HIGH
            elif risk == 'VERY_HIGH':
                local_result.risk_level = RiskLevel.VERY_HIGH
            
            # تنظیم RR
            rr = ai_result.get('risk_reward_ratio', 0)
            if isinstance(rr, (int, float)) and rr > 0:
                local_result.risk_reward_ratio = rr
            
            # تنظیم احساس AI
            local_result.ai_sentiment = ai_result.get('ai_sentiment', local_result.ai_sentiment)
            local_result.ai_summary = ai_result.get('ai_summary', local_result.ai_summary)
            local_result.trading_recommendation = ai_result.get('trading_recommendation', local_result.trading_recommendation)
            local_result.risk_warning = ai_result.get('risk_warning', local_result.risk_warning)
            
            # اضافه کردن فاکتورهای AI
            if 'bullish_factors' in ai_result:
                local_result.bullish_factors.extend(ai_result['bullish_factors'])
            if 'bearish_factors' in ai_result:
                local_result.bearish_factors.extend(ai_result['bearish_factors'])
            
            # تنظیم چشم‌انداز
            local_result.ai_sentiment = ai_result.get('outlook', local_result.ai_sentiment)
        
        return local_result
    
    def _create_default_result(self, symbol: str, error: str) -> CombinedAnalysisResult:
        """ایجاد نتیجه پیش‌فرض در صورت خطا"""
        return CombinedAnalysisResult(
            symbol=symbol,
            signal=SignalType.NEUTRAL,
            confidence=50,
            risk_level=RiskLevel.MEDIUM,
            ai_summary=f"خطا در تحلیل: {error}",
            trading_recommendation="⚠️ تحلیل با مشکل مواجه شد",
            risk_warning="⚠️ با احتیاط معامله کنید"
        )
    
    def format_combined_message(self, result: CombinedAnalysisResult) -> str:
        """
        فرمت‌بندی پیام تحلیل ترکیبی
        """
        # انتخاب ایموجی بر اساس سیگنال
        signal_emojis = {
            SignalType.STRONG_BUY: "🟢",
            SignalType.BUY: "🟢",
            SignalType.NEUTRAL: "🟡",
            SignalType.SELL: "🔴",
            SignalType.STRONG_SELL: "🔴"
        }
        
        emoji = signal_emojis.get(result.signal, "⚖️")
        
        # فرمت‌بندی TVL و Market Cap
        tvl_str = f"${result.tvl/1e9:.2f}B" if result.tvl > 1e9 else f"${result.tvl/1e6:.2f}M"
        mcap_str = f"${result.market_cap/1e9:.2f}B" if result.market_cap > 1e9 else f"${result.market_cap/1e6:.2f}M"
        
        # فرمت‌بندی RR
        rr_str = f"1:{result.risk_reward_ratio:.1f}" if result.risk_reward_ratio > 0 else "N/A"
        
        message = f"""
{emoji} تحلیل هوشمند ترکیبی {result.symbol}
{'─' * 40}

🎯 **سیگنال:** {result.signal.value}
📊 **اعتماد:** {result.confidence}%
⚠️ **ریسک:** {result.risk_level.value}
📈 **نسبت ریسک/پاداش:** {rr_str}

💰 **قیمت فعلی:** ${result.current_price:,.2f}
💎 **ارزش بازار:** {mcap_str}
🔒 **TVL:** {tvl_str}

🏦 **محیط کلان:** {result.macro_sentiment or 'نامشخص'}
💎 **فاندامنتال:** {result.fundamental_sentiment or 'نامشخص'}
📈 **تکنیکال:** {result.technical_sentiment or 'نامشخص'}

{'─' * 40}
🎯 **امتیاز همگرایی:** {result.confluence_score}/100

📝 **خلاصه AI:**
{result.ai_summary}

💡 **توصیه معاملاتی:**
{result.trading_recommendation}

⚠️ **هشدار ریسک:**
{result.risk_warning}

{'─' * 40}
🔗 **فاکتورهای همگرایی:**

📗 **صعودی ({len(result.bullish_factors)}):**
{chr(10).join([f"   • {f}" for f in result.bullish_factors[:5]]) if result.bullish_factors else "   • ندارد"}

📕 **نزولی ({len(result.bearish_factors)}):**
{chr(10).join([f"   • {f}" for f in result.bearish_factors[:5]]) if result.bearish_factors else "   • ندارد"}

🕐 به‌روزرسانی شده در: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        return message


# ═══════════════════════════════════════════════════════════════
# 📤 Export
# ═══════════════════════════════════════════════════════════════

# نمونه واحد (Singleton)
ai_integrated_analyzer = AIIntegratedAnalyzer()

# لیست خروجی
__all__ = [
    'CombinedAnalysisResult',
    'SignalType',
    'RiskLevel',
    'AIIntegratedAnalyzer',
    'ai_integrated_analyzer'
]


# ═══════════════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    
    # تنظیم لاگینگ
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("🤖 تست ماژول تحلیل ترکیبی AI")
    print("=" * 60)
    
    # بررسی Gemini
    print(f"\n📋 وضعیت Gemini: {'✅ تنظیم شده' if GEMINI_API_KEY else '❌ تنظیم نشده'}")
    
    async def test():
        try:
            analyzer = AIIntegratedAnalyzer()
            
            # تست با ETH
            print(f"\n🧪 تست با ETH...")
            result = await analyzer.analyze_combined(symbol="ETH", current_price=2200)
            
            print(f"\n✅ نتیجه تحلیل:")
            print(f"   سیگنال: {result.signal.value}")
            print(f"   اعتماد: {result.confidence}%")
            print(f"   ریسک: {result.risk_level.value}")
            print(f"   همگرایی: {result.confluence_score}/100")
            print(f"\n📝 خلاصه: {result.ai_summary}")
            print(f"\n💡 توصیه: {result.trading_recommendation}")
            
            # نمایش پیام کامل
            print("\n" + "=" * 60)
            print(analyzer.format_combined_message(result))
            
        except Exception as e:
            print(f"\n❌ خطا: {e}")
            import traceback
            traceback.print_exc()
    
    # اجرای تست
    asyncio.run(test())
