#!/usr/bin/env python3
"""
اسکریپت راه‌اندازی مجدد ربات با قابلیت‌های جدید SMC
"""

import os
import subprocess
import sys
import time

def restart_bot():
    """راه‌اندازی مجدد ربات"""
    
    print("🔄 شروع راه‌اندازی مجدد ربات...")
    
    # تغییر به دایرکتوری پروژه
    project_dir = "/workspace/ai_chart_analyzer"
    os.chdir(project_dir)
    print(f"📁 در دایرکتوری: {os.getcwd()}")
    
    # بررسی فایل‌های اصلی
    essential_files = ['bot.py', 'config.py', 'requirements.txt', '.env']
    for file in essential_files:
        if os.path.exists(file):
            print(f"✅ {file} موجود است")
        else:
            print(f"❌ {file} موجود نیست!")
    
    # بررسی ماژول‌ها
    modules_dir = "modules"
    if os.path.exists(modules_dir):
        modules = os.listdir(modules_dir)
        print(f"📦 ماژول‌ها: {modules}")
    
    try:
        # تست import ماژول‌ها
        sys.path.append(project_dir)
        from modules.ai_analyzer import ChartAnalyzer
        from modules.leverage_calculator import LeverageCalculator  
        from modules.signal_formatter import SignalFormatter
        print("✅ همه ماژول‌ها با موفقیت import شدند")
        
        # تست سریع format کننده SMC
        test_data = {
            'bias': 'LONG',
            'entry': '1.2500', 
            'sl': '1.2450',
            'tp': '1.2600',
            'confidence': 85,
            'structure': 'روند صعودی قوی',
            'zones': 'اردر بلاک معتبر در 1.2480',
            'momentum': 'RSI مثبت در 45',
            'decision_reasoning': 'سیگنال‌های SMC تایید شده'
        }
        
        formatted_msg = SignalFormatter.format_signal(test_data)
        print("✅ فرمت‌کننده SMC کار می‌کند")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(formatted_msg[:200] + "...")  # نمایش بخشی از خروجی
        print("━━━━━━━━━━━━━━━━━━━━━━━━━")
        
    except Exception as e:
        print(f"❌ خطا در تست ماژول‌ها: {e}")
        return False
    
    try:
        # توقف فرآیندهای قبلی (اگر وجود دارد)
        print("🛑 توقف فرآیندهای قبلی...")
        subprocess.run(['pkill', '-f', 'python bot.py'], capture_output=True)
        time.sleep(2)
        
        # نصب dependencies
        print("📦 بررسی dependencies...")
        subprocess.run(['uv', 'pip', 'install', '-r', 'requirements.txt'], 
                      capture_output=True, text=True)
        
        # راه‌اندازی ربات در پس‌زمینه
        print("🚀 راه‌اندازی ربات...")
        with open('bot_smc_output.log', 'w') as log_file:
            process = subprocess.Popen(['python', 'bot.py'], 
                                     stdout=log_file, 
                                     stderr=subprocess.STDOUT)
        
        print(f"✅ ربات با PID {process.pid} راه‌اندازی شد")
        print("📊 ربات اکنون با قابلیت‌های SMC آماده است!")
        
        # نمایش وضعیت اولیه
        time.sleep(3)
        if os.path.exists('bot_smc_output.log'):
            print("\n📋 وضعیت اولیه:")
            with open('bot_smc_output.log', 'r') as f:
                recent_logs = f.read()[:500]
                print(recent_logs)
        
        return True
        
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی: {e}")
        return False

if __name__ == "__main__":
    success = restart_bot()
    if success:
        print("\n🎉 ربات با موفقیت با قابلیت‌های SMC راه‌اندازی شد!")
        print("📱 ربات آماده دریافت چارت‌ها و ارائه تحلیل‌های حرفه‌ای است")
    else:
        print("\n❌ خطا در راه‌اندازی ربات")