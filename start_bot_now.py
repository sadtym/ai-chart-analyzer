#!/usr/bin/env python3
import subprocess
import os
import time

# تغییر به دایرکتوری پروژه
os.chdir('/workspace/ai_chart_analyzer')
print(f"📁 دایرکتوری جاری: {os.getcwd()}")

# بررسی فایل‌های مهم
files_to_check = ['bot.py', 'config.py', '.env']
for file in files_to_check:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} یافت نشد!")

try:
    # اجرای مستقیم ربات
    print("🚀 شروع ربات...")
    
    # ایجاد فایل لاگ جدید
    with open('smc_bot.log', 'w') as log_file:
        log_file.write("=== شروع ربات SMC ===\n")
    
    # اجرای ربات در background
    process = subprocess.Popen(['python', 'bot.py'], 
                             stdout=open('smc_bot.log', 'a'),
                             stderr=subprocess.STDOUT)
    
    print(f"✅ ربات آغاز شد - PID: {process.pid}")
    print("⏳ منتظر اتصال ربات...")
    
    # انتظار برای اتصال
    time.sleep(5)
    
    # بررسی وضعیت لاگ
    if os.path.exists('smc_bot.log'):
        print("\n📊 وضعیت ربات:")
        with open('smc_bot.log', 'r') as f:
            content = f.read()
            print(content[-500:] if len(content) > 500 else content)
    
    print("\n🎉 ربات آماده است!")
    print("📱 حالا می‌توانید چارت ارسال کنید تا تحلیل SMC حرفه‌ای دریافت کنید")
    
except Exception as e:
    print(f"❌ خطا: {e}")

print("\nبرای توقف ربات:")
print(f"pkill -f 'python bot.py'")