"""
ماژول سرور Webhook برای دریافت Alerts از TradingView
این ماژول یک سرور FastAPI راه‌اندازی می‌کند که درخواست‌های HTTP از TradingView را دریافت می‌کند

💡 برای استفاده:
1. این ماژول را اجرا کنید: python webhook_server.py
2. در TradingView یک Alert بسازید و URL را تنظیم کنید
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# بارگذاری تنظیمات
load_dotenv(Path(__file__).parent / ".env")

# اضافه کردن مسیر ماژول‌ها به path
MODULES_DIR = Path(__file__).parent / "modules"
sys.path.insert(0, str(MODULES_DIR))

# ═══════════════════════════════════════════════════════════════
# 📦 وارد کردن کتابخانه‌های مورد نیاز
# ═══════════════════════════════════════════════════════════════

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import TELEGRAM_TOKEN, WEBHOOK_SECRET, AI_PROVIDER
from modules.ai_analyzer import ChartAnalyzer
from modules.signal_formatter import SignalFormatter

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ⚙️ تنظیمات سرور
# ═══════════════════════════════════════════════════════════════

# کلید مخفی برای احراز هویت Webhook
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "my_secure_secret_key_12345")

# پورت سرور
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))

# ═══════════════════════════════════════════════════════════════
# 🏗️ ایجاد اپلیکیشن FastAPI
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="TradingView Webhook Server",
    description="سرور دریافت Alerts از TradingView برای تحلیل هوشمند چارت",
    version="1.0.0"
)

# اضافه کردن CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# 📊 مدل‌های داده برای دریافت Alerts
# ═══════════════════════════════════════════════════════════════

class TradingViewAlert(BaseModel):
    """مدل داده برای Alert TradingView"""
    passphrase: str  # کلید مخفی برای احراز هویت
    telegram_id: int  # شناسه تلگرام کاربر
    symbol: str  # نماد معاملاتی
    price: float  # قیمت فعلی
    timeframe: str  # تایم‌فریم
    condition: str  # شرط Alert
    direction: str  # جهت پیشنهادی (buy/sell)
    chart_url: str = None  # لینک چارت (اختیاری)
    custom_message: str = None  # پیام سفارشی

class AlertResponse(BaseModel):
    """مدل پاسخ به Alert"""
    status: str
    message: str
    alert_id: str = None

# ═══════════════════════════════════════════════════════════════
# 🧠 راه‌اندازی ماژول‌ها
# ═══════════════════════════════════════════════════════════════

try:
    analyzer = ChartAnalyzer()
    formatter = SignalFormatter()
    logger.info("✅ ماژول‌های تحلیلگر راه‌اندازی شدند")
except Exception as e:
    logger.error(f"❌ خطا در راه‌اندازی ماژول‌ها: {e}")
    analyzer = None
    formatter = None

# ذخیره وضعیت پردازش
processing_status = {}

# ═══════════════════════════════════════════════════════════════
# 📡 Endpoint های Webhook
# ═══════════════════════════════════════════════════════════════

@app.post("/webhook/tradingview", response_model=AlertResponse)
async def receive_tradingview_alert(alert: TradingViewAlert, background_tasks: BackgroundTasks):
    """
    دریافت Alert از TradingView
    
    فرمت JSON مورد نیاز در TradingView:
    {
        "passphrase": "کلید_شما",
        "telegram_id": 123456789,
        "symbol": "{{ticker}}",
        "price": {{close}},
        "timeframe": "{{interval}}",
        "condition": "شرط Alert",
        "direction": "buy/sell",
        "chart_url": "{{plot_0}}",
        "custom_message": "پیام سفارشی"
    }
    """
    # بررسی کلید مخفی
    if alert.passphrase != WEBHOOK_SECRET:
        logger.warning(f"⚠️ تلاش برای دسترسی غیرمجاز از IP نامشخص")
        raise HTTPException(status_code=403, detail="کلید احراز هویت نامعتبر است")
    
    # تولید شناسه یکتا برای Alert
    alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    logger.info(f"📨 Alert دریافت شد: {alert.symbol} | تایم‌فریم: {alert.timeframe} | کاربر: {alert.telegram_id}")
    
    # ذخیره اطلاعات Alert
    alert_data = {
        "alert_id": alert_id,
        "telegram_id": alert.telegram_id,
        "symbol": alert.symbol,
        "price": alert.price,
        "timeframe": alert.timeframe,
        "condition": alert.condition,
        "direction": alert.direction,
        "chart_url": alert.chart_url,
        "custom_message": alert.custom_message,
        "received_at": datetime.now().isoformat()
    }
    
    processing_status[alert_id] = {
        "status": "processing",
        "data": alert_data
    }
    
    # پردازش در پس‌زمینه
    background_tasks.add_task(process_alert, alert_id, alert_data)
    
    return AlertResponse(
        status="success",
        message="Alert دریافت شد و در حال پردازش است",
        alert_id=alert_id
    )


@app.get("/webhook/status/{alert_id}")
async def get_alert_status(alert_id: str):
    """دریافت وضعیت پردازش Alert"""
    if alert_id in processing_status:
        return processing_status[alert_id]
    return {"status": "not_found", "message": "Alert یافت نشد"}


@app.get("/health")
async def health_check():
    """بررسی سلامت سرور"""
    return {
        "status": "healthy",
        "service": "TradingView Webhook Server",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """صفحه اصلی سرور"""
    return {
        "service": "TradingView Webhook Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "webhook": "POST /webhook/tradingview",
            "status": "GET /webhook/status/{alert_id}",
            "health": "GET /health"
        },
        "docs": "/docs"
    }

# ═══════════════════════════════════════════════════════════════
# 🧠 تابع پردازش Alert
# ═══════════════════════════════════════════════════════════════

async def process_alert(alert_id: str, alert_data: dict):
    """
    پردازش Alert در پس‌زمینه
    
    این تابع:
    1. اطلاعات Alert را آماده می‌کند
    2. تحلیل هوشمند انجام می‌دهد
    3. نتیجه را به تلگرام ارسال می‌کند
    """
    try:
        logger.info(f"🔄 شروع پردازش Alert: {alert_id}")
        
        # آماده‌سازی داده‌ها برای تحلیل
        analysis_data = prepare_alert_data(alert_data)
        
        # انجام تحلیل
        if analyzer and alert_data.get('chart_url'):
            # اگر لینک چارت وجود دارد، تلاش برای دانلود و تحلیل
            try:
                import requests
                import base64
                
                response = requests.get(alert_data['chart_url'], timeout=10)
                if response.status_code == 200:
                    # بررسی نوع محتوا
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type:
                        # تصویر است - تبدیل به base64
                        image_base64 = base64.b64encode(response.content).decode('utf-8')
                        analysis_result = analyzer.analyze(image_base64)
                        analysis_data['has_image'] = True
                    else:
                        # صفحه HTML است - فقط تحلیل متنی
                        analysis_result = analyze_text_only(analysis_data)
                        analysis_data['has_image'] = False
                else:
                    analysis_result = analyze_text_only(analysis_data)
                    analysis_data['has_image'] = False
            except Exception as e:
                logger.warning(f"⚠️ خطا در دانلود چارت: {e}")
                analysis_result = analyze_text_only(analysis_data)
                analysis_data['has_image'] = False
        else:
            # فقط تحلیل متنی
            analysis_result = analyze_text_only(analysis_data)
            analysis_data['has_image'] = False
        
        # فرمت‌بندی نتیجه
        signal_text = format_alert_signal(alert_data, analysis_result, analysis_data)
        
        # ارسال به تلگرام
        await send_to_telegram(alert_data['telegram_id'], signal_text)
        
        # به‌روزرسانی وضعیت
        processing_status[alert_id]['status'] = 'completed'
        processing_status[alert_id]['result'] = signal_text
        
        logger.info(f"✅ Alert تکمیل شد: {alert_id}")
        
    except Exception as e:
        logger.error(f"❌ خطا در پردازش Alert {alert_id}: {e}")
        processing_status[alert_id]['status'] = 'error'
        processing_status[alert_id]['error'] = str(e)


def prepare_alert_data(alert_data: dict) -> dict:
    """آماده‌سازی داده‌های Alert برای تحلیل"""
    return {
        'symbol': alert_data['symbol'],
        'price': alert_data['price'],
        'timeframe': alert_data['timeframe'],
        'condition': alert_data['condition'],
        'direction': alert_data.get('direction', 'unknown'),
        'custom_message': alert_data.get('custom_message', ''),
        'timestamp': alert_data.get('received_at', '')
    }


def analyze_text_only(data: dict) -> dict:
    """
    تحلیل فقط با استفاده از متن (بدون تصویر)
    
    بر اساس اطلاعات Alert، یک تحلیل سریع SMC انجام می‌دهد
    """
    symbol = data['symbol']
    price = data['price']
    timeframe = data['timeframe']
    condition = data['condition']
    direction = data['direction'].upper()
    
    # تولید تحلیل بر اساس شرط و جهت
    if direction == 'BUY':
        bias = 'Long'
        signal = 'BUY'
        confidence = 75
        structure = f"هشدار خرید برای {symbol} در قیمت {price}. شرط: {condition}"
        zones = f"ناحیه ورود: {price}. منتظر تأیید SMC باشید."
        momentum = "بر اساس Alert TradingView، مومنتوم صعودی تشخیص داده شده"
    elif direction == 'SELL':
        bias = 'Short'
        signal = 'SELL'
        confidence = 75
        structure = f"هشدار فروش برای {symbol} در قیمت {price}. شرط: {condition}"
        zones = f"ناحیه ورود: {price}. منتظر تأیید SMC باشید."
        momentum = "بر اساس Alert TradingView، مومنتوم نزولی تشخیص داده شده"
    else:
        bias = 'Range'
        signal = 'WAIT'
        confidence = 50
        structure = f"هشدار برای {symbol} - جهت نامشخص"
        zones = "منتظر روشن شدن جهت باشید"
        momentum = "مومنتوم نامشخص"
    
    return {
        'bias': bias,
        'signal': signal,
        'confidence': confidence,
        'entry': str(price),
        'sl': 'N/A',
        'tp': 'N/A',
        'structure': structure,
        'zones': zones,
        'momentum': momentum,
        'decision_reasoning': f"تحلیل خودکار از Alert TradingView: {condition}",
        'timeframe': timeframe,
        'leverage_recommendation': 10,
        'leverage_reasoning': 'تحلیل سریع - اهرم پیشنهادی میانه',
        'risk_warning': '⚠️ این تحلیل بر اساس Alert است. لطفاً چارت را بررسی کنید',
        'is_alert': True
    }


def format_alert_signal(alert_data: dict, analysis_result: dict, extra_data: dict = None) -> str:
    """فرمت‌بندی سیگنال Alert برای ارسال به تلگرام"""
    
    # انتخاب ایموجی بر اساس جهت
    direction = analysis_result.get('signal', '').upper()
    if direction == 'BUY':
        emoji = '📈'
        direction_text = 'BUY'
        color = '🟢'
    elif direction == 'SELL':
        emoji = '📉'
        direction_text = 'SELL'
        color = '🔴'
    else:
        emoji = '⚖️'
        direction_text = 'WAIT'
        color = '🟡'
    
    # بررسی وجود تصویر
    has_image = extra_data.get('has_image', False) if extra_data else False
    image_note = "📊 همراه با تصویر چارت" if has_image else "📝 تحلیل سریع (بدون تصویر)"
    
    # ساخت پیام
    message = f"""{emoji} **{direction_text}** | 🎯 اعتماد: {analysis_result.get('confidence', 0)}%
{color} **TradingView Alert**

🔔 **هشدار معاملاتی**
📊 نماد: **{alert_data['symbol']}**
💰 قیمت: `{alert_data['price']}`
⏰ تایم‌فریم: `{alert_data['timeframe']}`
📋 شرط: {alert_data['condition']}

{image_note}

━━━━━━━━━━━━━━━━━━━
📊 **ساختار بازار:**
{analysis_result.get('structure', 'نامشخص')}

🎯 **نواحی کلیدی:**
{analysis_result.get('zones', 'شناسایی نشد')}

⚡ **مومنتوم:**
{analysis_result.get('momentum', 'نامشخص')}

━━━━━━━━━━━━━━━━━━━
🧠 **دلیل تصمیم‌گیری:**
{analysis_result.get('decision_reasoning', 'تحلیل خودکار از Alert')}

{analysis_result.get('risk_warning', '⚠️ مدیریت ریسک ضروری')}
━━━━━━━━━━━━━━━━━━━
    """.strip()
    
    return message


async def send_to_telegram(chat_id: int, text: str):
    """ارسال پیام به تلگرام"""
    try:
        from aiogram import Bot
        
        bot_instance = Bot(token=TELEGRAM_TOKEN)
        await bot_instance.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        logger.info(f"✅ پیام به تلگرام ارسال شد: chat_id={chat_id}")
        
    except ImportError:
        logger.error("❌ aiogram نصب نیست! نمی‌توان پیام ارسال کرد")
    except Exception as e:
        logger.error(f"❌ خطا در ارسال به تلگرام: {e}")

# ═══════════════════════════════════════════════════════════════
# 🚀 تابع اصلی برای اجرای سرور
# ═══════════════════════════════════════════════════════════════

def run_server():
    """اجرای سرور Webhook"""
    logger.info("🚀 راه‌اندازی سرور Webhook...")
    logger.info(f"📡 پورت: {WEBHOOK_PORT}")
    logger.info(f"🔐 کلید احراز هویت: {WEBHOOK_SECRET[:8]}...")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=WEBHOOK_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
