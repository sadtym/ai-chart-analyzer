#!/usr/bin/env python3
import os
import subprocess
import sys

# Change to project directory
os.chdir('/workspace/ai_chart_analyzer')

# Check if dependencies exist and install if needed
try:
    print("🔧 نصب dependencies...")
    result = subprocess.run(['uv', 'pip', 'install', '-r', 'requirements.txt'], 
                          capture_output=True, text=True, timeout=60)
    print("✅ Dependencies نصب شد")
except Exception as e:
    print(f"⚠️ خطا در نصب dependencies: {e}")

# Kill any existing bot processes
try:
    subprocess.run(['pkill', '-f', 'python bot.py'], capture_output=True)
    print("🛑 فرآیندهای قبلی متوقف شد")
except:
    pass

# Start the bot
try:
    print("🚀 راه‌اندازی ربات با SMC...")
    process = subprocess.Popen(['nohup', 'python', 'bot.py'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.STDOUT)
    
    print(f"✅ ربات با PID {process.pid} آغاز شد")
    print("📱 ربات آماده دریافت چارت‌ها با تحلیل SMC!")
    
except Exception as e:
    print(f"❌ خطا در راه‌اندازی: {e}")