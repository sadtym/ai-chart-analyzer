#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch script to fix FRED data fetching
"""

import asyncio
import aiohttp

API_KEY = "350fb036fbc276cc1c2ccea013883a23"
BASE_URL = "https://api.stlouisfed.org/fred"

async def test_fred_fixed():
    """Test with proper parameters"""
    
    # تست با observation_start برای گرفتن داده‌های اخیر
    series_to_test = {
        'FEDFUNDS': 'نرخ بهره فدرال رزرو',
        'M2SL': 'عرضه پول M2',
        'CPIAUCSL': 'شاخص CPI',
        'DTWEXBGS': 'شاخص دلار',
    }
    
    async with aiohttp.ClientSession() as session:
        for series_id, name in series_to_test.items():
            try:
                # استفاده از observation_start برای گرفتن داده‌ها از تاریخ مشخص
                url = f"{BASE_URL}/series/observations"
                params = {
                    'series_id': series_id,
                    'api_key': API_KEY,
                    'file_type': 'json',
                    'observation_start': '2024-01-01',  # شروع از ژانویه 2024
                    'limit': 5
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        observations = data.get('observations', [])
                        if observations:
                            print(f"\n{name} ({series_id}):")
                            # نمایش آخرین داده‌ها (که الان باید جدیدترین باشند)
                            for obs in observations[-5:]:
                                date = obs['date']
                                value = obs['value']
                                print(f"  {date}: {value}")
                    else:
                        print(f"\n{name} ({series_id}): خطا {response.status}")
                        text = await response.text()
                        print(f"  Response: {text[:200]}")
            except Exception as e:
                print(f"\n{name} ({series_id}): خطا - {e}")

if __name__ == "__main__":
    asyncio.run(test_fred_fixed())
