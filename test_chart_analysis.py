"""
تست عملی تحلیل چارت با Gemini API
"""

import os
import sys
from pathlib import Path
from PIL import Image
from io import BytesIO
import base64

# تنظیم مسیر
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# بارگذاری تنظیمات
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from modules.ai_analyzer import ChartAnalyzer
from modules.image_processor import preprocess_image
from modules.signal_formatter import SignalFormatter

def create_sample_chart():
    """ایجاد یک چارت نمونه برای تست"""
    # ایجاد یک تصویر ساده که شبیه چارت باشد
    img = Image.new('RGB', (800, 400), color='#1a1a2e')
    
    # رسم خطوط چارت
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # پس‌زمینه تیره
    draw.rectangle([0, 0, 800, 400], fill='#1a1a2e')
    
    # رسم محورها
    draw.rectangle([60, 20, 70, 350], fill='#444')  # محور y
    draw.rectangle([60, 340, 750, 350], fill='#444')  # محور x
    
    # رسم قیمت‌ها روی محور y
    prices = ['$65,000', '$64,000', '$63,000', '$62,000']
    y_positions = [50, 120, 190, 260]
    for price, y in zip(prices, y_positions):
        draw.text((75, y), price, fill='#fff')
    
    # رسم تایم‌فریم روی محور x
    draw.text((650, 355), '4H', fill='#888')
    
    # رسم کندل‌های نمونه (y1 باید کوچکتر از y2 باشد)
    candles = [
        (100, 140, 110, 150, '#00ff00'),  # سبز
        (120, 145, 130, 155, '#ff0000'),  # قرمز
        (140, 150, 150, 160, '#00ff00'),  # سبز
        (160, 155, 170, 165, '#00ff00'),  # سبز
        (180, 160, 190, 170, '#ff0000'),  # قرمز
        (200, 155, 210, 175, '#00ff00'),  # سبز
    ]
    
    for x1, y1, x2, y2, color in candles:
        draw.rectangle([x1, y1, x2, y2], fill=color)
    
    # عنوان چارت
    draw.text((300, 370), 'BTC/USD - 4 Hour Chart', fill='#888')
    
    return img

def main():
    print("=" * 70)
    print("🚀 تست عملی تحلیل چارت با Google Gemini")
    print("=" * 70)
    
    # بررسی تنظیمات
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("❌ خطا: GEMINI_API_KEY تنظیم نشده است!")
        return
    
    print(f"\n✅ API Key: {gemini_key[:15]}...")
    print(f"📊 مدل: gemini-1.5-flash")
    
    # ایجاد چارت نمونه
    print("\n📈 ایجاد چارت نمونه...")
    chart_img = create_sample_chart()
    
    # ذخیره موقت چارت
    chart_path = PROJECT_ROOT / "test_chart.jpg"
    chart_img.save(chart_path)
    print(f"✅ چارت ذخیره شد: {chart_path}")
    
    # پیش‌پردازش تصویر
    print("\n🔧 پیش‌پردازش تصویر...")
    base64_image = preprocess_image(str(chart_path))
    print(f"✅ تصویر به base64 تبدیل شد (طول: {len(base64_image)} کاراکتر)")
    
    # راه‌اندازی تحلیلگر
    print("\n🤖 راه‌اندازی تحلیلگر...")
    try:
        analyzer = ChartAnalyzer()
        print(f"✅ تحلیلگر راه‌اندازی شد: {analyzer.model}")
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی: {e}")
        return
    
    # تحلیل چارت
    print("\n📊 ارسال چارت به Gemini برای تحلیل...")
    print("⏳ لطفاً صبر کنید (حدود 10-20 ثانیه)...")
    
    try:
        result = analyzer.analyze(base64_image)
        
        print("\n" + "=" * 70)
        print("📋 نتیجه تحلیل:")
        print("=" * 70)
        
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # فرمت‌بندی و نمایش سیگنال
        print("\n" + "=" * 70)
        print("📨 سیگنال فرمت‌شده:")
        print("=" * 70)
        signal_text = SignalFormatter.format_signal(result)
        print(signal_text)
        
        print("\n" + "=" * 70)
        print("✅ تست با موفقیت تکمیل شد!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ خطا در تحلیل: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # پاکسازی
        if chart_path.exists():
            chart_path.unlink()
            print("\n🧹 فایل موقت پاکسازی شد")

if __name__ == "__main__":
    main()
