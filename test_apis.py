#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test CoinGecko and DeFiLlama APIs
"""

import asyncio
import aiohttp

async def test_apis():
    """Test CoinGecko and DeFiLlama APIs"""
    
    print("=== Testing CoinGecko ===\\n")
    
    # Test CoinGecko - Get coin data
    async with aiohttp.ClientSession() as session:
        # Try different coin IDs for ETH
        coin_ids = ['ethereum', 'eth', 'weth']
        
        for coin_id in coin_ids:
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                params = {
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false',
                    'sparkline': 'false'
                }
                
                async with session.get(url, params=params) as response:
                    print(f"CoinGecko {coin_id}: Status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        market_data = data.get('market_data', {})
                        mcap = market_data.get('market_cap', {}).get('usd', 0)
                        volume = market_data.get('total_volume', {}).get('usd', 0)
                        print(f"  Market Cap: ${mcap/1e9:.2f}B")
                        print(f"  Volume: ${volume/1e9:.2f}B")
                        break
                    else:
                        text = await response.text()[:200]
                        print(f"  Error: {text}")
            except Exception as e:
                print(f"  Exception: {e}")
    
    print("\\n=== Testing DeFiLlama ===\\n")
    
    # Test DeFiLlama - Global TVL
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.llama.fi/tvl") as response:
                print(f"DeFiLlama TVL: Status {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if data:
                        tvl = data[-1].get('totalLiquidityUSD', 0)
                        print(f"  Total TVL: ${tvl/1e9:.2f}B")
    except Exception as e:
        print(f"  Exception: {e}")
    
    print("\\n=== Testing CoinGecko Global ===\\n")
    
    # Test CoinGecko - Global data
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/global") as response:
                print(f"CoinGecko Global: Status {response.status}")
                if response.status == 200:
                    data = await response.json()
                    data_dict = data.get('data', {})
                    print(f"  Total Market Cap: ${data_dict.get('total_market_cap', {}).get('usd', 0)/1e12:.2f}T")
    except Exception as e:
        print(f"  Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_apis())
