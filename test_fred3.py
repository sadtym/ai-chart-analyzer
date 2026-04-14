#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test different FRED series for more accurate data
"""

import asyncio
import aiohttp

API_KEY = "350fb036fbc276cc1c2ccea013883a23"
BASE_URL = "https://api.stlouisfed.org/fred"

async def test_all_series():
    """Test all relevant FRED series"""
    
    # سری‌های مختلف برای تست
    test_series = {
        # نرخ بهره
        'FEDFUNDS': ('نرخ بهره فدرال رزرو', 'https://fred.stlouisfed.org/series/FEDFUNDS'),
        'FEDRATE': ('نرخ بهره', 'https://fred.stlouisfed.org/series/FEDFUND'),
        
        # DXY
        'DTWEXBGS': ('شاخص دلار (Trade Weighted)', 'https://fred.stlouisfed.org/series/DTWEXBGS'),
        'DTWEXB': ('شاخص دلار ساده', 'https://fred.stlouisfed.org/series/DTWEXB'),
        
        # M2
        'M2SL': ('عرضه پول M2 (میلیارد)', 'https://fred.stlouisfed.org/series/M2SL'),
        'WM2NS': ('عرضه پول M2 (هفتگی)', 'https://fred.stlouisfed.org/series/WM2NS'),
    }
    
    async with aiohttp.ClientSession() as session:
        for series_id, (name, url) in test_series.items():
            try:
                params = {
                    'series_id': series_id,
                    'api_key': API_KEY,
                    'file_type': 'json',
                    'observation_start': '2025-01-01',
                    'limit': 3
                }
                
                async with session.get(f"{BASE_URL}/series/observations", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        observations = data.get('observations', [])
                        if observations:
                            obs = observations[-1]
                            value = obs['value']
                            date = obs['date']
                            print(f"{name} ({series_id}): {value} ({date})")
                    else:
                        print(f"{name} ({series_id}): خطا {response.status}")
            except Exception as e:
                print(f"{name} ({series_id}): خطا - {e}")

if __name__ == "__main__":
    asyncio.run(test_all_series())
