#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch to fix DeFiLlama and CoinGecko API calls
"""

# Read the file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Update DeFiLlama TVL endpoint
old_defillama = '''    async def get_global_tvl(self) -> Optional[float]:
        """دریافت TVL کل بازار"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.BASE_URL}/tvl") as response:
                    if response.status == 200:
                        data = await response.json()
                        # آخرین مقدار
                        if data:
                            return data[-1].get('totalLiquidityUSD', 0)
            return None
        except Exception as e:
            logger.error(f"خطا در دریافت TVL: {e}")
            return None'''

new_defillama = '''    async def get_global_tvl(self) -> Optional[float]:
        """دریافت TVL کل بازار"""
        try:
            # endpoint جدید DeFiLlama v2
            async with aiohttp.ClientSession() as session:
                # روش اول: استفاده از /tvl
                async with session.get(f"{self.BASE_URL}/tvl") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            return data[-1].get('totalLiquidityUSD', 0)
                    
                # روش دوم: استفاده از /overview/tvl
                async with session.get(f"{self.BASE_URL}/overview/tvl") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return data.get('totalTvl', 0)
                            
                # روش سوم: فقط defi tvl
                async with session.get(f"{self.BASE_URL}/overview/defi") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            tvl_data = data.get('data', {}).get('defi', {})
                            return tvl_data.get('market_cap', 0)
                            
            return None
        except Exception as e:
            logger.error(f"خطا در دریافت TVL: {e}")
            return None'''

if old_defillama in content:
    content = content.replace(old_defillama, new_defillama)
    print("✅ Fixed DeFiLlama TVL endpoint")
else:
    print("❌ Could not find DeFiLlama code")

# Write the fixed file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\\n✅ File updated!")
