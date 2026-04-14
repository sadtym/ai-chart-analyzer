"""
ماژول اسکنر بازار ارزهای دیجیتال
دریافت خودکار داده‌های بازار از CoinGecko و تحلیل با هوش مصنوعی

💡 ویژگی‌ها:
- دریافت ۱۵ ارز برتر به صورت خودکار
- تحلیل SMC بدون نیاز به تصویر
- رتبه‌بندی فرصت‌های معاملاتی
- اجرای دوره‌ای یا دستی

💡 استفاده:
    scanner = MarketScanner(analyzer)
    result = await scanner.scan_market()
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# 📦 وارد کردن تنظیمات
# ═══════════════════════════════════════════════════════════════

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# تعریف logger در سطح ماژول
logger = logging.getLogger(__name__)

try:
    from config import COINGECKO_API_KEY
except ImportError:
    COINGECKO_API_KEY = None  # CoinGecko رایگان است!

# ═══════════════════════════════════════════════════════════════
# ⚙️ تنظیمات
# ═══════════════════════════════════════════════════════════════

# لیست ارزهای مورد بررسی (می‌توانید تغییر دهید)
DEFAULT_COINS = [
    'bitcoin', 'ethereum', 'solana', 'binancecoin', 
    'ripple', 'cardano', 'avalanche-2', 'polkadot',
    'chainlink', 'polygon-ecosystem-token', 'dogecoin',
    'shiba-inu', 'bitcoin-cash', 'litecoin', 'uniswap'
]

# ارزهای حذف شدنی (Stablecoins و غیره)
EXCLUDED_COINS = [
    'tether', 'usd-coin', 'dai', 'binance-usd', 
    'frax-share', 'frax-share'
]

# ═══════════════════════════════════════════════════════════════
# 🏗️ کلاس اصلی اسکنر بازار
# ═══════════════════════════════════════════════════════════════

class MarketScanner:
    """کلاس اسکنر بازار ارزهای دیجیتال"""
    
    def __init__(self, ai_analyzer=None):
        """راه‌اندازی اسکنر"""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.ai_analyzer = ai_analyzer
        self.session = None
        self.cache = {}
        self.cache_timeout = 300  # ۵ دقیقه

        logger.info("✅ Market Scanner راه‌اندازی شد")
    
    async def get_session(self):
        """دریافت یا ایجاد session"""
        if self.session is None:
            import aiohttp
            self.session = aiohttp.ClientSession(
                headers={
                    "Accept": "application/json",
                    "User-Agent": "CryptoMarketScanner/1.0"
                }
            )
        return self.session
    
    async def close(self):
        """بستن session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    # ═══════════════════════════════════════════════════════════════
    # 📊 دریافت داده‌های بازار
    # ═══════════════════════════════════════════════════════════════
    
    async def get_top_coins(self, limit: int = 15) -> List[Dict]:
        """
        دریافت لیست ارزهای برتر
        
        Args:
            limit: تعداد ارزها
            
        Returns:
            لیست ارزها با اطلاعات قیمت
        """
        try:
            session = await self.get_session()
            
            # دریافت ارزها از CoinGecko
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit + 20,  # درخواست بیشتر برای فیلتر
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h,7d'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    logger.warning("⚠️ Rate limit از CoinGecko!")
                    await asyncio.sleep(60)  # صبر کنید
                    return await self.get_top_coins(limit)
                
                data = await response.json()
            
            # فیلتر کردن ارزها
            coins = []
            for coin in data:
                coin_id = coin.get('id', '')
                
                # حذف stablecoins و ارزهای نامطلوب
                if coin_id in EXCLUDED_COINS:
                    continue
                
                # بررسی حجم معاملات
                volume = coin.get('market_cap', 0)
                if volume < 100_000_000:  # حداقل ۱۰۰ میلیون دلار
                    continue
                
                coins.append({
                    'id': coin_id,
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name', ''),
                    'current_price': coin.get('current_price', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'volume_24h': coin.get('total_volume', 0),
                    'price_change_24h': coin.get('price_change_percentage_24h', 0),
                    'price_change_7d': coin.get('price_change_percentage_7d', 0),
                    'high_24h': coin.get('high_24h', 0),
                    'low_24h': coin.get('low_24h', 0),
                    'ath': coin.get('ath', 0),
                    'ath_change_percentage': coin.get('ath_change_percentage', 0)
                })
                
                if len(coins) >= limit:
                    break
            
            logger.info(f"📊 {len(coins)} ارز برتر دریافت شد")
            return coins
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت ارزها: {e}")
            return []
    
    async def get_coin_history(self, coin_id: str, days: int = 1) -> Dict:
        """
        دریافت تاریخچه قیمت یک ارز

        Args:
            coin_id: شناسه ارز
            days: تعداد روزها

        Returns:
            دیکشنری قیمت‌ها
        """
        try:
            session = await self.get_session()

            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly'
            }

            max_retries = 2
            for attempt in range(max_retries):
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        wait_time = 10 * (attempt + 1)  # افزایش زمان انتظار
                        logger.warning(f"⚠️ Rate limit برای {coin_id} - انتظار {wait_time} ثانیه...")
                        await asyncio.sleep(wait_time)
                        continue  #retry

                    data = await response.json()
                    break  # موفق، خارج شو
            else:
                # بعد از max_retries تلاش، داده‌های پیش‌فرض برگردان
                logger.warning(f"⚠️ رد شدن {coin_id} به دلیل rate limit")
                return {'prices': [], 'volumes': [], 'trend': 'UNKNOWN'}

            # استخراج قیمت‌ها
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            
            if not prices:
                return {'prices': [], 'volumes': [], 'trend': 'UNKNOWN'}
            
            # محاسبه روند
            price_list = [p[1] for p in prices[-12:]]  # ۱۲ ساعت اخیر
            
            if len(price_list) >= 2:
                if price_list[-1] > price_list[0]:
                    trend = 'UPTREND'
                elif price_list[-1] < price_list[0]:
                    trend = 'DOWNTREND'
                else:
                    trend = 'SIDEWAYS'
            else:
                trend = 'UNKNOWN'
            
            return {
                'prices': price_list,
                'volumes': [v[1] for v in volumes[-12:]] if volumes else [],
                'trend': trend,
                'current_price': prices[-1][1] if prices else 0,
                'highest_24h': max(p[1] for p in prices[:24]) if prices else 0,
                'lowest_24h': min(p[1] for p in prices[:24]) if prices else 0
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت تاریخچه {coin_id}: {e}")
            return {'prices': [], 'volumes': [], 'trend': 'UNKNOWN'}
    
    # ═══════════════════════════════════════════════════════════════
    # 🧠 تحلیل با هوش مصنوعی
    # ═══════════════════════════════════════════════════════════════
    
    def prepare_market_data(self, coins: List[Dict], histories: Dict[str, Dict]) -> str:
        """
        آماده‌سازی داده‌ها برای تحلیل AI
        
        Args:
            coins: لیست ارزها
            histories: تاریخچه قیمت‌ها
            
        Returns:
            رشته متنی آماده برای AI
        """
        data_lines = []
        
        for coin in coins:
            coin_id = coin['id']
            history = histories.get(coin_id, {})
            trend = history.get('trend', 'UNKNOWN')
            prices = history.get('prices', [])
            
            # فرمت قیمت‌ها
            if prices:
                price_str = ' | '.join([f"${p:.2f}" for p in prices[-5:]])
            else:
                price_str = "داده کافی نیست"
            
            # خط داده
            line = f"{coin['symbol']} | ${coin['current_price']:,.0f} | "
            line += f"24h: {coin['price_change_24h']:+.1f}% | "
            line += f"7d: {coin['price_change_7d']:+.1f}% | "
            line += f"روند: {trend} | "
            line += f"قیمت‌ها: {price_str}"
            
            data_lines.append(line)
        
        return '\n'.join(data_lines)
    
    async def analyze_with_ai(self, market_data: str) -> List[Dict]:
        """
        تحلیل بازار با هوش مصنوعی
        
        Args:
            market_data: داده‌های بازار
            
        Returns:
            لیست فرصت‌های معاملاتی
        """
        if not self.ai_analyzer:
            logger.warning("❌ AI Analyzer موجود نیست!")
            return []
        
        # پرامپت تحلیل بازار
        system_prompt = """تو یک تحلیلگر حرفه‌ای بازارهای کریپتو هستی با ۲۰ سال تجربه در تحلیل تکنیکال.
هدفت: تحلیل سریع و دقیق ۱۵ ارز برتر و شناسایی بهترین فرصت‌های معاملاتی.

📊 اصول تحلیل:
۱. بررسی ساختار بازار (روند صعودی/نزولی/رنج)
۲. شناسایی ارزهای با مومنتوم قوی
۳. بررسی نسبت ریسک به ریوارد
۴. توجه به حجم معاملات

🎯 خروجی مورد نیاز:
لیست ۵ فرصت برتر به ترتیب اولویت

📝 فرمت دقیق خروجی JSON:
```json
{
    "opportunities": [
        {
            "symbol": "BTC",
            "direction": "BUY/SELL/WAIT",
            "confidence": 75,
            "entry_zone": "64000-64500",
            "stop_loss": "63000",
            "take_profit": "66000",
            "reason": "توضیح کوتاه تحلیل",
            "timeframe": "4h",
            "rr_ratio": 2.0
        }
    ],
    "market_summary": {
        "overall_sentiment": "BULLISH/BEARISH/NEUTRAL",
        "top_sector": "DeFi/Layer1/Metaverse",
        "volatility_level": "HIGH/MEDIUM/LOW"
    }
}
```

⚠️ قوانین مهم:
- فقط ارزهای با فرصت واقعی را لیست کن
- اگر فرصت خوبی نیست، بنویس "WAIT"
- دلایل تحلیل را مختصر و مفید بنویس
- به SMA200 و نواحی حمایت/مقاومت توجه کن
"""
        
        try:
            # استفاده از Gemini برای تحلیل متنی
            import google.generativeai as genai
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_prompt
            )
            
            response = model.generate_content([
                f"📈 داده‌های بازار:\n\n{market_data}\n\n"
                f"🕐 زمان تحلیل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "لطفاً بالاترین فرصت‌های معاملاتی را شناسایی کن:"
            ])
            
            content = response.text.strip()
            
            # حذف علامت‌های markdown
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # پارس کردن JSON
            result = json.loads(content)
            
            logger.info(f"✅ تحلیل AI انجام شد: {len(result.get('opportunities', []))} فرصت شناسایی شد")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ خطا در پارس JSON: {e}")
            return {'opportunities': [], 'market_summary': {'overall_sentiment': 'UNKNOWN'}}
        except Exception as e:
            logger.error(f"❌ خطا در تحلیل AI: {e}")
            return {'opportunities': [], 'market_summary': {'overall_sentiment': 'UNKNOWN'}}
    
    # ═══════════════════════════════════════════════════════════════
    # 🔍 اسکن کامل بازار
    # ═══════════════════════════════════════════════════════════════
    
    async def scan_market(self, min_confidence: int = 60) -> Dict[str, Any]:
        """
        اسکن کامل بازار و تحلیل فرصت‌ها
        
        Args:
            min_confidence: حداقل اعتماد برای گزارش
            
        Returns:
            گزارش کامل بازار
        """
        logger.info("🔍 شروع اسکن بازار...")
        
        start_time = datetime.now()
        
        # ۱. دریافت ارزهای برتر
        coins = await self.get_top_coins(limit=15)
        
        if not coins:
            return {
                'success': False,
                'error': 'خطا در دریافت داده‌های بازار',
                'timestamp': start_time.isoformat()
            }
        
        logger.info(f"📊 {len(coins)} ارز دریافت شد، در حال دریافت تاریخچه...")
        
        # ۲. دریافت تاریخچه قیمت‌ها (با تأخیر برای رعایت rate limit)
        histories = {}
        for i, coin in enumerate(coins):
            history = await self.get_coin_history(coin['id'], days=1)
            histories[coin['id']] = history

            # تأخیر بین درخواست‌ها (۳ ثانیه برای جلوگیری از rate limit)
            if i < len(coins) - 1:
                await asyncio.sleep(3)
        
        # ۳. آماده‌سازی داده‌ها
        market_data = self.prepare_market_data(coins, histories)
        
        # ۴. تحلیل با AI
        analysis_result = await self.analyze_with_ai(market_data)
        
        # ۵. فیلتر کردن بر اساس اعتماد
        opportunities = analysis_result.get('opportunities', [])
        filtered_opportunities = [
            opp for opp in opportunities 
            if opp.get('confidence', 0) >= min_confidence
        ]
        
        # مرتب‌سازی بر اساس اعتماد
        filtered_opportunities.sort(
            key=lambda x: x.get('confidence', 0), 
            reverse=True
        )
        
        # ۶. محاسبه زمان اجرا
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            'success': True,
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'coins_analyzed': len(coins),
            'opportunities_found': len(filtered_opportunities),
            'opportunities': filtered_opportunities[:5],  # حداکثر ۵ فرصت
            'market_summary': analysis_result.get('market_summary', {})
        }
        
        logger.info(f"✅ اسکن بازار تکمیل شد: {len(filtered_opportunities)} فرصت در {duration:.1f} ثانیه")
        
        return result
    
    # ═══════════════════════════════════════════════════════════════
    # 📱 فرمت‌بندی گزارش برای تلگرام
    # ═══════════════════════════════════════════════════════════════
    
    def format_scan_report(self, scan_result: Dict) -> str:
        """
        فرمت‌بندی گزارش اسکن برای ارسال به تلگرام
        
        Args:
            scan_result: نتیجه اسکن
            
        Returns:
            پیام فرمت‌شده
        """
        if not scan_result.get('success', False):
            return f"""
❌ **خطا در اسکن بازار**

{scan_result.get('error', 'خطای نامشخص')}

🕐 زمان: {scan_result.get('timestamp', '')}
            """.strip()
        
        opportunities = scan_result.get('opportunities', [])
        summary = scan_result.get('market_summary', {})
        
        # انتخاب ایموجی بر اساس احساس کلی
        sentiment = summary.get('overall_sentiment', 'NEUTRAL').upper()
        if sentiment == 'BULLISH':
            sentiment_emoji = '🟢'
            sentiment_text = 'صعودی'
        elif sentiment == 'BEARISH':
            sentiment_emoji = '🔴'
            sentiment_text = 'نزولی'
        else:
            sentiment_emoji = '🟡'
            sentiment_text = 'خنثی'
        
        # ساخت پیام
        # استخراج زمان از timestamp
        timestamp_str = scan_result.get('timestamp', '')
        time_part = timestamp_str.split('T')[1][:8] if 'T' in timestamp_str else timestamp_str

        message = f"""🚀 **گزارش اسکن بازار کریپتو**

📊 **خلاصه بازار:**
{sentiment_emoji} احساس کلی: {sentiment_text}
⏰ زمان اسکن: `{time_part}`
⏱️ مدت زمان: {scan_result.get('duration_seconds', 0):.1f} ثانیه
📈 ارزهای بررسی شده: {scan_result.get('coins_analyzed', 0)}
🎯 فرصت‌های یافت شده: {scan_result.get('opportunities_found', 0)}

━━━━━━━━━━━━━━━━━━━
"""
        if opportunities:
            message += "💎 **بهترین فرصت‌ها:**\n\n"
            
            for i, opp in enumerate(opportunities, 1):
                direction = opp.get('direction', 'WAIT').upper()
                
                if direction == 'BUY':
                    emoji = '📈'
                    color = '🟢'
                elif direction == 'SELL':
                    emoji = '📉'
                    color = '🔴'
                else:
                    emoji = '⚖️'
                    color = '🟡'
                
                entry = opp.get('entry_zone', 'N/A')
                sl = opp.get('stop_loss', 'N/A')
                tp = opp.get('take_profit', 'N/A')
                confidence = opp.get('confidence', 0)
                symbol = opp.get('symbol', 'N/A')
                reason = opp.get('reason', '')
                rr = opp.get('rr_ratio', 0)
                timeframe = opp.get('timeframe', '4h')
                
                message += f"""**{i}. {emoji} {symbol}** {color}
   🎯 جهت: {direction}
   📊 اعتماد: {confidence}%
   ⏰ تایم‌فریم: {timeframe}
   💰 ورود: `{entry}`
   ❌ حد ضرر: `{sl}`
   🎯 حد سود: `{tp}`
   ⚡ RR: 1:{rr}
   📝 دلیل: {reason}

"""
        else:
            message += "❌ **هیچ فرصت معاملاتی با اعتماد کافی یافت نشد**\n\n"
            message += "💡 پیشنهاد: منتظر شرایط بهتر باشید یا تایم‌فریم را تغییر دهید.\n"
        
        message += """━━━━━━━━━━━━━━━━━━━

📱 **دستورات مفید:**
• /scan - اسکن دستی بازار
• ارسال عکس چارت - تحلیل SMC

⚠️ **هشدار:** این تحلیل فقط جنبه اطلاعاتی دارد.
         مسئولیت معاملات با خودتان است.
"""
        return message


# ═══════════════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_scanner():
        print("=" * 60)
        print("🧪 تست Market Scanner")
        print("=" * 60)
        
        scanner = MarketScanner()
        
        # تست دریافت ارزها
        print("\n📊 دریافت ارزهای برتر...")
        coins = await scanner.get_top_coins(limit=5)
        print(f"   یافت شد: {len(coins)} ارز")
        for coin in coins[:3]:
            print(f"   - {coin['symbol']}: ${coin['current_price']:,.0f}")
        
        # تست دریافت تاریخچه
        print("\n📈 دریافت تاریخچه...")
        history = await scanner.get_coin_history('bitcoin', days=1)
        print(f"   روند: {history.get('trend', 'UNKNOWN')}")
        print(f"   قیمت‌ها: {len(history.get('prices', []))} داده")
        
        # تست فرمت‌بندی
        print("\n📝 آماده‌سازی داده‌ها...")
        market_data = scanner.prepare_market_data(coins, {'bitcoin': history})
        print(f"   داده‌های آماده: {len(market_data)} کاراکتر")
        
        await scanner.close()
        print("\n✅ تست تکمیل شد!")
    
    asyncio.run(test_scanner())
