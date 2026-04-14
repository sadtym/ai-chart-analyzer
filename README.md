# 🤖 ربات تحلیل هوشمند چارت تلگرام + TradingView Integration

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![aiogram](https://img.shields.io/badge/aiogram-3.x-purple.svg)
![Gemini](https://img.shields.io/badge/Google-Gemini-red.svg)
![TradingView](https://img.shields.io/badge/TradingView-Webhook-orange.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Deploy](https://img.shields.io/badge/Deploy-Render-46e198.svg)

**تحلیل خودکار چارت‌های تکنیکال با هوش مصنوعی + اتصال TradingView**

[ویژگی‌ها](#-ویژگیها) • [نصب](#-نصب-و-راهاندازی) • [Render](#️-استقرار-در-render) • [TradingView](#-راهاندازی-tradingview-alerts) • [ساختار پروژه](#-ساختار-پروژه)

</div>

---

## 📋 درباره پروژه

این ربات تلگرامی با استفاده از هوش مصنوعی چندوجهی (Vision LLM) قادر است تصاویر چارت‌های تکنیکال را تحلیل کند و سیگنال‌های معاملاتی حرفه‌ای تولید نماید. پروژه ترکیبی از فناوری‌های پیشرفته بینایی رایانه‌ای، مدل‌های زبانی و اتوماسیون پیام‌رسان است.

### ✨ ویژگی‌ها

- 📸 **دریافت تصویر چارت**: پشتیبانی از ارسال عکس از تمام پلتفرم‌های معاملاتی
- 🧠 **تحلیل SMC**: تحلیل پیشرفته با مفاهیم Smart Money Concepts
- 🔄 **مولتی تایم‌فریم**: تحلیل همزمان ساختار تایم‌فریم‌های مختلف
- 🤖 **هوش مصنوعی**: استفاده از Google Gemini (کاملاً رایگان!)
- 📊 **تشخیص خودکار**: شناسایی نماد، تایم‌فریم و روند قیمت
- 🎯 **نقاط ورود و خروج**: تعیین دقیق Entry، Stop Loss و Take Profit
- 📈 **محاسبه RR**: نسبت ریسک به ریوارد معامله
- 💰 **مدیریت سرمایه**: محاسبه حجم معامله و اهرم مناسب
- 🌐 **TradingView Alerts**: دریافت خودکار هشدارها از TradingView
- ☁️ **استقرار در Render**: پشتیبانی کامل از استقرار در پلتفرم Render

---

## 🛠️ نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.10 یا بالاتر
- توکن ربات تلگرام
- کلید API Google Gemini (کاملاً رایگان!)
- حساب GitHub برای استقرار در Render

### مراحل نصب

1. **کلون پروژه:**
```bash
git clone https://github.com/yourusername/ai-chart-analyzer.git
cd ai-chart-analyzer
```

2. **ایجاد محیط مجازی:**
```bash
python -m venv venv
source venv/bin/activate  # در ویندوز: venv\Scripts\activate
```

3. **نصب پیش‌نیازها:**
```bash
pip install -r requirements.txt
```

4. **تنظیم متغیرهای محیطی:**
```bash
cp .env.example .env
# ویرایش فایل .env و تنظیم مقادیر
```

### اجرای ربات

**فقط ربات تلگرام:**
```bash
python bot.py
```

**همراه با سرور Webhook (برای TradingView):**
```bash
python run_combined.py
```

### در ویندوز:
```cmd
set TELEGRAM_TOKEN=your_telegram_bot_token
set GEMINI_API_KEY=your_gemini_api_key
python bot.py
```

---

## ☁️ استقرار در Render

### روش ۱: Deploy با یک کلیک

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### روش ۲: استقرار دستی

#### پیش‌نیازها
- حساب [Render](https://render.com)
- حساب [GitHub](https://github.com)
- توکن ربات تلگرام از [@BotFather](https://t.me/BotFather)
- کلید API Google Gemini از [Google AI Studio](https://aistudio.google.com)

#### مراحل

**1. آماده‌سازی پروژه برای GitHub:**

فایل‌های پروژه را به GitHub push کنید:
```bash
cd ai-chart-analyzer
git init
git add .
git commit -m "Initial commit - AI Chart Analyzer Bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-chart-analyzer.git
git push -u origin main
```

**2. تنظیم در Render:**

- وارد حساب [Render](https://render.com) شوید
- روی **New +** → **Web Service** کلیک کنید
- Repository GitHub خود را انتخاب کنید

**3. تنظیمات استقرار:**

| تنظیم | مقدار |
|-------|------|
| **Name** | `ai-chart-analyzer` |
| **Region** | Oregon (یا نزدیک‌ترین) |
| **Branch** | `main` |
| **Runtime** | `Python 3.11` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Free Tier** | ✅ فعال |

**4. تنظیم Environment Variables:**

در بخش Environment متغیرهای زیر را اضافه کنید:

| متغیر | مقدار |
|-------|------|
| `TELEGRAM_TOKEN` | توکن ربات تلگرام شما |
| `GEMINI_API_KEY` | کلید API Google Gemini |
| `AI_PROVIDER` | `gemini` |
| `LOG_LEVEL` | `INFO` |

**5. استقرار:**

روی **Create Web Service** کلیک کنید و منتظر استقرار بمانید (2-3 دقیقه).

**6. بررسی لاگ‌ها:**

پس از استقرار، در تب Logs می‌توانید لاگ‌های ربات را مشاهده کنید.

### 📝 نکات مهم برای Render

- **Free Tier**: 750 ساعت/ماه - برای تست کافی است
- **Sleep Mode**: Render بعد از 15 دقیقه عدم فعالیت، سرویس را به حالت خواب می‌برد
- **Cold Start**: اولین درخواست بعد از خواب، 30-60 ثانیه طول می‌کشد
- **Webhook**: برای استفاده از Webhook در Render، باید از Web Service با پلن پولی استفاده کنید یا از Cron Jobs استفاده کنید

### 🔄 آپدیت پروژه در Render

```bash
# پس از تغییرات در کد
git add .
git commit -m "Your update message"
git push origin main
```

Render به صورت خودکار rebuild و deploy می‌شود.

---

## 📱 نحوه استفاده

### ایجاد ربات تلگرام

1. به BotFather (@BotFather) در تلگرام بروید
2. دستور `/newbot` را ارسال کنید
3. نام و نام کاربری ربات را انتخاب کنید
4. توکن دریافتی را کپی کنید

### اجرای ربات

```bash
python bot.py
```

### ارسال چارت

1. ربات را در تلگرام پیدا کنید و استارت کنید
2. عکس چارت قیمت را ارسال کنید
3. ظرف 10-20 ثانیه تحلیل کامل دریافت کنید

### ارسال نام ارز

برای دریافت تحلیل خودکار، نام ارز دیجیتال را ارسال کنید:
- `BTC` - تحلیل بیت‌کوین
- `ETH` - تحلیل اتریوم
- `SOL` - تحلیل سولانا

---

## 🌐 راه‌اندازی TradingView Alerts

این قابلیت به شما اجازه می‌دهد هشدارهای TradingView را به صورت خودکار دریافت کنید و ربات فوراً تحلیل SMC انجام دهد.

### مرحله ۱: دریافت Telegram ID

برای اینکه Alerts به اکانت تلگرام شما ارسال شوند، Telegram ID خود را از ربات `@userinfobot` دریافت کنید.

### مرحله ۲: ایجاد Alert در TradingView

۱. وارد TradingView شوید
۲. نماد مورد نظر را انتخاب کنید
۳. روی زنگوله (Alert) کلیک کنید
۴. شرط مورد نظر را تنظیم کنید
۵. در قسمت **Notifications**، گزینه **Webhook URL** را فعال کنید

### مرحله ۳: تنظیم Webhook URL

آدرس Webhook به این صورت است:
```
http://YOUR_RENDER_APP_NAME.onrender.com/webhook/tradingview
```

**مثال:**
```
http://ai-chart-analyzer.onrender.com/webhook/tradingview
```

### مرحله ۴: تنظیم JSON Payload

در قسمت **Message** یا **JSON Payload**، فرمت زیر را وارد کنید:

```json
{
    "passphrase": "کلید_شما_از_فایل_env",
    "telegram_id": "your_telegram_id",
    "symbol": "{{ticker}}",
    "price": {{close}},
    "timeframe": "{{interval}}",
    "condition": "Price crossed Resistance",
    "direction": "buy",
    "chart_url": "{{plot_0}}"
}
```

### متغیرهای TradingView قابل استفاده:

| متغیر | توضیح |
|-------|-------|
| `{{ticker}}` | نماد معاملاتی |
| `{{close}}` | قیمت بسته شدن |
| `{{high}}` | بالاترین قیمت |
| `{{low}}` | پایین‌ترین قیمت |
| `{{volume}}` | حجم معاملات |
| `{{interval}}` | تایم‌فریم |
| `{{time}}` | زمان |
| `{{plot_0}}` | اولین نمودار (معمولاً لینک چارت) |

### نکات مهم برای Webhook:

- **سرور**: برای Webhook در Render، باید پلن پولی داشته باشید یا از روش جایگزین استفاده کنید
- **SSL**: استفاده از SSL پیشنهاد می‌شود (در پلن پولی Render موجود است)
- **کلید امنیتی**: `WEBHOOK_SECRET` را حتماً تغییر دهید

---

## 📁 ساختار پروژه

```
ai_chart_analyzer/
├── bot.py                    # فایل اصلی ربات تلگرام
├── webhook_server.py         # سرور Webhook برای TradingView
├── run_combined.py           # اجرای همزمان ربات و Webhook
├── config.py                 # تنظیمات پروژه
├── requirements.txt          # پیش‌نیازها
├── .env.example              # نمونه تنظیمات
├── .gitignore                # فایل‌های رد شده از Git
├── README.md                 # مستندات
├── modules/
│   ├── ai_analyzer.py        # تحلیل با هوش مصنوعی
│   ├── ai_signal_generator.py # تولید سیگنال با AI
│   ├── mtf_market_scanner.py  # اسکنر بازار چندتایم‌فریم
│   ├── smc_analyzer.py        # تحلیل SMC
│   ├── fundamental_analyzer.py # تحلیل فاندامنتال
│   ├── macro_analyzer.py      # تحلیل ماکرو اقتصادی
│   ├── signal_formatter.py    # فرمت‌بندی سیگنال
│   ├── image_processor.py    # پردازش تصویر
│   ├── leverage_calculator.py # محاسبه اهرم
│   ├── capital_manager.py     # مدیریت سرمایه
│   └── chart_annotator.py    # رسم علامت روی چارت
├── charts/                   # پوشه تصاویر موقت
├── data/                     # پوشه داده‌ها و لاگ‌ها
├── database/                 # پوشه دیتابیس
└── .env                      # متغیرهای محیطی (ایجاد شود)
```

---

## ⚙️ تنظیمات قابل تغییر

در فایل `config.py` می‌توانید موارد زیر را تغییر دهید:

| پارامتر | توضیح | پیش‌فرض |
|---------|-------|---------|
| `IMAGE_MAX_WIDTH` | حداکثر عرض تصویر | 1024 |
| `IMAGE_QUALITY` | کیفیت فشرده‌سازی | 85 |
| `GEMINI_MODEL` | مدل هوش مصنوعی | gemini-1.5-flash |
| `LOG_LEVEL` | سطح لاگینگ | INFO |

### تغییر مدل هوش مصنوعی

```python
# در config.py یا متغیرهای محیطی
GEMINI_MODEL = "gemini-1.5-flash"    # سریع و رایگان
GEMINI_MODEL = "gemini-1.5-pro"     # دقیق‌تر
```

---

## 🎨 نمونه خروجی

```
🚀 🎯 سیگنال معاملاتی | #BTCUSD

📊 اطلاعات معامله:
• نماد: BTCUSD
• تایم‌فریم: 4H
• جهت: 📈 خرید (LONG)

━━━━━━━━━━━━━━━━━━━

🟢 🎯 نقطه ورود:
64,200 - 64,500

❌ ❌ حد ضرر:
63,800

💰 💰 اهداف قیمتی:
├ 🎯 TP1: 65,500
└ 🎯 TP2: 66,800

━━━━━━━━━━━━━━━━━━━

📈 تحلیل: قیمت به سطح حمایتی ماژور برخورد کرده
         و الگوی چکش تشکیل شده است.

⚡ RR: 1:2.5
• اعتماد تحلیل: 85%

━━━━━━━━━━━━━━━━━━━

⚠️ هشدار: این تحلیل فقط جنبه اطلاعاتی دارد.
🤖 تولید شده توسط AI Chart Analyzer
```

---

## 🚨 عیب‌یابی

### خطای توکن تلگرام
```
❌ توکن تلگرام تنظیم نشده است!
```
**راه‌حل**: توکن را در متغیر محیطی `TELEGRAM_TOKEN` تنظیم کنید.

### خطای Gemini API
```
❌ کلید Gemini API تنظیم نشده است!
```
**راه‌حل**: کلید API را در متغیر محیطی `GEMINI_API_KEY` تنظیم کنید.

### خطای استقرار در Render
```
Build failed
```
**راه‌حل**:
- بررسی کنید `requirements.txt` صحیح باشد
- مطمئن شوید Python version در Render درست تنظیم شده
- لاگ‌های Build را بررسی کنید

### خطای تحلیل
```
❌ خطا در تحلیل چارت
```
**راه‌حل**: 
- کیفیت تصویر را افزایش دهید
- مطمئن شوید محورهای قیمت واضح هستند
- از چارت با پس‌زمینه روشن استفاده کنید

### خطای Webhook
```
❌ کلید احراز هویت نامعتبر است
```
**راه‌حل**:
- بررسی کنید `WEBHOOK_SECRET` در Alert و فایل .env یکسان باشد
- فرمت JSON را بررسی کنید

### ربات در Render پاسخ نمی‌دهد
**راه‌حل**:
- مطمئن شوید ربات در تلگرام استارت شده
- لاگ‌های Render را بررسی کنید
- مطمئن شوید `TELEGRAM_TOKEN` درست تنظیم شده

---

## 📝 نکات مهم

1. **هزینه API**: استفاده از Google Gemini کاملاً رایگان است!
2. **دقت تحلیل**: هوش مصنوعی ممکن است گاهی اشتباه بخواند - همیشه بررسی کنید
3. **مدیریت ریسک**: این ربات فقط جنبه کمکی دارد - مسئولیت معاملات با شماست
4. **TradingView Alerts**: برای استفاده از این قابلیت، باید سرور با IP ثابت داشته باشید
5. **امنیت Webhook**: کلید `WEBHOOK_SECRET` را حتماً تغییر دهید
6. **استقرار در Render**: از پلن Free برای تست استفاده کنید

---

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

---

## 👤 نویسنده

**MiniMax Agent** - توسعه‌دهنده پروژه

---

<div align="center">

🌟 اگر این پروژه برایتان مفید بود، لطفاً ستاره⭐ بدهید!

</div>