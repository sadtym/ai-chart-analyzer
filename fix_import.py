#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch script to fix lbank_client import issue
"""

# Read the file
with open('/workspace/ai_chart_analyzer/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the import - remove the broken import line
old_code = '''        lbank_symbol = symbol_mapping.get(symbol, f"{symbol}/USDT")
        if "/" not in lbank_symbol:
            lbank_symbol = f"{lbank_symbol}/USDT"

        from modules.lbank_client import lbank_client

        analyzing_msg = await message.answer('''

new_code = '''        lbank_symbol = symbol_mapping.get(symbol, f"{symbol}/USDT")
        if "/" not in lbank_symbol:
            lbank_symbol = f"{lbank_symbol}/USDT"

        analyzing_msg = await message.answer('''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('/workspace/ai_chart_analyzer/bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Import fixed successfully")
else:
    print("❌ Pattern not found")
