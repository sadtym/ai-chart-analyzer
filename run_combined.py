"""
اسکریپت راه‌اندازی ترکیبی
اجرای همزمان ربات تلگرام و سرور Webhook

💡 استفاده:
    python run_combined.py

این اسکریپت هر دو سرویس را به صورت همزمان اجرا می‌کند:
- ربات تلگرام (دریافت تصاویر و تحلیل)
- سرور Webhook (دریافت Alerts از TradingView)
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# اضافه کردن مسیر پروژه
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "modules"))

# ═══════════════════════════════════════════════════════════════
# ⚙️ تنظیمات لاگینگ
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 🚀 تابع اصلی
# ═══════════════════════════════════════════════════════════════

async def main():
    """
    اجرای همزمان ربات تلگرام و سرور Webhook
    """
    logger.info("=" * 60)
    logger.info("🚀 راه‌اندازی سیستم ترکیبی...")
    logger.info("=" * 60)
    
    try:
        # ═══════════════════════════════════════════════════════
        # 🟢 راه‌اندازی ربات تلگرام
        # ═══════════════════════════════════════════════════════
        
        from bot import bot, dp, main as bot_main
        from config import TELEGRAM_TOKEN
        
        logger.info("📱 راه‌اندازی ربات تلگرام...")
        
        # بررسی اتصال به تلگرام
        bot_info = await bot.get_me()
        logger.info(f"✅ ربات تلگرام متصل شد: @{bot_info.username}")
        
        # ═══════════════════════════════════════════════════════
        # 🌐 راه‌اندازی سرور Webhook
        # ═══════════════════════════════════════════════════════
        
        from webhook_server import app
        from config import WEBHOOK_PORT
        import uvicorn
        
        logger.info(f"🌐 راه‌اندازی سرور Webhook روی پورت {WEBHOOK_PORT}...")
        
        # پیکربندی uvicorn
        config = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=WEBHOOK_PORT,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # ═══════════════════════════════════════════════════════
        # 🎯 اجرای همزمان
        # ═══════════════════════════════════════════════════════
        
        logger.info("=" * 60)
        logger.info("✅ سیستم آماده است!")
        logger.info("=" * 60)
        logger.info(f"📱 ربات تلگرام: @{bot_info.username}")
        logger.info(f"🌐 سرور Webhook: http://localhost:{WEBHOOK_PORT}/webhook/tradingview")
        logger.info(f"📡 وضعیت سرور: http://localhost:{WEBHOOK_PORT}/health")
        logger.info("=" * 60)
        logger.info("در حال دریافت Alerts از TradingView و پیام‌های تلگرام...")
        logger.info("=" * 60)
        
        # اجرای همزمان ربات و سرور
        # ربات در یک task جداگانه
        bot_task = asyncio.create_task(dp.start_polling(bot))
        
        # سرور uvicorn خودش یک coroutine است
        await server.serve()
        
        # انتظار برای تکمیل (این خط اجرا نمی‌شود تا سرور متوقف شود)
        await bot_task
        
    except KeyboardInterrupt:
        logger.info("⚠️ سیستم متوقف شد (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ خطای بحرانی: {e}")
        raise
    finally:
        logger.info("👋 خداحافظ!")


def run():
    """نقطه ورود برنامه"""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⚠️ برنامه متوقف شد")


if __name__ == "__main__":
    run()
