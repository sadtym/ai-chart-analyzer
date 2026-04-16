# راهنمای کامل استقرار پروژه در GitHub و Render

این راهنما شما را قدم به قدم از مرحله آپلود پروژه در GitHub تا استقرار آن در Render هدایت می‌کند.

---

## بخش اول: آپلود پروژه در GitHub

### مرحله ۱: ایجاد حساب GitHub

اگر هنوز حساب GitHub ندارید، به آدرس [github.com](https://github.com) بروید و یک حساب رایگان ایجاد کنید.

### مرحله ۲: ایجاد Repository جدید

پس از ورود به حساب GitHub، مراحل زیر را انجام دهید:

1. روی دکمه **+** در گوشه بالا سمت راست صفحه کلیک کنید
2. گزینه **New repository** را انتخاب کنید
3. اطلاعات زیر را وارد کنید:

   - **Repository name**: `ai-chart-analyzer`
   - **Description**: `ربات تلگرام تحلیل چارت ارز دیجیتال با هوش مصنوعی`
   - **Visibility**: گزینه **Public** را انتخاب کنید (برای استفاده رایگان از Render)
   - تیک گزینه **Add a README file** را بردارید (چون فایل README.md از قبل دارید)

4. روی دکمه **Create repository** کلیک کنید

پس از ایجاد، صفحه‌ای باز می‌شود که آدرس repository شما را نشان می‌دهد. آدرس به این شکل خواهد بود:

```
https://github.com/USERNAME/ai-chart-analyzer.git
```

به جای `USERNAME` نام کاربری GitHub شما قرار می‌گیرد.

### مرحله ۳: اتصال پروژه محلی به GitHub

حالا باید پروژه موجود در این سرور را به repository جدید GitHub متصل کنید. دستورات زیر را اجرا کنید:

```bash
cd /workspace/ai_chart_analyzer
git remote add origin https://github.com/USERNAME/ai-chart-analyzer.git
git branch -M main
git push -u origin main
```

پس از اجرای دستور push، سیستم از شما نام کاربری و رمز عبور GitHub سؤال می‌کند. اگر احراز هویت دو مرحله‌ای فعال کرده‌اید، باید یک **Personal Access Token** ایجاد کنید:

1. در GitHub به **Settings** → **Developer settings** → **Personal access tokens** بروید
2. یک token جدید با دسترسی `repo` ایجاد کنید
3. به جای رمز عبور، این token را وارد کنید

### مرحله ۴: بررسی موفقیت آپلود

صفحه repository را در GitHub را رفرش کنید. باید تمام فایل‌های پروژه شامل `bot.py`، `modules/`، `requirements.txt` و سایر فایل‌ها را ببینید.

---

## بخش دوم: استقرار در Render

### مرحله ۱: ایجاد حساب Render

به آدرس [render.com](https://render.com) بروید و با حساب GitHub خود ثبت‌نام کنید.

### مرحله ۲: ایجاد Web Service جدید

1. در داشبورد Render روی **New +** کلیک کنید
2. از منوی باز شده گزینه **Web Service** را انتخاب کنید
3. در صفحه بعد، repository GitHub خود را انتخاب کنید:
   - روی **Connect a GitHub account** کلیک کنید
   - به GitHub اجازه دسترسی دهید
   - repository `ai-chart-analyzer` را پیدا کنید و انتخاب کنید

### مرحله ۳: تنظیمات استقرار

صفحه تنظیمات Web Service را به شکل زیر پر کنید:

| فیلد | مقدار |
|------|-------|
| **Name** | `ai-chart-analyzer` |
| **Region** | `Oregon` (یا نزدیک‌ترین منطقه) |
| **Branch** | `main` |
| **Runtime** | `Python 3.11` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Plan** | `Free` |

### مرحله ۴: تنظیم متغیرهای محیطی

در بخش **Environment Variables** متغیرهای زیر را اضافه کنید:

| نام متغیر | مقدار |
|-----------|-------|
| `TELEGRAM_TOKEN` | توکن ربات تلگرام شما |
| `GEMINI_API_KEY` | کلید API Google Gemini |
| `AI_PROVIDER` | `gemini` |
| `WEBHOOK_URL` | `https://your-app-name.onrender.com/` |
| `LOG_LEVEL` | `INFO` |

برای دریافت این مقادیر:

- **TELEGRAM_TOKEN**: از ربات [@BotFather](https://t.me/BotFather) در تلگرام دریافت کنید
- **GEMINI_API_KEY**: از [Google AI Studio](https://aistudio.google.com) دریافت کنید
- **WEBHOOK_URL**: آدرس کامل اپلیکیشن Render شما (مثال: `https://ai-chart-analyzer.onrender.com/`) - این برای جلوگیری از تداخل با اجرای لوکال استفاده می‌شود

### مرحله ۵: ایجاد سرویس

روی دکمه **Create Web Service** کلیک کنید. Render شروع به build و deploy پروژه می‌کند. این فرآیند معمولاً ۲ تا ۳ دقیقه طول می‌کشد.

### مرحله ۶: بررسی لاگ‌ها

پس از استقرار، می‌توانید در تب **Logs** لاگ‌های سرویس را مشاهده کنید. اگر همه چیز درست پیش رفته باشد، باید پیام‌های زیر را ببینید:

```
✅ از Google Gemini استفاده می‌شود
✅ دیتابیس راه‌اندازی شد
🚀 ربات در حال راه‌اندازی...
✅ ربات متصل شد: @YourBotName
📡 شروع به دریافت پیام‌ها...
```

---

## بخش سوم: استفاده از ربات پس از استقرار

پس از موفقیت‌آمیز بودن استقرار، ربات تلگرام شما باید کار کند:

1. در تلگرام، نام ربات خود را جستجو کنید
2. روی **Start** کلیک کنید
3. نام ارز دیجیتال ارسال کنید (مثلاً `BTC`، `ETH`، `SOL`)

ربات باید ظرف چند ثانیه تحلیل کامل را برای شما ارسال کند.

---

## بخش چهارم: آپدیت پروژه

### آپدیت کد

برای آپدیت پروژه در Render پس از تغییرات:

```bash
cd /workspace/ai_chart_analyzer
git add .
git commit -m "توضیح تغییرات"
git push origin main
```

Render به صورت خودکار تغییرات جدید را شناسایی و مجدداً deploy می‌کند.

### بررسی وضعیت استقرار

در داشبورد Render، وضعیت سرویس را می‌توانید مشاهده کنید:

- **Building**: در حال build
- **Deploying**: در حال استقرار
- **Live**: فعال و در حال کار
- **Idle**: غیرفعال (پس از ۱۵ دقیقه عدم فعالیت در پلن رایگان)

---

## بخش پنجم: عیب‌یابی مشکلات رایج

### مشکل: احراز هویت GitHub ناموفق

اگر هنگام push با خطای احراز هویت مواجه شدید:

```bash
# استفاده از token به جای رمز عبور
git remote set-url origin https://YOUR_TOKEN@github.com/USERNAME/ai-chart-analyzer.git
git push -u origin main
```

### مشکل: Build失败的

لاگ‌های Build را در Render بررسی کنید. مشکلات رایج:

- خطا در فایل `requirements.txt`
- نسخه Python نادرست
- کمبود حافظه

### مشکل: ربات پاسخ نمی‌دهد

1. مطمئن شوید ربات در تلگرام **Start** شده است
2. لاگ‌های Render را بررسی کنید
3. مطمئن شوید `TELEGRAM_TOKEN` درست تنظیم شده
4. بررسی کنید ربات در BotFather فعال باشد

---

## خلاصه دستورات مهم

```bash
# بررسی وضعیت git
git status

# افزودن همه فایل‌ها
git add .

# ایجاد commit
git commit -m "پیام commit"

# آپلود در GitHub
git push origin main

# کلون پروژه
git clone https://github.com/USERNAME/ai-chart-analyzer.git

# دریافت آخرین تغییرات
git pull origin main
```

---

اکنون پروژه شما آماده است. در Render روی آدرس سرویس کلیک کنید تا لاگ‌ها و وضعیت را مشاهده کنید.