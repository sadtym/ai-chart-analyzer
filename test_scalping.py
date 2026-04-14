#!/usr/bin/env python3
"""
تست تحلیل اسکالپ با چارت واقعی
"""

import sys
import os
import base64

# Add project root to path
sys.path.insert(0, '/workspace/ai_chart_analyzer')

from dotenv import load_dotenv
load_dotenv()

from modules.ai_analyzer import ChartAnalyzer
from modules.signal_formatter import SignalFormatter
from config import GEMINI_MODEL, AI_PROVIDER, SYSTEM_PROMPT

def image_to_base64(image_path: str) -> str:
    """تبدیل تصویر به base64"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def main():
    print("🚀 شروع تحلیل اسکالپ...")
    print(f"📊 مدل: {GEMINI_MODEL}")
    print(f"🔧 پرووایدر: {AI_PROVIDER}")
    print("-" * 50)
    
    # مسیر تصویر
    image_path = '/workspace/user_input_files/Screenshot_20251224-091008.png'
    
    if not os.path.exists(image_path):
        print(f"❌ خطا: فایل تصویر یافت نشد: {image_path}")
        return
    
    print(f"📸 تحلیل چارت: {image_path}")
    
    # تبدیل تصویر به base64
    print("📦 تبدیل تصویر به base64...")
    base64_image = image_to_base64(image_path)
    print(f"✅ تصویر با موفقیت encode شد (طول: {len(base64_image)} کاراکتر)")
    
    # نمایش پرامپت سیستمی
    print("\n" + "=" * 60)
    print("📝 پرامپت سیستمی AI:")
    print("=" * 60)
    print(SYSTEM_PROMPT[:500] + "..." if len(SYSTEM_PROMPT) > 500 else SYSTEM_PROMPT)
    print("=" * 50)
    
    # تحلیل توسط AI
    print("\n🔄 ارسال به Gemini...")
    analyzer = ChartAnalyzer()
    result = analyzer.analyze(base64_image)
    
    print("\n" + "=" * 60)
    print("📋 خروجی خام از AI:")
    print("=" * 60)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)
    
    # فرمت‌بندی پیام
    print("\n📱 پیام نهایی برای تلگرام:")
    print("=" * 60)
    message = SignalFormatter.format_signal(result)
    print(message)
    print("=" * 60)
    
    if result.get('error'):
        print("\n❌ تحلیل با خطا مواجه شد")
    else:
        print("\n✅ تحلیل با موفقیت انجام شد!")

if __name__ == "__main__":
    main()
