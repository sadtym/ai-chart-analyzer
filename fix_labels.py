#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch to improve macro data presentation
"""

# Read the file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the DXY label to be more accurate
old_dxy = "💵 **شاخص دلار (DXY):**"
new_dxy = "💵 **شاخص دلار (Trade-Weighted):**"

if old_dxy in content:
    content = content.replace(old_dxy, new_dxy)
    print("✅ Updated DXY label")
else:
    print("❌ Could not find DXY label")

# Fix the CPI label
old_cpi = "📊 **شاخص قیمت مصرف‌کننده (CPI):**"
new_cpi = "📊 **شاخص قیمت مصرف‌کننده (CPI):**"

if old_cpi in content:
    content = content.replace(old_cpi, new_cpi)
    print("✅ CPI label OK")
else:
    print("❌ Could not find CPI label")

# Write the fixed file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\\n✅ File updated!")
