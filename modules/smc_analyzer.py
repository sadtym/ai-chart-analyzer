"""
ماژول یکپارچه‌سازی SMC Engine با تحلیل هوش مصنوعی
ترکیب تحلیل SMC با Gemini برای تولید سیگنال‌های معاملاتی

این ماژول شامل:
- دریافت داده‌های بازار
- اجرای SMC Engine
- تحلیل توسط AI
- تولید سیگنال ساختاریافته
"""

import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
from telegram import Update

from config import (
    DEFAULT_TIMEFRAMES, GEMINI_API_KEY, AI_MODEL,
    MAX_TOKENS, TEMPERATURE
)

try:
    from modules.smc_engine import SMCEngine, create_smc_analysis, get_trade_setup_from_data
    from modules.ai_analyzer import AIAnalyzer
except ImportError:
    from smc_engine import SMCEngine, create_smc_analysis, get_trade_setup_from_data
    from ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)


class SMCTraderAnalyzer:
    """
    تحلیلگر ترکیبی SMC + AI
    
    این کلاس SMC Engine را با هوش مصنوعی ترکیب می‌کند تا:
    1. داده‌های بازار را تحلیل کند
    2. ساختار SMC را استخراج کند
    3. توسط AI تفسیر کند
    4. سیگنال معاملاتی صادر کند
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        مقداردهی اولیه
        
        Args:
            api_key: کلید API Gemini (اختیاری)
            model: نام مدل AI (اختیاری)
        """
        self.ai_analyzer = AIAnalyzer(
            api_key=api_key or GEMINI_API_KEY,
            model=model or AI_MODEL
        )
        
        # تنظیمات تحلیل
        self.timeframes = DEFAULT_TIMEFRAMES
        self.min_confidence = 60  # حداقل اطمینان برای صدور سیگنال
    
    def analyze_market_with_smc(
        self,
        df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        include_ai_narrative: bool = True
    ) -> Dict:
        """
        تحلیل کامل بازار با SMC + AI
        
        Args:
            df: دیتافریم OHLCV
            symbol: نماد معاملاتی
            include_ai_narrative: آیا تفسیر AI اضافه شود؟
            
        Returns:
            نتایج تحلیل کامل
        """
        try:
            # اجرای SMC Engine
            logger.info(f"Starting SMC analysis for {symbol}")
            smc_result = create_smc_analysis(df)
            
            # استخراج تنظیم معاملاتی
            trade_setup = get_trade_setup_from_data(df)
            
            result = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "smc_analysis": smc_result,
                "trade_setup": trade_setup,
                "ai_narrative": None
            }
            
            # تحلیل توسط AI (در صورت درخواست)
            if include_ai_narrative and trade_setup:
                result["ai_narrative"] = self._generate_ai_analysis(smc_result, trade_setup)
            
            logger.info(f"SMC analysis completed for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error in SMC analysis: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_ai_analysis(
        self,
        smc_result: Dict,
        trade_setup: Dict
    ) -> Dict:
        """
        تولید تحلیل توسط هوش مصنوعی
        """
        prompt = self._build_ai_prompt(smc_result, trade_setup)
        
        ai_response = self.ai_analyzer.analyze(prompt)
        
        return {
            "narrative": ai_response.get("analysis", ""),
            "confidence": ai_response.get("confidence", 0),
            "risk_assessment": ai_response.get("risk", "")
        }
    
    def _build_ai_prompt(
        self,
        smc_result: Dict,
        trade_setup: Dict
    ) -> str:
        """
        ساخت پرامپت برای AI
        """
        market = smc_result.get("market_condition", {})
        structures = smc_result.get("recent_structures", [])
        levels = smc_result.get("key_levels", {})
        
        prompt = f"""
بازار: {market.get('symbol', 'crypto')}
قیمت فعلی: {market.get('current_price', 'N/A')}
روند: {market.get('trend', 'N/A')} (قدرت: {market.get('trend_strength', 0)})
نوسانات: {market.get('volatility', 'N/A')}
وضعیت حجم: {market.get('volume_status', 'N/A')}

## رویدادهای ساختاری اخیر:
{json.dumps(structures, indent=2, ensure_ascii=False)}

## سطوح کلیدی:
### Order Blocks:
{json.dumps(levels.get('order_blocks', []), indent=2, ensure_ascii=False)}

### Fair Value Gaps:
{json.dumps(levels.get('fair_value_gaps', []), indent=2, ensure_ascii=False)}

### نواحی نقدینگی:
{json.dumps(levels.get('liquidity', []), indent=2, ensure_ascii=False)}

## تنظیم معاملاتی پیشنهادی:
جهت: {trade_setup.get('direction', 'N/A')}
ناحیه ورود: {trade_setup.get('entry_zone', 'N/A')}
حد ضرر: {trade_setup.get('stop_loss', 'N/A')}
قیمت فعلی: {trade_setup.get('current_price', 'N/A')}
حد سودها: {trade_setup.get('take_profits', [])}
نسبت R/R: {trade_setup.get('rr_ratios', [])}
اطمینان SMC: {trade_setup.get('confidence_based_on_smc', 0)}%

لطفاً تحلیل کاملی ارائه دهید شامل:
1. خلاصه وضعیت بازار (2-3 جمله)
2. تحلیل ساختار و روند
3. ارزیابی تنظیم معاملاتی
4. نقاط ورود، حد ضرر و حد سود
5. سطح اطمینان (0-100%)
6. ریسک‌ها و ملاحظات

پاسخ را به صورت JSON با فرمت زیر بدهید:
{{
    "summary": "خلاصه وضعیت بازار",
    "trend_analysis": "تحلیل روند و ساختار",
    "setup_evaluation": "ارزیابی تنظیم معاملاتی",
    "entry_point": "نقطه ورود پیشنهادی",
    "stop_loss": "حد ضرر",
    "take_profits": ["حد سود اول", "حد سود دوم"],
    "confidence": 85,
    "risk_assessment": "ریسک‌ها و ملاحظات"
}}
"""
        return prompt
    
    def format_telegram_signal(
        self,
        analysis_result: Dict,
        include_chart: bool = False
    ) -> str:
        """
        فرمت‌بندی سیگنال برای ارسال در تلگرام
        """
        if "error" in analysis_result:
            return f"❌ خطا در تحلیل: {analysis_result['error']}"
        
        smc = analysis_result.get("smc_analysis", {})
        trade = analysis_result.get("trade_setup", {})
        ai = analysis_result.get("ai_narrative", {})
        
        market = smc.get("market_condition", {})
        direction = trade.get("direction", "N/A")
        
        # انتخاب ایموجی بر اساس جهت
        if direction == "LONG":
            emoji = "📈"
            direction_text = "**خرید (LONG)**"
        elif direction == "SHORT":
            emoji = "📉"
            direction_text = "**فروش (SHORT)**"
        else:
            emoji = "⚖️"
            direction_text = "**خنثی**"
        
        # محاسبه اطمینان نهایی
        smc_confidence = trade.get("confidence_based_on_smc", 0)
        ai_confidence = ai.get("confidence", 0)
        final_confidence = int((smc_confidence + ai_confidence) / 2)
        
        # ساخت پیام
        message = f"""
{emoji} **سیگنال معاملاتی SMC + AI**

━━━━━━━━━━━━━━━━━━━━
{direction_text}
━━━━━━━━━━━━━━━━━━━━

**قیمت فعلی:** ${market.get('current_price', 'N/A')}
**روند:** {market.get('trend', 'N/A')} | قدرت: {market.get('trend_strength', 0)}/1

**🎯 تنظیم معاملاتی:**
• **ناحیه ورود:** `{trade.get('entry_zone', 'N/A')}`
• **حد ضرر (SL):** `${trade.get('stop_loss', 'N/A')}`
• **حد سود (TP):** `{" / ".join(str(tp) for tp in trade.get('take_profits', []))}`
• **نسبت R/R:** `{trade.get('rr_ratios', [])}`

**📊 اطمینان:** {final_confidence}% (SMC: {smc_confidence}% | AI: {ai_confidence}%)

**🤖 تحلیل AI:**
{ai.get('narrative', 'تحلیل در دسترس نیست')}

━━━━━━━━━━━━━━━━━━━━
⚠️ **مدیریت ریسک:** {ai.get('risk_assessment', 'ریسک‌ها را ارزیابی کنید')}
━━━━━━━━━━━━━━━━━━━━
"""
        
        return message
    
    async def analyze_with_ai(
        self,
        symbol: str,
        ohlcv_data: Dict
    ) -> Dict:
        """
        تحلیل کامل با هوش مصنوعی
        
        Args:
            symbol: نماد معاملاتی
            ohlcv_data: داده‌های OHLCV
            
        Returns:
            نتیجه تحلیل
        """
        # تبدیل به DataFrame
        df = pd.DataFrame(ohlcv_data)
        
        # تحلیل SMC
        result = self.analyze_market_with_smc(df, symbol)
        
        return result


# ═══════════════════════════════════════════════════════════════
# توابع کمکی برای استفاده مستقیم
# ═══════════════════════════════════════════════════════════════

def quick_smc_analysis(df: pd.DataFrame) -> Dict:
    """
    تحلیل سریع SMC (بدون AI)
    
    Args:
        df: دیتافریم OHLCV
        
    Returns:
        نتایج SMC
    """
    return create_smc_analysis(df)


def get_smc_trade_setup(df: pd.DataFrame) -> Optional[Dict]:
    """
    دریافت تنظیم معاملاتی SMC
    
    Args:
        df: دیتافریم OHLCV
        
    Returns:
        تنظیم معاملاتی یا None
    """
    return get_trade_setup_from_data(df)


def format_smc_signal(result: Dict) -> str:
    """
    فرمت‌بندی سیگنال SMC برای تلگرام
    
    Args:
        result: نتیجه تحلیل
        
    Returns:
        پیام فرمت‌شده
    """
    analyzer = SMCTraderAnalyzer()
    return analyzer.format_telegram_signal(result)


# ═══════════════════════════════════════════════════════════════
# مثال استفاده
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # نمونه داده
    import numpy as np
    
    # تولید داده‌های نمونه
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1H")
    base_price = 50000
    
    data = {
        'timestamp': dates,
        'open': base_price + np.cumsum(np.random.randn(100) * 100),
        'high': None,
        'low': None,
        'close': None,
        'volume': np.random.randint(1000, 10000, 100)
    }
    
    # محاسبه high و low
    data['high'] = data['open'] + np.abs(np.random.randn(100) * 50)
    data['low'] = data['open'] - np.abs(np.random.randn(100) * 50)
    data['close'] = (data['open'] + data['high'] + data['low']) / 3 + np.random.randn(100) * 30
    
    df = pd.DataFrame(data)
    
    # اجرای تحلیل
    print("در حال اجرای تحلیل SMC...")
    
    result = quick_smc_analysis(df)
    setup = get_smc_trade_setup(df)
    
    print("\n📊 نتایج SMC:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if setup:
        print("\n🎯 تنظیم معاملاتی:")
        print(json.dumps(setup, indent=2, ensure_ascii=False))
    else:
        print("\n⚠️ تنظیم معاملاتی یافت نشد")
