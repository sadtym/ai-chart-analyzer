#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch script to fix data formatting issues
"""

# Read the file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Update format_macro_message for better formatting
old_format = '''    def format_macro_message(self, macro: MacroData) -> str:
        """فرمت‌بندی پیام داده‌های کلان"""
        if not macro or macro.interest_rate == 0:
            return "❌ داده‌های کلان اقتصادی در دسترس نیست"
        
        sentiment, description = macro.get_sentiment()
        
        emoji_map = {
            "صعودی": "📈",
            "نزولی": "📉",
            "خنثی": "⚖️"
        }
        
        message = (
            f"{emoji_map.get(sentiment, '⚖️')} وضعیت کلان اقتصادی\n"
            f"{'─' * 30}\n\n"
            f"🏦 **نرخ بهره فدرال رزرو:** {macro.interest_rate:.2f}%\n"
            f"   تغییر ماهانه: {macro.interest_rate_change:+.2f}%\n\n"
            f"📊 **نرخ تورم (CPI):** {macro.cpi:.2f}%\n"
            f"   تغییر سالانه: {macro.cpi_change:+.2f}%\n\n"
            f"💵 **شاخص دلار (DXY):** {macro.dxy:.2f}\n"
            f"   تغییر: {macro.dxy_change:+.2f}%\n\n"
            f"💰 **عرضه پول (M2):** ${macro.m2_money_supply:,.0f}T\n"
            f"   تغییر ماهانه: {macro.m2_change:+.2f}%\n\n"
            f"{'─' * 30}\n"
            f"🎯 **احساس کلی:** {sentiment}\n"
            f"💡 {description}\n"
            f"🕐 آخرین به‌روزرسانی: {macro.last_updated}"
        )
        
        return message'''

new_format = '''    def format_macro_message(self, macro: MacroData) -> str:
        """فرمت‌بندی پیام داده‌های کلان"""
        if not macro or macro.interest_rate == 0:
            return "❌ داده‌های کلان اقتصادی در دسترس نیست"
        
        sentiment, description = macro.get_sentiment()
        
        emoji_map = {
            "صعودی": "📈",
            "نزولی": "📉",
            "خنثی": "⚖️"
        }
        
        # فرمت‌بندی M2 (میلیارد دلار -> تریلیون دلار)
        m2_trillion = macro.m2_money_supply / 1000  # تبدیل به تریلیون
        
        # فرمت‌بندی CPI (شاخص)
        cpi_index = macro.cpi if macro.cpi > 100 else macro.cpi * 100
        
        message = (
            f"{emoji_map.get(sentiment, '⚖️')} وضعیت کلان اقتصادی\\n"
            f"{'─' * 30}\\n\\n"
            f"🏦 **نرخ بهره فدرال رزرو:** {macro.interest_rate:.2f}%\\n"
            f"   تغییر ماهانه: {macro.interest_rate_change:+.2f}%\\n\\n"
            f"📊 **شاخص قیمت مصرف‌کننده (CPI):** {cpi_index:.1f}\\n"
            f"   (نرخ تورم سالانه: {macro.cpi_change:+.2f}%)\\n\\n"
            f"💵 **شاخص دلار (DXY):** {macro.dxy:.2f}\\n"
            f"   تغییر: {macro.dxy_change:+.2f}%\\n\\n"
            f"💰 **عرضه پول (M2):** ${m2_trillion:,.1f}T\\n"
            f"   تغییر ماهانه: {macro.m2_change:+.2f}%\\n\\n"
            f"{'─' * 30}\\n"
            f"🎯 **احساس کلی:** {sentiment}\\n"
            f"💡 {description}\\n"
            f"🕐 آخرین به‌روزرسانی: {macro.last_updated}"
        )
        
        return message'''

if old_format in content:
    content = content.replace(old_format, new_format)
    print("✅ Fix: Updated format_macro_message")
else:
    print("❌ Could not find format_macro_message")

# Write the fixed file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\\n✅ File updated!")
