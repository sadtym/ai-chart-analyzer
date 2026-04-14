#!/usr/bin/env python3
"""
تست سریع قابلیت‌های SMC
"""
import sys
import os
sys.path.append('/workspace/ai_chart_analyzer')

# تست import ماژول‌ها
try:
    from modules.ai_analyzer import ChartAnalyzer
    from modules.signal_formatter import SignalFormatter
    from modules.leverage_calculator import LeverageCalculator
    print("✅ همه ماژول‌ها با موفقیت بارگذاری شدند")
    
    # تست فرمت‌کننده SMC
    test_smc_data = {
        'bias': 'LONG',
        'entry': '1.2500',
        'sl': '1.2450', 
        'tp': '1.2600',
        'confidence': 85,
        'structure': 'روند صعودی با شکست ساختار (BOS) تایید شده در محدوده 1.2470',
        'zones': 'اردر بلاک قوی در نزدیکی 1.2480 - Fair Value Gap مشخص شده در 1.2495',
        'momentum': 'RSI در ناحیه 42 نشان‌دهنده قدرت خرید - واگرایی مثبت مشاهده شده',
        'decision_reasoning': 'ترکیب سه عامل SMC: ساختار صعودی، اردر بلاک معتبر و واگرایی مثبت RSI موجبات اعتماد بالا برای ورود خرید را فراهم کرده است',
        'leverage_recommendation': '5',
        'leverage_reasoning': 'با توجه به اعتماد 85% و تایید چندگانه سیگنال‌ها'
    }
    
    # تست فرمت‌کردن پیام
    formatted_signal = SignalFormatter.format_signal(test_smc_data)
    print("\n🎯 نمونه خروجی SMC:")
    print("=" * 50)
    print(formatted_signal)
    print("=" * 50)
    
    # تست محاسبه‌گر اهرم
    leverage_calc = LeverageCalculator()
    suggested_leverage = leverage_calc.suggest_leverage(85, "متوسط", "scalping")
    print(f"\n🎚️ اهرم پیشنهادی: {suggested_leverage}")
    
    print("\n✨ همه سیستم‌ها آماده!")
    print("🤖 ربات آماده ارائه تحلیل‌های SMC حرفه‌ای است")
    
except Exception as e:
    print(f"❌ خطا در تست: {e}")
    import traceback
    traceback.print_exc()

print("\n📋 برای راه‌اندازی ربات:")
print("cd /workspace/ai_chart_analyzer")
print("python start_bot_now.py")