"""
ماژول کلاینت API صرافی LBank
این ماژول برای دریافت داده‌های OHLCV از صرافی LBank طراحی شده است
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
import pandas as pd
import logging

# تنظیم لاگر
logger = logging.getLogger(__name__)


class LBankClient:
    """
    کلاینت برای دسترسی به API صرافی LBank
    این کلاس شامل متدهایی برای دریافت داده‌های کندل استیک است
    """

    # آدرس‌های پایه API
    BASE_URLS = [
        "https://api.lbkex.com/",
        "https://api.lbank.info/",
    ]

    # تایم فریم‌های پشتیبانی شده
    TIMEFRAMES = {
        "1m": "minute1",
        "5m": "minute5",
        "15m": "minute15",
        "30m": "minute30",
        "1h": "hour1",
        "4h": "hour4",
        "8h": "hour8",
        "12h": "hour12",
        "1d": "day1",
        "1w": "week1",
        "1M": "month1",
    }

    # نگاشت نمادهای استاندارد به نمادهای LBank
    SYMBOL_MAPPING = {
        "BTC/USDT": "btc_usdt",
        "ETH/USDT": "eth_usdt",
        "BNB/USDT": "bnb_usdt",
        "XRP/USDT": "xrp_usdt",
        "ADA/USDT": "ada_usdt",
        "SOL/USDT": "sol_usdt",
        "DOGE/USDT": "doge_usdt",
        "DOT/USDT": "dot_usdt",
        "MATIC/USDT": "matic_usdt",
        "LTC/USDT": "ltc_usdt",
        "LINK/USDT": "link_usdt",
        "UNI/USDT": "uni_usdt",
        "ATOM/USDT": "atom_usdt",
        "XMR/USDT": "xmr_usdt",
        "NEO/USDT": "neo_usdt",
        "EOS/USDT": "eos_usdt",
        "XTZ/USDT": "xtz_usdt",
        "BCH/USDT": "bch_usdt",
        "ETC/USDT": "etc_usdt",
        "FIL/USDT": "fil_usdt",
        "THETA/USDT": "theta_usdt",
        "TRX/USDT": "trx_usdt",
        "AVAX/USDT": "avax_usdt",
        "SHIB/USDT": "shib_usdt",
        "ARB/USDT": "arb_usdt",
        "OP/USDT": "op_usdt",
        "APT/USDT": "apt_usdt",
        "SUI/USDT": "sui_usdt",
        "INJ/USDT": "inj_usdt",
        "LDO/USDT": "ldo_usdt",
        "RNDR/USDT": "rndr_usdt",
        "MKR/USDT": "mkr_usdt",
        "AAVE/USDT": "aave_usdt",
        "CRV/USDT": "crv_usdt",
        "SNX/USDT": "snx_usdt",
        "COMP/USDT": "comp_usdt",
        "BAL/USDT": "bal_usdt",
        "YFI/USDT": "yfi_usdt",
        "SUSHI/USDT": "sushi_usdt",
        "PERP/USDT": "perp_usdt",
    }

    def __init__(self, base_url: str = None):
        """
        مقداردهی اولیه کلاینت LBank

        Args:
            base_url: آدرس پایه API (در صورت عدم ارائه، از پیش‌فرض استفاده می‌شود)
        """
        self.base_url = base_url or self.BASE_URLS[0]
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        دریافت یا ایجاد جلسه HTTP

        Returns:
            جلسه aiohttp برای درخواست‌های غیرهمزمان
        """
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """
        بستن جلسه HTTP
        """
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _make_request(
        self, endpoint: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ارسال درخواست به API LBank

        Args:
            endpoint: مسیر اندپوینت
            params: پارامترهای درخواست

        Returns:
            پاسخ API در قالب دیکشنری

        Raises:
            Exception: در صورت بروز خطا در درخواست
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"

        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"خطای HTTP: {response.status}")

                data = await response.json()

                # بررسی وجود خطا در پاسخ
                if isinstance(data, dict):
                    if data.get("error_code"):
                        raise Exception(f"خطای API: {data.get('msg')}")

                return data

        except aiohttp.ClientError as e:
            logger.error(f"خطا در اتصال به LBank: {e}")
            raise Exception(f"خطا در اتصال به سرور: {str(e)}")

    def _convert_lbank_symbol(self, symbol: str) -> str:
        """
        تبدیل نماد استاندارد به فرمت LBank

        Args:
            symbol: نماد به فرمت استاندارد مانند BTC/USDT

        Returns:
            نماد در فرمت LBank مانند btc_usdt
        """
        # حذف پسوندهای اضافی و تبدیل به حروف کوچک
        clean_symbol = symbol.upper().replace("-", "_").replace(" ", "_")

        # بررسی نگاشت مستقیم
        if clean_symbol in self.SYMBOL_MAPPING:
            return self.SYMBOL_MAPPING[clean_symbol]

        # تلاش برای تبدیل خودکار
        parts = clean_symbol.split("/")
        if len(parts) == 2:
            base = parts[0].lower()
            quote = parts[1].lower()
            return f"{base}_{quote}"

        # اگر فرمت شناخته شده نیست، به صورت کوچک برگردان
        return symbol.lower().replace("-", "_").replace(" ", "_")

    def _convert_timeframe(self, timeframe: str) -> str:
        """
        تبدیل تایم فریم استاندارد به فرمت LBank

        Args:
            timeframe: تایم فریم استاندارد مانند 1h, 4h, 1d

        Returns:
            تایم فریم در فرمت LBank
        """
        return self.TIMEFRAMES.get(timeframe.lower(), "hour1")

    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """
        تبدیل تایم فریم به ثانیه

        Args:
            timeframe: تایم فریم به فرمت LBank

        Returns:
            تعداد ثانیه‌های هر کندل
        """
        timeframe_map = {
            "minute1": 60,
            "minute5": 300,
            "minute15": 900,
            "minute30": 1800,
            "hour1": 3600,
            "hour4": 14400,
            "hour8": 28800,
            "hour12": 43200,
            "day1": 86400,
            "week1": 604800,
            "month1": 2592000,
        }
        return timeframe_map.get(timeframe, 3600)

    def _parse_kline_data(self, data: List[List[float]]) -> pd.DataFrame:
        """
        تبدیل داده‌های کندل استیک LBank به DataFrame

        Args:
            data: لیست داده‌های خام از API

        Returns:
            DataFrame با ستون‌های استاندارد OHLCV
        """
        if not data:
            return pd.DataFrame()

        # ایجاد لیست برای ذخیره داده‌ها
        records = []

        for candle in data:
            try:
                # فرمت داده LBank: [timestamp(ثانیه), open, high, low, close, volume]
                if len(candle) >= 6:
                    # timestamp در LBank بر حسب ثانیه است، نه میلی‌ثانیه
                    timestamp_sec = int(candle[0])
                    # برای سازگاری با سایر بخش‌های سیستم، timestamp را به میلی‌ثانیه تبدیل می‌کنیم
                    timestamp_ms = timestamp_sec * 1000
                    record = {
                        "timestamp": timestamp_ms,
                        "datetime": datetime.fromtimestamp(
                            timestamp_sec
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                    }
                    records.append(record)
            except (IndexError, ValueError) as e:
                logger.warning(f"خطا در پردازش کندل: {e}")
                continue

        # ایجاد DataFrame
        df = pd.DataFrame(records)

        if df.empty:
            return df

        # تنظیم ایندکس بر اساس زمان
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        return df

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 500,
        since: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        دریافت داده‌های OHLCV از صرافی LBank

        Args:
            symbol: نماد معاملاتی مانند BTC/USDT
            timeframe: تایم فریم کندل‌ها (پیش‌فرض: 1h)
            limit: تعداد کندل‌های درخواستی (1-2000)
            since: زمان شروع بر حسب timestamp میلی‌ثانیه

        Returns:
            DataFrame با داده‌های OHLCV
        """
        # تبدیل نماد و تایم فریم به فرمت LBank
        lbank_symbol = self._convert_lbank_symbol(symbol)
        lbank_timeframe = self._convert_timeframe(timeframe)

        # محدود کردن تعداد کندل‌ها
        limit = min(max(1, limit), 2000)

        # محاسبه timestamp
        # نکته مهم: پارامتر time در LBank باید زمان پایان بازه در گذشته باشد
        # یعنی باید زمانی را مشخص کنیم که کندل‌ها قبل از آن تمام شده‌اند
        tf_seconds = self._timeframe_to_seconds(lbank_timeframe)
        current_time = int(time.time())
        
        if since:
            # اگر زمان شروع مشخص شده، زمان پایان را محاسبه می‌کنیم
            time_param = int(since / 1000) + (limit * tf_seconds)
        else:
            # اگر زمان شروع مشخص نشده، از زمان فعلی استفاده می‌کنیم
            # برای دریافت limit کندل، زمان پایان باید در گذشته باشد
            # یعنی: زمان فعلی - (limit * ثانیه هر کندل) + (ثانیه هر کندل)
            # این تضمین می‌کند که کندل‌های کافی درخواست شوند
            time_param = current_time - (limit * tf_seconds) + tf_seconds

        # پارامترهای درخواست
        params = {
            "symbol": lbank_symbol,
            "size": limit,
            "type": lbank_timeframe,
            "time": str(time_param),
        }

        logger.info(
            f"درخواست داده‌های OHLCV از LBank: نماد={lbank_symbol}, "
            f"تایم فریم={lbank_timeframe}, تعداد={limit}, time={time_param}"
        )

        # ارسال درخواست
        response = await self._make_request("v2/kline.do", params)

        # پردازش و تبدیل داده‌ها
        if isinstance(response, dict):
            data = response.get("data", [])
        else:
            data = response if isinstance(response, list) else []

        df = self._parse_kline_data(data)

        if df.empty:
            logger.warning(f"هیچ داده‌ای برای {symbol} دریافت نشد")
        else:
            logger.info(
                f"{len(df)} کندل برای {symbol} دریافت شد. "
                f"بازه زمانی: {df.index[0]} تا {df.index[-1]}"
            )

        return df

    async def get_available_symbols(self) -> List[str]:
        """
        دریافت لیست نمادهای معاملاتی موجود

        Returns:
            لیست نمادهای موجود
        """
        try:
            response = await self._make_request("v2/currencyPairs.do", {})
            if isinstance(response, dict):
                data = response.get("data", [])
                return [item.get("symbol", "") for item in data if item.get("symbol")]
            return []
        except Exception as e:
            logger.error(f"خطا در دریافت لیست نمادها: {e}")
            return []

    async def get_ticker_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        دریافت قیمت فعلی یک نماد

        Args:
            symbol: نماد معاملاتی

        Returns:
            دیکشنری حاوی اطلاعات قیمت
        """
        lbank_symbol = self._convert_lbank_symbol(symbol)

        try:
            params = {"symbol": lbank_symbol}
            response = await self._make_request("v2/ticker.do", params)

            if isinstance(response, dict):
                data = response.get("data", [])
                if data and len(data) > 0:
                    ticker = data[0]
                    return {
                        "symbol": symbol,
                        "price": float(ticker.get("latestPrice", 0)),
                        "change_24h": float(ticker.get("changePercent24h", 0)),
                        "high_24h": float(ticker.get("high24h", 0)),
                        "low_24h": float(ticker.get("low24h", 0)),
                        "volume_24h": float(ticker.get("volume24h", 0)),
                    }
            return None
        except Exception as e:
            logger.error(f"خطا در دریافت قیمت {symbol}: {e}")
            return None


# تابع کمکی برای ایجاد نمونه کلاینت
def create_lbank_client(base_url: str = None) -> LBankClient:
    """
    ایجاد یک نمونه از کلاینت LBank

    Args:
        base_url: آدرس پایه API

    Returns:
        نمونه‌ای از LBankClient
    """
    return LBankClient(base_url)
