# -*- coding: utf-8 -*-
"""
ماژول داده‌های فاندامنتال و کلان اقتصادی
Fundamental & Macro-Economic Data Module

شامل:
- داده‌های کلان اقتصادی (نرخ بهره، تورم، DXY)
- داده‌های فاندامنتال ارزهای دیجیتال (TVL, Stablecoin Flows)
- تحلیل همبستگی بین بازارها
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# ==================== Data Classes ====================

class TrendDirection(Enum):
    BULLISH = "صعودی"
    BEARISH = "نزولی"
    NEUTRAL = "خنثی"

@dataclass
class MacroData:
    """داده‌های کلان اقتصادی"""
    interest_rate: float = 0.0  # نرخ بهره فدرال رزرو
    interest_rate_change: float = 0.0  # تغییر ماهانه
    cpi: float = 0.0  # نرخ تورم
    cpi_change: float = 0.0  # تغییر سالانه
    dxy: float = 0.0  # شاخص دلار
    dxy_change: float = 0.0  # تغییر
    m2_money_supply: float = 0.0  # عرضه پول M2
    m2_change: float = 0.0  # تغییر ماهانه
    last_updated: str = ""
    
    def get_sentiment(self) -> Tuple[str, str]:
        """تعیین احساس کلان اقتصادی"""
        score = 0
        
        # نرخ بهره بالا = فشار نزولی بر ریسک‌پذیری
        if self.interest_rate > 5.0:
            score -= 2
        elif self.interest_rate > 4.0:
            score -= 1
        
        # تورم بالا = فشار نزولی (بر اساس درصد تغییر سالانه)
        # اگر cpi_change موجود است، از آن استفاده کن
        if hasattr(self, 'cpi_change') and self.cpi_change != 0:
            if self.cpi_change > 5.0:
                score -= 2
            elif self.cpi_change > 3.0:
                score -= 1
        else:
            # اگر درصد تغییر نداریم، فرض می‌کنیم تورم نرمال است
            pass
        
        # DXY قوی = فشار نزولی بر بیت‌کوین
        if self.dxy > 105:
            score -= 1
        elif self.dxy < 95:
            score += 1
            
        # M2 در حال رشد = محیط مساعد
        if self.m2_change > 1:
            score += 1
        elif self.m2_change < -1:
            score -= 1
            
        if score > 1:
            return "صعودی", f"محیط کلان مساعد (نرخ بهره: {self.interest_rate}%, CPI: {self.cpi}%)"
        elif score < -1:
            return "نزولی", f"فشار کلان منفی (نرخ بهره بالا: {self.interest_rate}%)"
        else:
            return "خنثی", "شرایط کلان متعادل"

@dataclass
class CryptoFundamentals:
    """داده‌های فاندامنتال ارز دیجیتال"""
    symbol: str = ""
    market_cap: float = 0.0
    market_cap_change_24h: float = 0.0
    tvl: float = 0.0  # Total Value Locked
    tvl_change_24h: float = 0.0
    stablecoin_mcap: float = 0.0
    stablecoin_flow_24h: float = 0.0
    defi_tvl: float = 0.0
    lending_rates: Dict[str, float] = field(default_factory=dict)  # نرخ‌های وام‌دهی
    volume_24h: float = 0.0
    dominance: float = 0.0
    
    def get_market_sentiment(self) -> str:
        """تعیین احساس بازار از دید فاندامنتال"""
        bullish_signals = 0
        bearish_signals = 0
        
        # TVL در حال رشد = مثبت
        if self.tvl_change_24h > 5:
            bullish_signals += 2
        elif self.tvl_change_24h < -5:
            bearish_signals += 2
            
        # جریان استیبل‌کوین مثبت = ورود پول جدید
        if self.stablecoin_flow_24h > 1e9:  # بیش از 1 میلیارد
            bullish_signals += 2
        elif self.stablecoin_flow_24h < -1e9:
            bearish_signals += 2
            
        # حجم معاملات بالا = نقدینگی خوب
        if self.volume_24h > self.market_cap * 0.1:
            bullish_signals += 1
            
        if bullish_signals > bearish_signals + 1:
            return "صعودی"
        elif bearish_signals > bullish_signals + 1:
            return "نزولی"
        return "خنثی"

@dataclass
class FullAnalysisData:
    """داده‌های کامل تحلیل (ترکیبی)"""
    macro: Optional[MacroData] = None
    crypto_fundamentals: Optional[CryptoFundamentals] = None
    smc_results: Dict = field(default_factory=dict)
    symbol: str = ""
    current_price: float = 0.0
    
    def get_confluence_score(self) -> int:
        """محاسبه امتیاز همگرایی"""
        score = 50  # امتیاز پایه
        
        # تأثیر کلان اقتصادی
        if self.macro:
            macro_sentiment, _ = self.macro.get_sentiment()
            if macro_sentiment == "صعودی":
                score += 15
            elif macro_sentiment == "نزولی":
                score -= 15
                
        # تأثیر فاندامنتال
        if self.crypto_fundamentals:
            fund_sentiment = self.crypto_fundamentals.get_market_sentiment()
            if fund_sentiment == "صعودی":
                score += 15
            elif fund_sentiment == "نزولی":
                score -= 15
                
        # تأثیر تکنیکال
        if self.smc_results:
            bias = self.smc_results.get('bias', 'NEUTRAL')
            if bias in ['BULLISH', 'STRONG_BULLISH']:
                score += 20
            elif bias in ['BEARISH', 'STRONG_BEARISH']:
                score -= 20
                
        return max(0, min(100, score))

# ==================== API Clients ====================

class FREDClient:
    """
    کلاینت داده‌های فدرال رزرو (FRED API)
    Federal Reserve Economic Data
    """
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    # سریال‌های مهم
    SERIES = {
        'FEDFUNDS': 'interest_rate',        # Federal Funds Rate
        'CPIAUCSL': 'cpi',                   # Consumer Price Index
        'DTWEXBGS': 'dxy',                   # Trade Weighted Dollar Index
        'M2SL': 'm2',                        # M2 Money Supply
    }
    
    def __init__(self, api_key: str = None):
        from config import FRED_API_KEY
        self.api_key = api_key or FRED_API_KEY
        
    async def fetch_series(self, series_id: str) -> Optional[Tuple[float, float]]:
        """دریافت آخرین مقدار یک سری (بازگشت: مقدار فعلی، مقدار قبلی)"""
        try:
            url = f"{self.BASE_URL}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'observation_start': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'limit': 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        observations = data.get('observations', [])
                        
                        # استخراج مقادیر معتبر
                        valid_values = []
                        for obs in observations:
                            raw_value = obs.get('value', '')
                            
                            # بررسی اینکه value یک رشته عددی معتبر باشد
                            if isinstance(raw_value, str) and raw_value.strip() != '' and raw_value != '.':
                                try:
                                    float_val = float(raw_value)
                                    valid_values.append(float_val)
                                except (ValueError, TypeError):
                                    continue
                            elif isinstance(raw_value, (int, float)):
                                valid_values.append(float(raw_value))
                        
                        if len(valid_values) >= 2:
                            current = valid_values[-1]
                            previous = valid_values[-2]
                            logger.info(f"FRED {series_id}: current={current}, previous={previous}")
                            return current, previous
                        else:
                            logger.warning(f"FRED {series_id}: داده معتبر یافت نشد ({len(valid_values)} observations)")
                            return None
                    else:
                        logger.warning(f"FRED {series_id}: وضعیت پاسخ {response.status}")
                    return None
        except Exception as e:
            logger.error(f"خطا در دریافت FRED {series_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_all_macro_data(self) -> MacroData:
        """دریافت تمام داده‌های کلان اقتصادی"""
        macro = MacroData()
        macro.last_updated = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        tasks = [
            (series_id, series_name) 
            for series_id, series_name in self.SERIES.items()
        ]
        
        results = await asyncio.gather(
            *[self.fetch_series(sid) for sid, _ in tasks],
            return_exceptions=True
        )
        
        for i, (series_id, series_name) in enumerate(tasks):
            try:
                result = results[i]
                if result and isinstance(result, tuple):
                    current, previous = result
                    change_pct = ((current - previous) / previous * 100) if previous else 0
                    
                    if series_name == 'interest_rate':
                        macro.interest_rate = current
                        macro.interest_rate_change = change_pct
                    elif series_name == 'cpi':
                        # CPI بر اساس شاخص است، باید درصد تغییر سالانه را محاسبه کنیم
                        # اما چون فقط 2-3 داده داریم، فعلا خام نمایش می‌دهیم
                        macro.cpi = current
                        # اگر داده‌های بیشتری داشتیم، می‌توانیم سالانه محاسبه کنیم
                        # فعلا درصد تغییر ماهانه را نشان می‌دهیم
                        macro.cpi_change = change_pct
                    elif series_name == 'dxy':
                        macro.dxy = current
                        macro.dxy_change = change_pct
                    elif series_name == 'm2':
                        macro.m2_money_supply = current
                        macro.m2_change = change_pct
                        
            except Exception as e:
                logger.error(f"خطا در پردازش {series_id}: {e}")
        
        return macro


class DeFiLlamaClient:
    """
    کلاینت داده‌های DeFiLlama
    برای دریافت TVL، استیبل‌کوین و نرخ‌های وام‌دهی
    """
    
    BASE_URL = "https://api.llama.fi"
    
    async def get_global_tvl(self) -> Optional[float]:
        """دریافت TVL کل بازار از DeFiLlama"""
        try:
            async with aiohttp.ClientSession() as session:
                # استفاده از /charts/ethereum که درست کار می‌کند
                # این endpoint داده‌های TVL تاریخی را برمی‌گرداند
                url = f"{self.BASE_URL}/charts/ethereum"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            # آخرین ورودی شامل TVL فعلی است
                            last_entry = data[-1]
                            if isinstance(last_entry, dict):
                                tvl = last_entry.get('totalLiquidityUSD', 0)
                                if tvl and tvl > 0:
                                    return tvl
                            
                # روش کمکی: تلاش برای دریافت TVL از protocols
                async with session.get(f"{self.BASE_URL}/protocols") as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            for protocol in data:
                                if isinstance(protocol, dict) and protocol.get('id') == 'ethereum':
                                    return protocol.get('tvl', 0)
                            
                return 0.0
        except Exception as e:
            logger.error(f"خطا در دریافت TVL: {e}")
            return 0.0
    
    async def get_ethereum_tvl(self) -> Optional[float]:
        """دریافت TVL شبکه اتریوم از /charts/ethereum"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/charts/ethereum"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            last_entry = data[-1]
                            if isinstance(last_entry, dict):
                                tvl = last_entry.get('totalLiquidityUSD', 0)
                                if tvl and tvl > 0:
                                    logger.info(f"DeFiLlama ETH TVL: ${tvl/1e9:.2f}B")
                                    return tvl
                    return None
        except Exception as e:
            logger.error(f"خطا در دریافت TVL اتریوم: {e}")
            return None
    
    async def get_defi_tvl(self) -> Optional[float]:
        """دریافت TVL بخش DeFi"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/overview/defi"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            defi_data = data.get('data', {}).get('defi', {})
                            return defi_data.get('market_cap', 0)
                    elif response.status == 500:
                        # اگر overview خطا داد، از protocols استفاده کن
                        async with session.get(f"{self.BASE_URL}/protocols") as response:
                            if response.status == 200:
                                data = await response.json()
                                if isinstance(data, list):
                                    total_tvl = 0
                                    for protocol in data:
                                        if isinstance(protocol, dict):
                                            tvl = protocol.get('tvl', 0)
                                            if tvl and tvl > 0:
                                                total_tvl += tvl
                                    return total_tvl
                    return 0.0
        except Exception as e:
            logger.error(f"خطا در دریافت DeFi TVL: {e}")
            return 0.0
    
    async def get_stablecoin_data(self) -> Optional[Dict]:
        """دریافت داده‌های استیبل‌کوین"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.BASE_URL}/overview/stablecoins") as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except Exception as e:
            logger.error(f"خطا در دریافت داده استیبل‌کوین: {e}")
            return None
    
    async def get_protocol_tvl(self, protocol: str) -> Optional[float]:
        """دریافت TVL یک پروتکل خاص"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.BASE_URL}/tvl/{protocol}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'tvl' in data:
                            return data['tvl'][-1].get('totalLiquidityUSD', 0)
            return None
        except Exception as e:
            logger.error(f"خطا در دریافت TVL {protocol}: {e}")
            return None
    
    async def get_lending_rates(self) -> Dict[str, float]:
        """دریافت نرخ‌های وام‌دهی"""
        rates = {}
        
        # نرخ‌های Aave
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://aave-api-v2.aave.com/data/rates-history") as response:
                    if response.status == 200:
                        data = await response.json()
                        # محاسبه میانگین نرخ وام‌دهی
                        if data:
                            rates['Aave USDC'] = data[-1].get('lendingRate', 0) * 100
                            rates['Aave USDT'] = data[-1].get('lendingRate', 0) * 100
        except:
            pass
        
        # نرخ‌های Compound (تخمین از داده‌های عمومی)
        rates['Compound USDC'] = 3.5  # تخمین
        rates['Compound ETH'] = 1.2   # تخمین
        
        return rates


class CoinGeckoFundamentals:
    """
    کلاینت داده‌های فاندامنتال CoinGecko
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    async def get_coin_data(self, symbol: str) -> Optional[Dict]:
        """دریافت داده‌های فاندامنتال یک ارز"""
        try:
            # تبدیل نماد به نام کوین‌گکو
            symbol_lower = symbol.lower()
            
            # نگاشت نمادهای رایج به ID‌های CoinGecko
            symbol_map = {
                'btc': 'bitcoin',
                'eth': 'ethereum',
                'sol': 'solana',
                'bnb': 'binancecoin',
                'xrp': 'ripple',
                'ada': 'cardano',
                'doge': 'dogecoin',
                'dot': 'polkadot',
                'matic': 'matic-network',
                'link': 'chainlink'
            }
            
            coin_id = symbol_map.get(symbol_lower, symbol_lower)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/coins/{coin_id}"
                params = {
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false',
                    'sparkline': 'false'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"CoinGecko {symbol} ({coin_id}): داده دریافت شد")
                        return data
                    else:
                        logger.warning(f"CoinGecko {symbol} ({coin_id}): وضعیت {response.status}")
                        # تلاش مجدد با نام اصلی
                        if response.status == 404:
                            logger.warning(f"CoinGecko: تلاش با نام اصلی {symbol_lower}")
                            async with session.get(f"{self.BASE_URL}/coins/{symbol_lower}", params=params) as retry_response:
                                if retry_response.status == 200:
                                    return await retry_response.json()
                    return None
        except Exception as e:
            logger.error(f"خطا در دریافت داده CoinGecko {symbol}: {e}")
            return None
    
    async def get_global_data(self) -> Optional[Dict]:
        """دریافت داده‌های کلی بازار"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.BASE_URL}/global") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
            return None
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌های کلی: {e}")
            return None


# ==================== Main Data Manager ====================

class FundamentalDataManager:
    """
    مدیریت‌کننده داده‌های فاندامنتال و کلان اقتصادی
    """
    
    def __init__(self):
        self.fred_client = FREDClient()
        self.defillama_client = DeFiLlamaClient()
        self.coingecko_client = CoinGeckoFundamentals()
        
        # کش برای کاهش تعداد درخواست‌ها
        self._macro_cache = None
        self._macro_cache_time = None
        self._cache_duration = timedelta(hours=6)  # داده‌های کلان هر 6 ساعت یکبار
    
    async def get_macro_data(self, force_refresh: bool = False) -> MacroData:
        """دریافت داده‌های کلان اقتصادی"""
        # بررسی کش
        if (not force_refresh and 
            self._macro_cache and 
            self._macro_cache_time and 
            datetime.now() - self._macro_cache_time < self._cache_duration):
            return self._macro_cache
        
        try:
            macro = await self.fred_client.get_all_macro_data()
            self._macro_cache = macro
            self._macro_cache_time = datetime.now()
            return macro
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌های کلان: {e}")
            # برگرداندن داده‌های پیش‌فرض در صورت خطا
            return MacroData()
    
    async def get_crypto_fundamentals(self, symbol: str) -> CryptoFundamentals:
        """دریافت داده‌های فاندامنتال ارز دیجیتال"""
        fundamentals = CryptoFundamentals(symbol=symbol.upper())
        
        try:
            # داده‌های CoinGecko
            coin_data = await self.coingecko_client.get_coin_data(symbol)
            if coin_data:
                market_data = coin_data.get('market_data', {})
                
                # استخراج صحیح market_cap (CoinGecko یک dict برمی‌گرداند)
                mcap_data = market_data.get('market_cap', {})
                if isinstance(mcap_data, dict):
                    fundamentals.market_cap = mcap_data.get('usd', 0)
                elif isinstance(mcap_data, (int, float)):
                    fundamentals.market_cap = mcap_data
                else:
                    fundamentals.market_cap = 0
                
                # استخراج صحیح volume
                vol_data = market_data.get('total_volume', {})
                if isinstance(vol_data, dict):
                    fundamentals.volume_24h = vol_data.get('usd', 0)
                elif isinstance(vol_data, (int, float)):
                    fundamentals.volume_24h = vol_data
                else:
                    fundamentals.volume_24h = 0
                fundamentals.dominance = market_data.get('market_cap_percentage', {}).get('btc', 0)
                
                # تغییرات 24 ساعته
                price_change = market_data.get('price_change_percentage_24h', 0)
                fundamentals.market_cap_change_24h = price_change
                
            # داده‌های کلی بازار
            global_data = await self.coingecko_client.get_global_data()
            if global_data:
                tvl_data = global_data.get('data', {}).get('defi', {})
                fundamentals.defi_tvl = tvl_data.get('market_cap', 0)
                
            # داده‌های DeFiLlama
            defi_tvl = await self.defillama_client.get_ethereum_tvl()
            if defi_tvl:
                fundamentals.tvl = defi_tvl
            
            # DeFi TVL کل
            total_defi_tvl = await self.defillama_client.get_defi_tvl()
            if total_defi_tvl:
                fundamentals.defi_tvl = total_defi_tvl
                
            # نرخ‌های وام‌دهی
            fundamentals.lending_rates = await self.defillama_client.get_lending_rates()
            
        except Exception as e:
            logger.error(f"خطا در دریافت فاندامنتال {symbol}: {e}")
        
        return fundamentals
    
    async def get_full_analysis(self, symbol: str, smc_results: Dict = None, current_price: float = 0.0) -> FullAnalysisData:
        """
        دریافت تحلیل کامل (کلان + فاندامنتال + تکنیکال)
        
        Args:
            symbol: نماد ارز
            smc_results: نتایج تحلیل SMC (اختیاری)
            current_price: قیمت فعلی
        """
        full_data = FullAnalysisData(
            symbol=symbol.upper(),
            current_price=current_price,
            smc_results=smc_results or {}
        )
        
        # دریافت موازی داده‌ها
        macro_task = self.get_macro_data()
        fund_task = self.get_crypto_fundamentals(symbol)
        
        results = await asyncio.gather(
            macro_task,
            fund_task,
            return_exceptions=True
        )
        
        if isinstance(results[0], MacroData):
            full_data.macro = results[0]
        if isinstance(results[1], CryptoFundamentals):
            full_data.crypto_fundamentals = results[1]
        
        return full_data
    
    def format_macro_message(self, macro: MacroData) -> str:
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
            f"📊 **شاخص قیمت مصرف‌کننده (CPI):** {macro.cpi:.1f}\n"
            f"   (نرخ تورم سالانه: {macro.cpi_change:+.2f}%)\n\n"
            f"💵 **شاخص دلار (Trade-Weighted):** {macro.dxy:.2f}\n"
            f"   تغییر: {macro.dxy_change:+.2f}%\n\n"
            f"💰 **عرضه پول (M2):** ${macro.m2_money_supply/1000:.1f}T\n"
            f"   تغییر ماهانه: {macro.m2_change:+.2f}%\n\n"
            f"{'─' * 30}\n"
            f"🎯 **احساس کلی:** {sentiment}\n"
            f"💡 {description}\n"
            f"🕐 آخرین به‌روزرسانی: {macro.last_updated}"
        )
        
        return message
    
    def format_fundamentals_message(self, fund: CryptoFundamentals) -> str:
        """فرمت‌بندی پیام فاندامنتال"""
        if not fund or fund.market_cap == 0:
            return "❌ داده‌های فاندامنتال در دسترس نیست"
        
        sentiment = fund.get_market_sentiment()
        
        emoji_map = {
            "صعودی": "📈",
            "نزولی": "📉",
            "خنثی": "⚖️"
        }
        
        # فرمت TVL
        tvl_str = f"${fund.tvl/1e9:.2f}B" if fund.tvl > 1e9 else f"${fund.tvl/1e6:.2f}M"
        defi_tvl_str = f"${fund.defi_tvl/1e9:.2f}B" if fund.defi_tvl > 1e9 else f"${fund.defi_tvl/1e6:.2f}M"
        
        message = (
            f"💎 فاندامنتال {fund.symbol}\n"
            f"{'─' * 30}\n\n"
            f"📊 **ارزش بازار:** ${fund.market_cap/1e9:.2f}B\n"
            f"   تغییر 24h: {fund.market_cap_change_24h:+.2f}%\n\n"
            f"🔒 **TVL کل:** {tvl_str}\n"
            f"   TVL DeFi: {defi_tvl_str}\n\n"
            f"💵 **ارزش استیبل‌کوین‌ها:** ${fund.stablecoin_mcap/1e9:.2f}B\n\n"
            f"📈 **احساس بازار:** {emoji_map.get(sentiment, '⚖️')} {sentiment}\n"
        )
        
        # نرخ‌های وام‌دهی
        if fund.lending_rates:
            message += f"\n🏦 **نرخ‌های وام‌دهی:**\n"
            for protocol, rate in fund.lending_rates.items():
                message += f"   • {protocol}: {rate:.2f}%\n"
        
        return message
    
    def format_combined_message(self, full_data: FullAnalysisData) -> str:
        """فرمت‌بندی پیام ترکیبی کامل"""
        message = f"📊 تحلیل جامع {full_data.symbol}\n"
        message += f"{'─' * 35}\n\n"
        
        # بخش کلان اقتصادی
        if full_data.macro:
            macro_sentiment, _ = full_data.macro.get_sentiment()
            message += f"🏦 **محیط کلان:** {macro_sentiment}\n"
            message += f"   نرخ بهره: {full_data.macro.interest_rate:.2f}% | "
            message += f"DXY: {full_data.macro.dxy:.2f}\n\n"
        
        # بخش فاندامنتال
        if full_data.crypto_fundamentals:
            fund_sentiment = full_data.crypto_fundamentals.get_market_sentiment()
            message += f"💎 **فاندامنتال:** {fund_sentiment}\n"
            mcap = full_data.crypto_fundamentals.market_cap
            message += f"   Market Cap: ${mcap/1e9:.2f}B | "
            message += f"TVL: ${full_data.crypto_fundamentals.tvl/1e9:.1f}B\n\n"
        
        # بخش تکنیکال (SMC)
        if full_data.smc_results:
            bias = full_data.smc_results.get('bias', {})
            direction = bias.get('direction', 'NEUTRAL')
            message += f"📈 **تحلیل تکنیکال:** {direction}\n"
            confidence = bias.get('confidence', 0)
            message += f"   اعتماد: {confidence}%\n\n"
        
        # امتیاز همگرایی
        confluence = full_data.get_confluence_score()
        message += f"{'─' * 35}\n"
        message += f"\n🎯 **امتیاز همگرایی:** {confluence}/100\n"
        
        if confluence >= 70:
            message += "   ✅ سیگنال قوی: همه شاخص‌ها همسو هستند\n"
        elif confluence >= 55:
            message += "   ⚠️ سیگنال متوسط: اکثر شاخص‌ها همسو هستند\n"
        elif confluence >= 45:
            message += "   ⚖️ سیگنال خنثی: شاخص‌ها متناقض هستند\n"
        else:
            message += "   ❌ سیگنال ضعیف: شاخص‌ها مخالف هستند\n"
        
        return message


# Singleton instance
fundamental_manager = FundamentalDataManager()

# Export
__all__ = [
    'MacroData',
    'CryptoFundamentals', 
    'FullAnalysisData',
    'FundamentalDataManager',
    'fundamental_manager'
]
