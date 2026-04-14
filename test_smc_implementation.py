#!/usr/bin/env python3
"""
تست کوتاه برای بررسی عملکرد پیاده‌سازی جدید SMC
"""

import sys
import os

# اضافه کردن مسیر پروژه
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_modules():
    """تست ماژول‌های اصلی پروژه"""
    
    print("🧪 تست ماژول‌های پروژه...")
    
    try:
        # تست import کردن ماژول‌ها
        from modules.ai_analyzer import ChartAnalyzer
        from modules.leverage_calculator import LeverageCalculator  
        from modules.signal_formatter import SignalFormatter
        print("✅ همه ماژول‌ها با موفقیت import شدند")
        
        # تست محاسبه‌گر اهرم
        calc = LeverageCalculator()
        test_leverage = calc.suggest_leverage(
            confidence=75,
            volatility_level="متوسط",
            trade_type="scalping"
        )
        print(f"✅ تست اهرم: {test_leverage}")
        
        # تست فرمت‌کننده با ساختار SMC جدید
        test_data = {
            'bias': 'LONG',
            'entry': '1.2500', 
            'sl': '1.2450',
            'tp': '1.2600',
            'confidence': 85,
            'structure': 'روند صعودی با شکست ساختار (BOS) تایید شده',
            'zones': 'اردر بلاک قوی در 1.2480 - FVG در نزدیکی 1.2495',
            'momentum': 'RSI در 42 - واگرایی مثبت مشاهده شده',
            'decision_reasoning': 'ترکیب مناسب از سیگنال‌های SMC برای ورود خرید',
            'leverage_recommendation': '5',
            'leverage_reasoning': 'اعتماد بالا و تایید چندگانه سیگنال‌ها'
        }
        
        formatted_message = SignalFormatter.format_signal(test_data)
        print("✅ پیام SMC فرمت شد:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(formatted_message)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━")
        
    except ImportError as e:
        print(f"❌ خطا در import: {e}")
        return False
    except Exception as e:
        print(f"❌ خطا در تست: {e}")
        return False
    
    print("🎉 همه تست‌ها با موفقیت انجام شد!")
    return True

if __name__ == "__main__":
    success = test_modules()
    if success:
        print("\n✨ آماده راه‌اندازی ربات با قابلیت‌های SMC جدید!")
    else:
        print("\n❌ برخی تست‌ها ناموفق بودند")
        sys.exit(1)