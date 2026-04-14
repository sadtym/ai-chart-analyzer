#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to check FRED data
"""

import asyncio
import aiohttp

API_KEY = "350fb036fbc276cc1c2ccea013883a23"
BASE_URL = "https://api.stlouisfed.org/fred"

async def test_fred():
    # Test different series
    series_to_test = {
        'FEDFUNDS': 'نرخ بهره فدرال رزرو',
        'FREDFF': 'نرخ بهره فدرال رزرو (دیگر)',
        'M2': 'عرضه پول M2',
        'M2SL': 'عرضه پول M2 (Official)',
        'CPIAUCSL': 'شاخص CPI (خام)',
        'CPILFESL': 'CPI Core',
        'PCEPI': 'شاخص PCE',
        'DTWEXBGS': 'شاخص دلار',
    }
    
    async with aiohttp.ClientSession() as session:
        for series_id, name in series_to_test.items():
            try:
                url = f"{BASE_URL}/series/observations"
                params = {
                    'series_id': series_id,
                    'api_key': API_KEY,
                    'file_type': 'json',
                    'observation_end': '2026-02-01',
                    'limit': 3
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        observations = data.get('observations', [])
                        if observations:
                            print(f"\n{name} ({series_id}):")
                            for obs in observations[-3:]:
                                date = obs['date']
                                value = obs['value']
                                print(f"  {date}: {value}")
                    else:
                        print(f"\n{name} ({series_id}): خطا {response.status}")
            except Exception as e:
                print(f"\n{name} ({series_id}): خطا - {e}")

if __name__ == "__main__":
    asyncio.run(test_fred())
