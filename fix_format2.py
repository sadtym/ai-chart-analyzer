#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch script to fix format_macro_message
"""

# Read the file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The old problematic lines
old_cpi = '📊 **نرخ تورم (CPI):** {macro.cpi:.2f}%\\n"\n            f"   تغییر سالانه: {macro.cpi_change:+.2f}%'
old_m2 = '💰 **عرضه پول (M2):** ${macro.m2_money_supply:,.0f}T'

# New corrected lines
new_cpi = '📊 **شاخص قیمت مصرف‌کننده (CPI):** {macro.cpi:.1f}\\n"\n            f"   (نرخ تورم سالانه: {macro.cpi_change:+.2f}%)'
new_m2 = '💰 **عرضه پول (M2):** ${macro.m2_money_supply/1000:.1f}T'

if old_cpi in content:
    content = content.replace(old_cpi, new_cpi)
    print("✅ Fixed CPI formatting")
else:
    print("❌ Could not find CPI line")

if old_m2 in content:
    content = content.replace(old_m2, new_m2)
    print("✅ Fixed M2 formatting")
else:
    print("❌ Could not find M2 line")

# Write the fixed file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\\n✅ File updated!")
