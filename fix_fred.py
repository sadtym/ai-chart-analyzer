#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch script to fix FRED data fetching in fundamental_data.py
"""

# Read the file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Change observation_end to observation_start in fetch_series
old_fetch = '''    async def fetch_series(self, series_id: str) -> Optional[float]:
        """دریافت آخرین مقدار یک سری"""
        try:
            url = f"{self.BASE_URL}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'observation_end': datetime.now().strftime('%Y-%m-%d'),
                'limit': 2
            }'''

new_fetch = '''    async def fetch_series(self, series_id: str) -> Optional[Tuple[float, float]]:
        """دریافت آخرین مقدار یک سری (بازگشت: مقدار فعلی، مقدار قبلی)"""
        try:
            url = f"{self.BASE_URL}/series/observations"
            # استفاده از observation_start برای گرفتن داده‌های اخیر
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'observation_start': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'limit': 3
            }'''

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)
    print("✅ Fix 1: Updated fetch_series parameters")
else:
    print("❌ Fix 1: Could not find old fetch_series code")

# Fix 2: Add timedelta import if not present
if 'from datetime import datetime' in content:
    content = content.replace(
        'from datetime import datetime',
        'from datetime import datetime, timedelta'
    )
    print("✅ Fix 2: Added timedelta import")
else:
    print("❌ Fix 2: Could not find datetime import")

# Write the fixed file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ File updated. Now let me also update the CPI calculation...")
