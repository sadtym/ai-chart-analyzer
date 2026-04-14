"""
تست‌های واحد برای پروژه تحلیل گر هوشمند چارت
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from io import BytesIO

# اضافه کردن مسیر پروژه
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from PIL import Image

# импорт ماژول‌ها
from config import (
    TELEGRAM_TOKEN, 
    OPENAI_API_KEY, 
    CHARTS_DIR,
    IMAGE_MAX_WIDTH
)


class TestConfig:
    """تست تنظیمات پیکربندی"""
    
    def test_charts_directory_exists(self):
        """بررسی وجود پوشه charts"""
        assert CHARTS_DIR.exists(), "پوشه charts باید وجود داشته باشد"
    
    def test_image_max_width(self):
        """بررسی حداکثر عرض تصویر"""
        assert IMAGE_MAX_WIDTH == 1024, "عرض پیش‌فرض باید 1024 باشد"
    
    def test_telegram_token_is_string(self):
        """بررسی نوع توکن تلگرام"""
        # در تست، ممکن است توکن تنظیم نشده باشد
        if TELEGRAM_TOKEN:
            assert isinstance(TELEGRAM_TOKEN, str), "توکن باید رشته باشد"
    
    def test_openai_api_key_is_string(self):
        """بررسی نوع کلید OpenAI"""
        if OPENAI_API_KEY:
            assert isinstance(OPENAI_API_KEY, str), "کلید API باید رشته باشد"


class TestImageProcessor:
    """تست پردازشگر تصویر"""
    
    def test_preprocess_image_creates_base64(self):
        """تست فشرده‌سازی تصویر و تبدیل به base64"""
        from modules.image_processor import preprocess_image
        
        # ایجاد تصویر تست
        test_image = Image.new('RGB', (1920, 1080), color='white')
        buffer = BytesIO()
        test_image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        
        # ذخیره موقت
        test_path = CHARTS_DIR / "test_image.jpg"
        with open(test_path, 'wb') as f:
            f.write(buffer.read())
        
        try:
            # تست پیش‌پردازش
            result = preprocess_image(str(test_path))
            
            assert isinstance(result, str), "خروجی باید رشته باشد"
            assert len(result) > 0, "خروجی نباید خالی باشد"
            
            # بررسی معتبر بودن base64
            import base64
            decoded = base64.b64decode(result)
            assert len(decoded) > 0, "باید قابلیت decode داشته باشد"
            
        finally:
            if test_path.exists():
                test_path.unlink()
    
    def test_validate_image_valid(self):
        """تست اعتبارسنجی تصویر معتبر"""
        from modules.image_processor import validate_image
        
        # ایجاد تصویر معتبر
        test_image = Image.new('RGB', (500, 500), color='blue')
        test_path = CHARTS_DIR / "valid_test.jpg"
        test_image.save(test_path, 'JPEG')
        
        try:
            is_valid, message = validate_image(str(test_path))
            
            assert is_valid == True, f"تصویر باید معتبر باشد: {message}"
            assert "معتبر" in message, "پیام باید شامل 'معتبر' باشد"
            
        finally:
            if test_path.exists():
                test_path.unlink()
    
    def test_validate_image_not_exists(self):
        """تست اعتبارسنجی تصویر وجود ندارد"""
        from modules.image_processor import validate_image
        
        is_valid, message = validate_image("/nonexistent/path.jpg")
        
        assert is_valid == False, "باید نامعتبر باشد"
        assert "یافت نشد" in message, "پیام باید شامل 'یافت نشد' باشد"
    
    def test_validate_image_too_small(self):
        """تست اعتبارسنجی تصویر با ابعاد کوچک"""
        from modules.image_processor import validate_image
        
        # ایجاد تصویر کوچک
        test_image = Image.new('RGB', (50, 50), color='red')
        test_path = CHARTS_DIR / "small_test.jpg"
        test_image.save(test_path, 'JPEG')
        
        try:
            is_valid, message = validate_image(str(test_path))
            
            assert is_valid == False, "باید نامعتبر باشد"
            assert "کوچک" in message, "پیام باید شامل 'کوچک' باشد"
            
        finally:
            if test_path.exists():
                test_path.unlink()
    
    def test_get_unique_filename(self):
        """تست تولید نام یکتا"""
        from modules.image_processor import get_unique_filename
        
        filename1 = get_unique_filename(12345)
        filename2 = get_unique_filename(12345)
        
        assert filename1 != filename2, "نام‌ها باید متفاوت باشند"
        assert filename1.suffix == ".jpg", "پسوند باید jpg باشد"
        assert str(filename1).startswith(str(CHARTS_DIR)), "باید در پوشه charts باشد"


class TestSignalFormatter:
    """تست فرمت‌بند سیگنال"""
    
    def test_format_signal_bullish(self):
        """تست فرمت‌بندی سیگنال صعودی"""
        from modules.signal_formatter import SignalFormatter
        
        data = {
            "symbol": "BTCUSD",
            "timeframe": "4H",
            "trend": "صعودی",
            "entry_zone": {"min": "64000", "max": "64500"},
            "stop_loss": "63800",
            "take_profit": ["66000", "68000"],
            "analysis": "قیمت به سطح حمایت رسیده",
            "confidence": "85"
        }
        
        result = SignalFormatter.format_signal(data)
        
        assert isinstance(result, str), "خروجی باید رشته باشد"
        assert len(result) > 0, "خروجی نباید خالی باشد"
        assert "BTCUSD" in result, "باید شامل نماد باشد"
        assert "64,000" in result, "باید شامل قیمت ورود باشد"
        assert "🟢" in result, "باید شامل ایموجی سبز باشد"
    
    def test_format_signal_bearish(self):
        """تست فرمت‌بندی سیگنال نزولی"""
        from modules.signal_formatter import SignalFormatter
        
        data = {
            "symbol": "ETHUSD",
            "timeframe": "1H",
            "trend": "نزولی",
            "entry_zone": {"min": "3500", "max": "3520"},
            "stop_loss": "3550",
            "take_profit": ["3400", "3300"],
            "analysis": "الگوی سر و شانه تشکیل شده",
            "confidence": "80"
        }
        
        result = SignalFormatter.format_signal(data)
        
        assert "🔴" in result, "باید شامل ایموجی قرمز باشد"
        assert "SHORT" in result, "باید شامل SHORT باشد"
    
    def test_format_error_message(self):
        """تست فرمت‌بندی پیام خطا"""
        from modules.signal_formatter import SignalFormatter
        
        result = SignalFormatter.format_error_message("خطای تست")
        
        assert isinstance(result, str), "خروجی باید رشته باشد"
        assert "خطا" in result, "باید شامل 'خطا' باشد"
    
    def test_format_welcome_message(self):
        """تست فرمت‌بندی پیام خوشامدگویی"""
        from modules.signal_formatter import SignalFormatter
        
        result = SignalFormatter.format_welcome_message()
        
        assert isinstance(result, str), "خروجی باید رشته باشد"
        assert len(result) > 0, "خروجی نباید خالی باشد"
    
    def test_format_help_message(self):
        """تست فرمت‌بندی پیام راهنما"""
        from modules.signal_formatter import SignalFormatter
        
        result = SignalFormatter.format_help_message()
        
        assert isinstance(result, str), "خروجی باید رشته باشد"
        assert "راهنما" in result or "راهنما" in result, "باید شامل راهنما باشد"


class TestChartAnalyzer:
    """تست تحلیلگر چارت"""
    
    @pytest.mark.skipif(not OPENAI_API_KEY, reason="API key not available")
    def test_analyzer_initialization(self):
        """تست راه‌اندازی تحلیلگر"""
        from modules.ai_analyzer import ChartAnalyzer
        
        analyzer = ChartAnalyzer()
        
        assert analyzer is not None, "تحلیلگر باید ایجاد شود"
        assert hasattr(analyzer, 'analyze'), "باید متد analyze داشته باشد"
    
    @pytest.mark.skipif(not OPENAI_API_KEY, reason="API key not available")
    def test_default_result_structure(self):
        """تست ساختار نتیجه پیش‌فرض"""
        from modules.ai_analyzer import ChartAnalyzer
        
        analyzer = ChartAnalyzer()
        result = analyzer._create_default_result("خطای تست")
        
        assert isinstance(result, dict), "خروجی باید دیکشنری باشد"
        assert "error" in result, "باید شامل فیلد error باشد"
        assert result["error"] == True, "باید خطا را نشان دهد"


class TestBotIntegration:
    """تست‌های یکپارچگی ربات"""
    
    def test_imports_work(self):
        """تست تمام import‌ها"""
        try:
            from config import TELEGRAM_TOKEN, OPENAI_API_KEY
            from modules.image_processor import preprocess_image, validate_image
            from modules.ai_analyzer import ChartAnalyzer
            from modules.signal_formatter import SignalFormatter
            from aiogram import Bot, Dispatcher
            assert True
        except ImportError as e:
            pytest.fail(f"خطا در import: {e}")
    
    def test_project_structure(self):
        """تست ساختار پروژه"""
        required_files = [
            "bot.py",
            "config.py",
            "requirements.txt",
            "README.md"
        ]
        
        required_dirs = [
            "modules",
            "charts",
            "data"
        ]
        
        for file in required_files:
            assert (PROJECT_ROOT / file).exists(), f"فایل {file} باید وجود داشته باشد"
        
        for dir_name in required_dirs:
            assert (PROJECT_ROOT / dir_name).exists(), f"پوشه {dir_name} باید وجود داشته باشد"


def run_tests():
    """اجرای تمام تست‌ها"""
    print("🚀 شروع اجرای تست‌ها...")
    print(f"📁 مسیر پروژه: {PROJECT_ROOT}")
    print()
    
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
