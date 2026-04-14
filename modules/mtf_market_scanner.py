"""
ماژول اسکنر بازار چند تایم‌فریمی (MTF)
دریافت و تحلیل حرفه‌ای داده‌های بازار با استفاده از تحلیل تکنیکال و هوش مصنوعی

💡 ویژگی‌ها:
- تحلیل ۳ تایم‌فریم: ۱ ساعت، ۴ ساعت، روزانه
- اندیکاتورهای تکنیکال: RSI، MACD، میانگین‌های متحرک
- سیستم امتیازدهی MTF Confluence
- رتبه‌بندی هوشمند فرصت‌های معاملاتی
- تحلیل SMC با هوش مصنوعی

💡 استفاده:
    scanner = MTFMarketScanner(analyzer)
    result = await scanner.scan_market()
"""

import asyncio
import json
import logging
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# تعریف logger در سطح ماژول
logger = logging.getLogger(__name__)

try:
    from config import COINGECKO_API_KEY
except ImportError:
    COINGECKO_API_KEY = None

# ═══════════════════════════════════════════════════════════════
# ⚙️ تنظیمات اسکنر MTF (بهینه‌شده)
# ═══════════════════════════════════════════════════════════════

MTF_TIMEFRAMES = {
    '1h': {'days': 2, 'label': '۱ ساعته'},
    '4h': {'days': 7, 'label': '۴ ساعته'},
    '1d': {'days': 14, 'label': 'روزانه'}
}

WEIGHTS = {
    '1d': 0.40,
    '4h': 0.35,
    '1h': 0.25
}

# ارزهای مورد نظر برای اسکن (با API رایگان - تعداد کمتر)
DEFAULT_COINS = [
    'bitcoin', 'ethereum', 'solana'
]

EXCLUDED_COINS = [
    'tether', 'usd-coin', 'dai', 'binance-usd',
    'frax-share', 'frax-share'
]


# ═══════════════════════════════════════════════════════════════
# 🛠️ توابع کمکی تحلیل تکنیکال
# ═══════════════════════════════════════════════════════════════

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """محاسبه اندیکاتورهای تکنیکال"""
    if df is None or len(df) < 20:
        return df

    close = df['close']

    # RSI
    df['rsi'] = ta.rsi(close, length=14)

    # MACD
    macd = ta.macd(close, fast=12, slow=26, signal=9)
    df['macd'] = macd['MACD_12_26_9'] if macd is not None else 0
    df['macd_signal'] = macd['MACDs_12_26_9'] if macd is not None else 0
    df['macd_hist'] = macd['MACDh_12_26_9'] if macd is not None else 0

    # Moving Averages
    df['ema20'] = ta.ema(close, length=20)
    df['ema50'] = ta.ema(close, length=50)
    df['ema200'] = ta.ema(close, length=200) if len(close) > 200 else close

    # Bollinger Bands
    bbands = ta.bbands(close, length=20, std=2)
    df['bb_upper'] = bbands['BBU_20_2.0'] if bbands is not None else 0
    df['bb_lower'] = bbands['BBL_20_2.0'] if bbands is not None else 0

    # ATR
    df['atr'] = ta.atr(df['high'], df['low'], close, length=14)

    return df


def detect_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """تشخیص روند و وضعیت تکنیکال"""
    if df is None or len(df) < 10:
        return {
            'trend': 'UNKNOWN',
            'rsi': 50,
            'macd_direction': 'NEUTRAL',
            'ema_alignment': 'NEUTRAL',
            'strength': 0
        }

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    # RSI Analysis
    rsi = latest.get('rsi', 50)
    if rsi > 70:
        rsi_status = 'OVERBOUGHT'
    elif rsi < 30:
        rsi_status = 'OVERSOLD'
    else:
        rsi_status = 'NEUTRAL'

    # MACD Analysis
    macd = latest.get('macd', 0)
    macd_signal = latest.get('macd_signal', 0)
    macd_hist = latest.get('macd_hist', 0)

    if macd > macd_signal and macd_hist > 0:
        macd_direction = 'BULLISH'
    elif macd < macd_signal and macd_hist < 0:
        macd_direction = 'BEARISH'
    else:
        macd_direction = 'NEUTRAL'

    # EMA Alignment
    ema20 = latest.get('ema20', 0)
    ema50 = latest.get('ema50', 0)
    ema200 = latest.get('ema200', 0)
    close = latest.get('close', 0)

    if close > ema50 > ema200:
        ema_alignment = 'BULLISH'
    elif close < ema50 < ema200:
        ema_alignment = 'BEARISH'
    elif close > ema20 and close > ema50:
        ema_alignment = 'SLIGHTLY_BULLISH'
    elif close < ema20 and close < ema50:
        ema_alignment = 'SLIGHTLY_BEARISH'
    else:
        ema_alignment = 'NEUTRAL'

    # Overall Trend
    bullish_signals = 0
    bearish_signals = 0

    if rsi > 50:
        bullish_signals += 1
    elif rsi < 50:
        bearish_signals += 1

    if macd_direction == 'BULLISH':
        bullish_signals += 2
    elif macd_direction == 'BEARISH':
        bearish_signals += 2

    if ema_alignment in ['BULLISH', 'SLIGHTLY_BULLISH']:
        bullish_signals += 1
    elif ema_alignment in ['BEARISH', 'SLIGHTLY_BEARISH']:
        bearish_signals += 1

    # Price vs EMAs
    if close > ema50:
        bullish_signals += 1
    else:
        bearish_signals += 1

    if bullish_signals > bearish_signals + 1:
        trend = 'BULLISH'
    elif bearish_signals > bullish_signals + 1:
        trend = 'BEARISH'
    else:
        trend = 'NEUTRAL'

    # Calculate strength (0-100)
    total_signals = bullish_signals + bearish_signals
    if total_signals > 0:
        strength = int((bullish_signals / total_signals) * 100)
    else:
        strength = 50

    return {
        'trend': trend,
        'rsi': round(rsi, 2),
        'rsi_status': rsi_status,
        'macd_direction': macd_direction,
        'macd_hist': round(macd_hist, 6),
        'ema_alignment': ema_alignment,
        'ema20': round(ema20, 4) if ema20 else None,
        'ema50': round(ema50, 4) if ema50 else None,
        'ema200': round(ema200, 4) if ema200 else None,
        'close': round(close, 4),
        'strength': strength,
        'support': round(latest.get('bb_lower', close * 0.98), 4),
        'resistance': round(latest.get('bb_upper', close * 1.02), 4),
        'atr': round(latest.get('atr', 0), 4)
    }


def resample_data(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """تبدیل داده‌های ساعتی به تایم‌فریم‌های بالاتر"""
    if df is None or len(df) < 5:
        return df

    df = df.copy()

    # تبدیل timestamp به datetime
    if 'timestamp' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    elif 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['time'], unit='ms')
    else:
        return df

    df.set_index('datetime', inplace=True)
    df = df.sort_index()

    # تبدیل OHLC
    if timeframe == '4h':
        df_resampled = df.resample('4H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
    elif timeframe == '1d':
        df_resampled = df.resample('D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
    else:
        return df

    # حذف ردیف‌های خالی
    df_resampled = df_resampled.dropna()
    df_resampled = df_resampled[df_resampled['volume'] > 0]

    return df_resampled.reset_index()


# ═══════════════════════════════════════════════════════════════
# 🏗️ کلاس اصلی اسکنر بازار MTF
# ═══════════════════════════════════════════════════════════════

class MTFMarketScanner:
    """اسکنر بازار چند تایم‌فریمی"""

    def __init__(self, ai_analyzer=None):
        """راه‌اندازی اسکنر"""
        # همیشه از API رایگان استفاده کن (Demo keys فقط با api.coingecko.com کار می‌کنند)
        self.base_url = "https://api.coingecko.com/api/v3"
        logger.info("✅ استفاده از CoinGecko Free API")
        self.ai_analyzer = ai_analyzer
        self.session = None
        self.cache = {}
        self.cache_timeout = 300

        logger.info("✅ MTF Market Scanner راه‌اندازی شد")

    async def get_session(self):
        """دریافت session"""
        if self.session is None:
            import aiohttp
            headers = {
                "Accept": "application/json",
                "User-Agent": "MTFMarketScanner/2.0"
            }
            # فقط برای API رایگان از header استفاده نکن (با API key تداخل دارد)
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        """بستن session"""
        if self.session:
            await self.session.close()
            self.session = None

    # ═══════════════════════════════════════════════════════════════
    # 📊 دریافت و پردازش داده‌ها
    # ═══════════════════════════════════════════════════════════════

    async def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        """
        دریافت داده‌های یک ارز برای همه تایم‌فریم‌ها
        """
        try:
            session = await self.get_session()

            # دریافت ۷ روز داده ساعتی (برای ساخت همه تایم‌فریم‌ها)
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': 7,
                'interval': 'hourly'
            }

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with session.get(url, params=params) as response:
                        if response.status == 429:
                            wait_time = 5 * (attempt + 1)
                            logger.warning(f"⚠️ Rate limit برای {coin_id} - انتظار {wait_time} ثانیه...")
                            await asyncio.sleep(wait_time)
                            continue

                        text = await response.text()
                        if not text.strip():
                            logger.warning(f"⚠️ پاسخ خالی برای {coin_id}")
                            await asyncio.sleep(5)
                            continue
                        
                        data = json.loads(text)
                        break
                except json.JSONDecodeError as e:
                    logger.error(f"❌ خطا در پارس JSON برای {coin_id}: {e}")
                    await asyncio.sleep(2)
                    continue
            else:
                logger.warning(f"⚠️ رد شدن {coin_id} به دلیل rate limit")
                return {'id': coin_id, 'error': 'rate_limit'}

            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])

            if not prices:
                return {'id': coin_id, 'error': 'no_data'}

            # ساخت DataFrame
            df_hourly = pd.DataFrame(prices, columns=['timestamp', 'close'])
            df_hourly['open'] = df_hourly['close']
            df_hourly['high'] = df_hourly['close']
            df_hourly['low'] = df_hourly['close']

            if volumes:
                df_vol = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
                df_hourly = df_hourly.merge(df_vol, on='timestamp', how='left')

            df_hourly['volume'] = df_hourly['volume'].fillna(0)

            # محاسبه High/Low از داده‌های قیمت (تقریبی)
            df_hourly['high'] = df_hourly['close'] * 1.002
            df_hourly['low'] = df_hourly['close'] * 0.998

            # تحلیل تایم‌فریم ۱ ساعته
            df_1h = df_hourly.copy()
            df_1h = calculate_indicators(df_1h)
            trend_1h = detect_trend(df_1h)

            # تحلیل تایم‌فریم ۴ ساعته
            df_4h = resample_data(df_hourly, '4h')
            if len(df_4h) >= 10:
                df_4h = calculate_indicators(df_4h)
                trend_4h = detect_trend(df_4h)
            else:
                trend_4h = {'trend': 'UNKNOWN', 'strength': 0, 'rsi': 50}

            # تحلیل تایم‌فریم روزانه
            df_1d = resample_data(df_hourly, '1d')
            if len(df_1d) >= 5:
                df_1d = calculate_indicators(df_1d)
                trend_1d = detect_trend(df_1d)
            else:
                trend_1d = {'trend': 'UNKNOWN', 'strength': 0, 'rsi': 50}

            # محاسبه امتیاز MTF Confluence
            confluence_score = self._calculate_confluence_score(
                trend_1h, trend_4h, trend_1d
            )

            return {
                'id': coin_id,
                'current_price': prices[-1][1] if prices else 0,
                'price_change_24h': self._get_price_change(prices),
                'timeframes': {
                    '1h': trend_1h,
                    '4h': trend_4h,
                    '1d': trend_1d
                },
                'confluence_score': confluence_score,
                'alignment': self._get_alignment(trend_1h, trend_4h, trend_1d)
            }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت داده {coin_id}: {e}")
            return {'id': coin_id, 'error': str(e)}

    def _calculate_confluence_score(self, tf_1h: Dict, tf_4h: Dict, tf_1d: Dict) -> int:
        """محاسبه امتیاز هماهنگی تایم‌فریم‌ها"""
        score = 0

        # وزن‌دهی به هر تایم‌فریم
        weights = {'1h': 0.25, '4h': 0.35, '1d': 0.40}

        for tf_name, tf_data in [('1h', tf_1h), ('4h', tf_4h), ('1d', tf_1d)]:
            trend = tf_data.get('trend', 'NEUTRAL')
            strength = tf_data.get('strength', 50)

            if trend == 'BULLISH':
                score += int(100 * weights[tf_name])
            elif trend == 'BEARISH':
                score -= int(100 * weights[tf_name])
            # NEUTRAL: امتیاز صفر

        return max(-100, min(100, score))

    def _get_alignment(self, tf_1h: Dict, tf_4h: Dict, tf_1d: Dict) -> str:
        """تشخیص میزان هماهنگی"""
        trends = [tf_1h.get('trend'), tf_4h.get('trend'), tf_1d.get('trend')]

        # همه صعودی
        if all(t == 'BULLISH' for t in trends):
            return 'PERFECT_BULLISH'

        # همه نزولی
        if all(t == 'BEARISH' for t in trends):
            return 'PERFECT_BEARISH'

        # دو صعودی، یک خنثی
        if trends.count('BULLISH') == 2 and 'NEUTRAL' in trends:
            return 'BULLISH_DIVERGENCE'

        # دو نزولی، یک خنثی
        if trends.count('BEARISH') == 2 and 'NEUTRAL' in trends:
            return 'BEARISH_DIVERGENCE'

        # ۱h و ۴h همسو، ۱d مخالف
        if tf_1h.get('trend') == tf_4h.get('trend') != tf_1d.get('trend'):
            return f"TF_CONFLICT_{tf_1d.get('trend')}"

        # رنج یا مخلوط
        if 'NEUTRAL' in trends or len(set(trends)) > 2:
            return 'MIXED'

        return 'NEUTRAL'

    def _get_price_change(self, prices: List) -> float:
        """محاسبه تغییر قیمت ۲۴ ساعته"""
        if len(prices) < 24:
            return 0

        current = prices[-1][1]
        prev_24h = prices[-25][1] if len(prices) > 24 else prices[0][1]

        if prev_24h == 0:
            return 0

        return round(((current - prev_24h) / prev_24h) * 100, 2)

    async def get_top_coins(self, limit: int = 7) -> List[Dict]:
        """دریافت لیست ارزهای برتر (بهینه‌شده)"""
        try:
            session = await self.get_session()

            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit + 20,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }

            async with session.get(url, params=params) as response:
                logger.info(f"📡 API Response Status: {response.status}")
                if response.status != 200:
                    logger.error(f"❌ API Error: {response.status}")
                    return []
                data = await response.json()
                logger.info(f"📊 دریافت {len(data)} ردیف از API")

            coins = []
            for coin in data:
                coin_id = coin.get('id', '')
                if coin_id in EXCLUDED_COINS:
                    continue
                if coin.get('market_cap', 0) < 100_000_000:
                    continue

                coins.append({
                    'id': coin_id,
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name', ''),
                    'current_price': coin.get('current_price', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'volume_24h': coin.get('total_volume', 0),
                    'price_change_24h': coin.get('price_change_percentage_24h', 0)
                })

                if len(coins) >= limit:
                    break

            logger.info(f"✅ {len(coins)} ارز پس از فیلتر انتخاب شد")
            return coins

        except Exception as e:
            logger.error(f"❌ خطا در دریافت ارزها: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════
    # 🧠 تحلیل با هوش مصنوعی
    # ═══════════════════════════════════════════════════════════════

    def prepare_mtf_data(self, coins_data: List[Dict]) -> str:
        """آماده‌سازی داده‌های MTF برای AI"""
        lines = []

        for coin in coins_data:
            tf_data = coin.get('timeframes', {})
            confluence = coin.get('confluence_score', 0)
            alignment = coin.get('alignment', 'NEUTRAL')
            price = coin.get('current_price', 0)
            change_24h = coin.get('price_change_24h', 0)

            # خلاصه هر ارز
            trend_1h = tf_data.get('1h', {}).get('trend', '?')
            trend_4h = tf_data.get('4h', {}).get('trend', '?')
            trend_1d = tf_data.get('1d', {}).get('trend', '?')
            rsi_4h = tf_data.get('4h', {}).get('rsi', 0)
            strength = tf_data.get('4h', {}).get('strength', 0)

            line = f"{coin['symbol']} | ${price:,.0f} | 24h: {change_24h:+.1f}% | "
            line += f"MTF: {trend_1h}/{trend_4h}/{trend_1d} | "
            line += f"Confluence: {confluence:+d} | "
            line += f"RSI4h: {rsi_4h:.0f} | Strength: {strength}%"

            lines.append(line)

        return '\n'.join(lines)

    def prepare_simple_data(self, coins: List[Dict]) -> str:
        """آماده‌سازی داده‌های ساده برای AI (بدون نیاز به API اضافی)"""
        lines = []

        for coin in coins:
            price = coin.get('current_price', 0)
            change_24h = coin.get('price_change_24h', 0)
            volume = coin.get('volume_24h', 0)
            market_cap = coin.get('market_cap', 0)

            # تخمین وضعیت بر اساس تغییرات قیمت
            if change_24h > 5:
                momentum = "بسیار صعودی"
            elif change_24h > 2:
                momentum = "صعودی"
            elif change_24h < -5:
                momentum = "بسیار نزولی"
            elif change_24h < -2:
                momentum = "نزولی"
            else:
                momentum = "خنثی"

            line = f"{coin['symbol']} ({coin['name']}) | "
            line += f"قیمت: ${price:,.2f} | "
            line += f"24h: {change_24h:+.2f}% | "
            line += f"وضعیت: {momentum} | "
            line += f"حجم: ${volume/1e9:.1f}B | "
            line += f"مارکت کپ: ${market_cap/1e9:.0f}B"

            lines.append(line)

        return '\n'.join(lines)

    def create_ai_prompt(self, mtf_summary: str) -> str:
        """ساخت پرامپت تحلیل بازار"""
        return f"""تو یک تحلیلگر حرفه‌ای بازارهای کریپتو با ۲۰ سال تجربه هستی.
تخصص تو: تحلیل تکنیکال و شناسایی فرصت‌های معاملاتی با احتمال موفقیت بالا.

📊 **اصول تحلیل:**
۱. بررسی مومنتوم قیمت (تغییرات ۲۴ ساعت)
۲. تحلیل حجم معاملات
۳. تشخیص روند کلی بازار
۴. شناسایی ارزهای با پتانسیل صعودی یا نزولی

🎯 **سیستم امتیازدهی:**
- تغییرات +5% یا بیشتر + مومنتوم قوی: امتیاز بالا
- تغییرات +2% تا +5%: امتیاز متوسط
- تغییرات -2% تا +2%: خنثی
- تغییرات زیر -2%: ریسک بیشتر

📝 **خروجی مورد نیاز (JSON):**
```json
{{
    "opportunities": [
        {{
            "symbol": "BTC",
            "direction": "BUY/SELL/WAIT",
            "confidence": 80,
            "entry_zone": "90000-91000",
            "stop_loss": "87000",
            "take_profit": "95000",
            "reason": "توضیح تحلیل",
            "rr_ratio": 2.0,
            "risk_level": "MEDIUM"
        }}
    ],
    "market_summary": {{
        "overall_sentiment": "BULLISH/BEARISH/NEUTRAL",
        "top_performers": "BTC, SOL",
        "volatility_level": "HIGH/MEDIUM/LOW",
        "market_trend": "صعودی/نزولی/رنج"
    }}
}}
```

⚠️ **قوانین مهم:**
- فقط فرصت‌های با اعتماد بالا (حداقل ۷۰٪) را گزارش کن
- حداقل RR: 1.5
- به نواحی حمایت/مقاومت توجه کن
- اگر اطمینان کافی نیست، WAIT پیشنهاد کن

📈 **داده‌های بازار:**
{mtf_summary}

زمان تحلیل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

لطفاً بهترین فرصت‌های معاملاتی را با تحلیل MTF شناسایی کن:
"""

    async def analyze_with_ai(self, market_data: str) -> Dict:
        """تحلیل بازار با هوش مصنوعی"""
        if not self.ai_analyzer:
            logger.warning("❌ AI Analyzer موجود نیست!")
            return {'opportunities': [], 'market_summary': {}}

        try:
            import google.generativeai as genai

            prompt = self.create_ai_prompt(market_data)

            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=prompt
            )

            response = model.generate_content([
                "لطفاً بر اساس داده‌های MTF بالا، تحلیل کن و بهترین فرصت‌ها را شناسایی کن:"
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

            result = json.loads(content)

            logger.info(f"✅ تحلیل AI انجام شد: {len(result.get('opportunities', []))} فرصت")
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

    async def scan_market(self, min_confidence: int = 65) -> Dict[str, Any]:
        """اسکن کامل بازار (نسخه ساده برای API رایگان)"""
        logger.info("🔍 شروع اسکن بازار...")

        start_time = datetime.now()

        # ۱. دریافت ارزهای برتر
        all_coins = await self.get_top_coins(limit=10)

        if not all_coins:
            return {
                'success': False,
                'error': 'خطا در دریافت داده‌های بازار',
                'timestamp': start_time.isoformat()
            }

        # فیلتر کردن فقط ارزهای مورد نظر
        coins = [c for c in all_coins if c['id'] in DEFAULT_COINS]
        if not coins:
            coins = all_coins[:5]  # از ۵ ارز برتر استفاده کن

        logger.info(f"📊 {len(coins)} ارز انتخاب شد برای تحلیل")

        # ۲. آماده‌سازی داده‌ها برای AI (بدون نیاز به API اضافی)
        mtf_summary = self.prepare_simple_data(coins)

        # ۳. تحلیل با AI
        analysis_result = await self.analyze_with_ai(mtf_summary)

        # ۴. فیلتر کردن فرصت‌ها
        opportunities = analysis_result.get('opportunities', [])
        filtered_opportunities = [
            opp for opp in opportunities
            if opp.get('confidence', 0) >= min_confidence
        ]

        filtered_opportunities.sort(
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )

        # ۵. محاسبه زمان اجرا
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        result = {
            'success': True,
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'coins_analyzed': len(coins),
            'opportunities_found': len(filtered_opportunities),
            'opportunities': filtered_opportunities[:5],
            'market_summary': analysis_result.get('market_summary', {}),
            'mtf_top_coins': []
        }

        logger.info(f"✅ اسکن تکمیل شد: {len(filtered_opportunities)} فرصت در {duration:.1f} ثانیه")
        return result

    # ═══════════════════════════════════════════════════════════════
    # 📱 فرمت‌بندی گزارش
    # ═══════════════════════════════════════════════════════════════

    def format_scan_report(self, scan_result: Dict) -> str:
        """فرمت‌بندی گزارش اسکن MTF"""
        if not scan_result.get('success', False):
            return f"""
❌ **خطا در اسکن بازار**

{scan_result.get('error', 'خطای نامشخص')}

🕐 زمان: {scan_result.get('timestamp', '')}
            """.strip()

        opportunities = scan_result.get('opportunities', [])
        summary = scan_result.get('market_summary', {})
        top_coins = scan_result.get('mtf_top_coins', [])

        # احساس کلی
        sentiment = summary.get('overall_sentiment', 'NEUTRAL').upper()
        sentiment_map = {
            'BULLISH': ('🟢', 'صعودی'),
            'BEARISH': ('🔴', 'نزولی'),
            'NEUTRAL': ('🟡', 'خنثی')
        }
        sentiment_emoji, sentiment_text = sentiment_map.get(sentiment, ('🟡', 'خنثی'))

        # بهترین هماهنگی
        best_alignment = summary.get('best_alignment', 'NEUTRAL')
        alignment_map = {
            'PERFECT_BULLISH': ('🟢', 'تمام تایم‌فریم‌ها صعودی'),
            'PERFECT_BEARISH': ('🔴', 'تمام تایم‌فریم‌ها نزولی'),
            'BULLISH_DIVERGENCE': ('🟢', '۲ صعودی + ۱ خنثی'),
            'BEARISH_DIVERGENCE': ('🔴', '۲ نزولی + ۱ خنثی'),
            'MIXED': ('🟡', 'مخلوط'),
            'NEUTRAL': ('🟡', 'خنثی')
        }
        align_emoji, align_text = alignment_map.get(best_alignment, ('🟡', 'خنثی'))

        # ساخت پیام
        message = f"""🚀 **گزارش اسکن بازار MTF**

📊 **خلاصه تحلیل چند تایم‌فریمی:**
{sentiment_emoji} احساس کلی: {sentiment_text}
{align_emoji} بهترین هماهنگی: {align_text}
⏰ زمان: `{scan_result.get('timestamp', '').split('T')[1][:8]}`
⏱️ مدت زمان: {scan_result.get('duration_seconds', 0):.1f} ثانیه
📈 ارزهای بررسی شده: {scan_result.get('coins_analyzed', 0)}
🎯 فرصت‌های یافت شده: {scan_result.get('opportunities_found', 0)}

━━━━━━━━━━━━━━━━━━━
"""

        # نمایش تاپ ۵ کوین‌های MTF
        if top_coins:
            message += "📊 **تاپ ۵ کوین‌های MTF:**\n\n"
            for i, coin in enumerate(top_coins, 1):
                confluence = coin.get('confluence', 0)
                alignment = coin.get('alignment', 'NEUTRAL')

                if confluence > 50:
                    color_emoji = '🟢'
                elif confluence < -50:
                    color_emoji = '🔴'
                else:
                    color_emoji = '🟡'

                message += f"{i}. {color_emoji} **{coin['symbol']}** | Confluence: {confluence:+.0f} | {alignment}\n"
            message += "\n"

        if opportunities:
            message += "💎 **بهترین فرصت‌های معاملاتی:**\n\n"

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
                mtf_conf = opp.get('mtf_confluence', 'NEUTRAL')
                risk = opp.get('risk_level', 'MEDIUM')

                message += f"""**{i}. {emoji} {symbol}** {color}
   🎯 جهت: {direction} | 📊 اعتماد: {confidence}%
   ⏰ تایم‌فریم: {timeframe} | ⚠️ ریسک: {risk}
   🔗 MTF: {mtf_conf}
   💰 ورود: `{entry}`
   ❌ حد ضرر: `{sl}`
   🎯 حد سود: `{tp}`
   ⚡ RR: 1:{rr}
   📝 دلیل: {reason}

"""
        else:
            message += "❌ **هیچ فرصت معاملاتی با اعتماد کافی یافت نشد**\n\n"
            message += "💡 پیشنهاد: منتظر شرایط بهتر یا تغییر تایم‌فریم باشید.\n"

        message += """━━━━━━━━━━━━━━━━━━━

📱 **دستورات مفید:**
• /scan - اسکن دستی بازار MTF
• ارسال عکس چارت - تحلیل SMC

⚠️ **هشدار:** این تحلیل فقط جنله اطلاعاتی دارد.
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
        print("🧪 تست MTF Market Scanner")
        print("=" * 60)

        scanner = MTFMarketScanner()

        # تست دریافت داده‌های BTC
        print("\n📊 دریافت داده‌های MTF برای BTC...")
        btc_data = await scanner.get_coin_data('bitcoin')
        print(f"   Confluence Score: {btc_data.get('confluence_score', 'N/A')}")
        print(f"   Alignment: {btc_data.get('alignment', 'N/A')}")

        tf = btc_data.get('timeframes', {})
        print(f"   1H Trend: {tf.get('1h', {}).get('trend', '?')}")
        print(f"   4H Trend: {tf.get('4h', {}).get('trend', '?')}")
        print(f"   1D Trend: {tf.get('1d', {}).get('trend', '?')}")

        await scanner.close()
        print("\n✅ تست تکمیل شد!")

    asyncio.run(test_scanner())
