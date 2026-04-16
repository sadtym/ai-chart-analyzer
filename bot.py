"""
ربات تلگرام تحلیل هوشمند چارت - نسخه ۲ (سطح ۲)
پیاده‌سازی کامل با ویژگی‌های:
- تحلیل On-Chain (Glassnode)
- سیستم چندکاربره
- Backtesting استراتژی‌های SMC

Author: MiniMax Agent
"""

import os
import sys
import asyncio
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# بارگذاری تنظیمات از فایل .env
load_dotenv(Path(__file__).parent / ".env")

# اضافه کردن مسیر ماژول‌ها به path
MODULES_DIR = Path(__file__).parent / "modules"
sys.path.insert(0, str(MODULES_DIR))

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# وارد کردن aiohttp برای webhook (فقط در صورت نیاز)
try:
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
from aiogram.client.default import DefaultBotProperties
from aiogram.methods.send_message import SendMessage

from config import TELEGRAM_TOKEN, LOG_LEVEL, LOG_FILE, AUTO_SCAN_ENABLED, AUTO_SCAN_INTERVAL
from modules.image_processor import preprocess_image, validate_image, get_unique_filename, cleanup_old_images
from modules.ai_analyzer import ChartAnalyzer
from modules.signal_formatter import SignalFormatter
from modules.chart_annotator import annotate_chart_with_analysis
from modules.leverage_calculator import LeverageCalculator, RiskLevel, VolatilityLevel
from modules.mtf_market_scanner import MTFMarketScanner
from modules.smc_engine import SMCEngine, create_smc_analysis, calculate_mtf_bias, detect_confluence_zones, format_mtf_analysis_message, calculate_trade_levels, calculate_volume_profile
from modules.lbank_client import LBankClient
from modules.price_alerts import alert_manager
from database.db_manager import init_database, UserManager, AlertManagerDB, BacktestManager, WatchlistManager
from modules.user_manager.services import UserService, AccessControl, FeatureChecker
from modules.onchain.glassnode_api import OnChainAnalyzer
from modules.backtester.engine import BacktestEngine, get_backtest_engine
import database.db_manager as db_manager

# تنظیم لاگینگ
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# راه‌اندازی ربات و دپاچر
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()

# راه‌اندازی ماژول‌ها
analyzer = ChartAnalyzer()
formatter = SignalFormatter()
leverage_calculator = LeverageCalculator()
market_scanner = MTFMarketScanner(analyzer)

# راه‌اندازی کلاینت LBank
lbank_client = LBankClient()


# ==================== هندلرهای دستورات ====================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """پاسخ به دستور /start - ثبت‌نام کاربر"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        user_name = message.from_user.full_name
        
        # ثبت‌نام کاربر
        user = UserService.register_user(user_id, username, first_name)
        
        logger.info(f"کاربر ثبت‌نام شد: {user_name} (ID: {user_id})")
        
        # دریافت پروفایل کامل
        profile = UserService.get_profile(user_id)
        
        welcome_text = formatter.format_welcome_message()
        
        # ایجاد کیبورد شروع
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 شروع تحلیل", callback_data="start_analysis"),
                InlineKeyboardButton(text="👤 پروفایل", callback_data="show_profile")
            ],
            [
                InlineKeyboardButton(text="📖 راهنما", callback_data="show_help"),
                InlineKeyboardButton(text="🆙 ارتقا", callback_data="show_upgrade")
            ]
        ])
        
        # پیام خوش‌آمدگویی شخصی‌سازی‌شده
        welcome_msg = f"""
👋 **سلام {first_name}! خوش اومدی! 🎉**

✅ ثبت‌نام موفقیت‌آمیز!
🏷️ سطح دسترسی: **{UserService.get_level_name(user['access_level'])}**

{welcome_text}
        """
        
        await message.answer(welcome_msg, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطا در cmd_start: {e}")
        await message.answer("خطایی رخ داد. لطفاً مجدداً تلاش کنید.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """پاسخ به دستور /help"""
    help_text = formatter.format_help_message()
    await message.answer(help_text)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """پاسخ به دستور /stats - نمایش آمار (برای توسعه آینده)"""
    await message.answer("📊 این قابلیت به زودی اضافه می‌شود!")


@dp.message(Command("cleanup"))
async def cmd_cleanup(message: Message):
    """پاکسازی تصاویر قدیمی - فقط برای مدیر"""
    # بررسی اینکه کاربر مدیر است (در صورت نیاز)
    cleanup_old_images(max_age_hours=0)  # حذف همه تصاویر
    await message.answer("✅ تصاویر موقت پاکسازی شدند")


@dp.message(Command("leverage"))
async def cmd_leverage(message: Message):
    """دستور محاسبه اهرم"""
    leverage_help = """
🎚️ **دستور محاسبه اهرم**

📝 **نحوه استفاده:**
`/leverage [مبلغ] [ورود] [ضرر] [ریسک%] [اهرم]`

📊 **مثال:**
`/leverage 1000 1.0850 1.0820 2 10`

💡 **توضیح پارامترها:**
• مبلغ: موجودی حساب ($)
• ورود: قیمت ورود
• ضرر: قیمت حد ضرر
• ریسک%: درصد ریسک (1-5)
• اهرم: سطح اهرم (اختیاری، پیش‌فرض: 1x)

🔔 **یا عکس چارت ارسال کنید تا AI اهرم مناسب را پیشنهاد دهد!**
    """
    await message.answer(leverage_help)


# ==================== هندلرهای سطح ۲ ====================

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    """دستور /profile - نمایش پروفایل کاربر"""
    user_id = message.from_user.id
    
    try:
        profile = UserService.get_profile(user_id)
        
        if not profile:
            await message.answer("⚠️ شما ثبت‌نام نکرده‌اید. لطفاً /start را بزنید.")
            return
        
        profile_msg = UserService.format_profile_message(profile)
        await message.answer(profile_msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطا در نمایش پروفایل: {e}")
        await message.answer("❌ خطا در دریافت پروفایل")


@dp.message(Command("onchain"))
async def cmd_onchain(message: Message):
    """دستور /onchain - تحلیل On-Chain"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # بررسی دسترسی
    has_access, access_msg = FeatureChecker.require_onchain(user_id)
    if not has_access:
        await message.answer(access_msg, parse_mode='Markdown')
        return
    
    try:
        # پارس کردن ورودی
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        symbol = args[0].upper() if args else "BTC"
        
        # نگاشت نمادها
        symbol_map = {'BTC': 'BTC', 'ETH': 'ETH', 'SOL': 'SOL'}
        asset = symbol_map.get(symbol, 'BTC')
        
        # ارسال پیام "در حال تحلیل"
        analyzing_msg = await message.answer(
            f"📊 **در حال دریافت تحلیل On-Chain برای {asset}...**\n\n"
            "⏱️ لطفاً صبر کنید..."
        )
        
        # بررسی محدودیت روزانه
        remaining = AccessControl.check_daily_limit(user_id, 'onchain')
        if remaining <= 0:
            await analyzing_msg.edit_text(
                "🚫 محدودیت روزانه آنچین به اتمام رسید.\n"
                "برای ارتقا /upgrade را بزنید."
            )
            return
        
        # دریافت تحلیل
        analyzer = OnChainAnalyzer()
        analysis = analyzer.get_comprehensive_analysis(asset, 30)
        
        # ثبت درخواست
        AccessControl.log_request(user_id, 'onchain')
        
        # فرمت و ارسال نتیجه
        result_msg = analyzer.format_analysis_message(analysis)
        
        await analyzing_msg.delete()
        await message.answer(result_msg, parse_mode='Markdown')
        
        logger.info(f"تحلیل On-Chain تکمیل شد برای {user_name} - {asset}")
        
    except Exception as e:
        logger.error(f"خطا در تحلیل On-Chain: {e}")
        await message.answer(f"❌ خطا در تحلیل On-Chain: {str(e)}")


@dp.message(Command("backtest"))
async def cmd_backtest(message: Message):
    """دستور /backtest - تست استراتژی روی داده‌های تاریخی"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    # بررسی دسترسی
    has_access, access_msg = FeatureChecker.require_backtest(user_id)
    if not has_access:
        await message.answer(access_msg, parse_mode='Markdown')
        return
    
    try:
        # پارس کردن ورودی
        args = message.text.split()[1:]
        
        if len(args) < 2:
            help_text = """📊دستور Backtesting
📝نحوه استفاده:
/backtest [نماد] [استراتژی]
📊مثال‌ها:
/backtest BTC fvg_reversal - تست FVG Reversal
/backtest ETH ob_breakout - تست Order Block
/backtest BTC bos_continuation - تست BOS
🎯استراتژی‌های موجود:
- fvg_reversal - بازگشت از Fair Value Gap
- ob_breakout - شکست Order Block
- bos_continuation - ادامه روند پس از BOS
- smc_combo - ترکیبی از همه
⚠️نکته: تست روی ۱ سال داده تاریخی انجام می‌شود."""
            await message.answer(help_text, parse_mode=None)
            return
        
        symbol = args[0].upper()
        strategy = args[1].lower() if len(args) > 1 else 'fvg_reversal'
        
        # نگاشت نمادها
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        
        # ارسال پیام "در حال تست"
        testing_msg = await message.answer(
            f"🔄 در حال اجرای Backtesting...\n\n"
            f"📊 نماد: {symbol}\n"
            f"🎯 استراتژی: {strategy}\n\n"
            "⏱️ این عملیات حدود ۱۵-۳۰ ثانیه طول می‌کشد...",
            parse_mode=None
        )
        
        # اجرای بک‌تست
        engine = get_backtest_engine()
        result = engine.run_backtest(
            symbol=symbol,
            strategy_name=strategy,
            timeframe='1h',
            days=365,
            sl_percent=2.0,
            tp_percent=4.0
        )
        
        # ثبت درخواست
        AccessControl.log_request(user_id, 'backtest')
        
        # ذخیره نتیجه
        BacktestManager.save_result(
            user_id=user_id,
            symbol=symbol,
            strategy=strategy,
            timeframe='1h',
            start_date=result.start_date,
            end_date=result.end_date,
            results={
                'total_trades': result.total_trades,
                'win_rate': result.win_rate,
                'profit_percentage': result.profit_percent,
                'max_drawdown': result.max_drawdown
            }
        )
        
        # فرمت و ارسال نتیجه
        result_msg = engine.format_result_message(result)
        
        await testing_msg.delete()
        await message.answer(result_msg, parse_mode=None)
        
        logger.info(f"Backtest تکمیل شد برای {user_name}: {symbol} - {strategy}")
        
    except Exception as e:
        logger.error(f"خطا در Backtest: {e}")
        await message.answer(f"❌ خطا در Backtesting: {str(e)}")


@dp.message(Command("watchlist"))
async def cmd_watchlist(message: Message):
    """دستور /watchlist - مدیریت لیست ارزهای مورد علاقه"""
    user_id = message.from_user.id
    
    try:
        args = message.text.split()[1:]
        
        if not args:
            # نمایش لیست فعلی
            watchlist = UserService.get_watchlist(user_id)
            
            if not watchlist:
                await message.answer(
                    "📋 **لیست ارزهای شما**\n\n"
                    "خالی است!\n\n"
                    "📝 برای افزودن:\n"
                    "`/watchlist add BTC`\n"
                    "`/watchlist add ETH`"
                )
                return
            
            watchlist_msg = "📋 **لیست ارزهای مورد علاقه شما**\n\n"
            for i, symbol in enumerate(watchlist, 1):
                watchlist_msg += f"{i}. {symbol}\n"
            
            watchlist_msg += "\n💡 برای حذف:\n`/watchlist remove BTC`"
            
            await message.answer(watchlist_msg, parse_mode='Markdown')
            return
        
        action = args[0].lower()
        symbol = args[1].upper() if len(args) > 1 else ""
        
        if action in ['add', '+', 'افزودن']:
            if not symbol:
                await message.answer("❌ لطفاً نماد را وارد کنید. مثال: `/watchlist add BTC`")
                return
            
            success, msg = UserService.add_to_watchlist(user_id, symbol)
            await message.answer(msg)
            
        elif action in ['remove', 'delete', '-', 'حذف']:
            if not symbol:
                await message.answer("❌ لطفاً نماد را وارد کنید. مثال: `/watchlist remove BTC`")
                return
            
            success, msg = UserService.remove_from_watchlist(user_id, symbol)
            await message.answer(msg)
            
        else:
            await message.answer(
                "❌ دستور نامعتبر!\n\n"
                "📝 دستورات:\n"
                "`/watchlist` - نمایش لیست\n"
                "`/watchlist add BTC` - افزودن\n"
                "`/watchlist remove BTC` - حذف"
            )
            
    except Exception as e:
        logger.error(f"خطا در مدیریت Watchlist: {e}")
        await message.answer("❌ خطا در پردازش دستور")


@dp.message(Command("upgrade"))
async def cmd_upgrade(message: Message):
    """دستور /upgrade - اطلاعات ارتقای حساب"""
    user_id = message.from_user.id
    user = UserService.get_profile(user_id)
    level = user['access_level'] if user else 1
    
    upgrade_msg = """
👑 **ارتقای حساب - سطوح دسترسی**

━━━━━━━━━━━━━━━━━━━━━━

🆓 **سطح رایگان** (فعال)
• تحلیل چارت با AI
• ۳ تحلیل On-Chain / روز
• ۱ بک‌تست / روز
• ۵ هشدار قیمت

⭐ **سطح پریمیوم** (۵$/ماه)
• تمام امکانات رایگان
• ۲۰ تحلیل On-Chain / روز
• ۱۰ بک‌تست / روز
• ۲۰ هشدار قیمت
• هشدارهای هوشمند AI
• پشتیبانی优先

👑 **سطح VIP** (۱۵$/ماه)
• تمام امکانات پریمیوم
• بی‌نهایت تحلیل On-Chain
• بی‌نهایت بک‌تست
• استراتژی‌های اختصاصی
• سیگنال‌های روزانه
• پشتیبانی ۲۴/۷

━━━━━━━━━━━━━━━━━━━━━━

💳 **برای پرداخت و ارتقا:**
با @admin تماس بگیرید

🎁 **کد تخفیف اولین خرید:** WELCOME10
    """
    
    await message.answer(upgrade_msg, parse_mode='Markdown')


@dp.message(Command("mybacktests"))
async def cmd_my_backtests(message: Message):
    """دستور /mybacktests - نمایش تاریخچه بک‌تست‌ها"""
    user_id = message.from_user.id
    
    try:
        results = BacktestManager.get_user_results(user_id, limit=10)
        
        if not results:
            await message.answer(
                "📊 **تاریخچه بک‌تست‌ها**\n\n"
                "هنوز بک‌تستی انجام نداده‌اید.\n\n"
                "📝 مثال:\n"
                "`/backtest BTC fvg_reversal`"
            )
            return
        
        msg = "📊 **تاریخچه بک‌تست‌های شما**\n\n"
        
        for i, r in enumerate(results, 1):
            emoji = "🟢" if r['profit_percentage'] > 0 else "🔴"
            msg += f"{i}. {emoji} **{r['symbol']}** - {r['strategy']}\n"
            msg += f"   📈 سود: {r['profit_percentage']:.2f}% | 🎯 Win Rate: {r['win_rate']:.1f}%\n"
            msg += f"   📅 {r['created_at'][:10]}\n\n"
        
        await message.answer(msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"خطا در نمایش تاریخچه بک‌تست: {e}")
        await message.answer("❌ خطا در دریافت تاریخچه")


# ==================== هندلر هشدارهای قیمت ====================

@dp.message(Command("alert"))
async def cmd_alert(message: Message):
    """دستور تنظیم هشدار قیمت"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    try:
        # پارس کردن ورودی
        args = message.text.split()[1:]
        
        if len(args) < 3:
            help_text = """
🔔 **دستور تنظیم هشدار قیمت**

📝 **نحوه استفاده:**
`/alert [نماد] [قیمت] [شرط]`

📊 **مثال‌ها:**
`/alert BTC 95000 above` - هشدار وقتی BTC بالای 95000 برود
`/alert BTC 90000 below` - هشدار وقتی BTC زیر 90000 برود
`/alert ETH 3500 above` - هشدار برای اتریوم

💡 **نمادهای پشتیبانی شده:**
BTC, ETH, SOL, XRP, ADA, DOGE, LTC, LINK, DOT, MATIC

⚠️ **نکته:** هشدارها هر ۱ دقیقه بررسی می‌شوند.
            """
            await message.answer(help_text)
            return
        
        symbol = args[0].upper()
        target_price = float(args[1])
        condition = args[2].lower()
        
        if condition not in ['above', 'below']:
            await message.answer("❌ شرط باید 'above' یا 'below' باشد")
            return
        
        # ایجاد هشدار
        alert = alert_manager.create_alert(user_id, symbol, target_price, condition)
        
        emoji = "🟢" if condition == "above" else "🔴"
        
        success_msg = f"""
✅ **هشدار تنظیم شد!**

🔔 {emoji} **{symbol}**
📍 قیمت هدف: `${target_price:,.2f}`
📌 شرط: وقتی قیمت {condition} این سطح شود
🆔 ID: `{alert.id}`

💡 هشدار فعال شد. هنگام فعال شدن در تلگرام اطلاع‌رسانی می‌شود.
            """
        await message.answer(success_msg)
        logger.info(f"هشدار جدید برای {user_name}: {symbol} @ {target_price} ({condition})")
        
    except ValueError:
        await message.answer("❌ فرمت قیمت نامعتبر است. لطفاً عدد وارد کنید.")
    except Exception as e:
        logger.error(f"خطا در ایجاد هشدار: {e}")
        await message.answer(f"❌ خطا در تنظیم هشدار: {str(e)}")


@dp.message(Command("myalerts"))
async def cmd_my_alerts(message: Message):
    """نمایش هشدارهای کاربر"""
    user_id = message.from_user.id
    
    alert_list = alert_manager.format_alert_list(user_id)
    await message.answer(alert_list)


@dp.message(Command("delalert"))
async def cmd_del_alert(message: Message):
    """حذف هشدار"""
    user_id = message.from_user.id
    
    try:
        args = message.text.split()[1:]
        
        if not args:
            await message.answer("❌ لطفاً ID هشدار را وارد کنید.\nمثال: `/delalert abc12345`")
            return
        
        alert_id = args[0]
        
        if alert_manager.delete_alert(alert_id, user_id):
            await message.answer(f"✅ هشدار با ID `{alert_id}` حذف شد.")
        else:
            await message.answer("❌ هشدار یافت نشد یا متعلق به شما نیست.")
            
    except Exception as e:
        logger.error(f"خطا در حذف هشدار: {e}")
        await message.answer(f"❌ خطا در حذف هشدار: {str(e)}")


# ==================== هندلر تصاویر ====================

@dp.message(F.photo)
async def handle_chart(message: Message):
    """پردازش تصویر چارت ارسالی"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    logger.info(f"دریافت تصویر از کاربر {user_name} (ID: {user_id})")
    
    try:
        # 1. دریافت تصویر با بالاترین کیفیت
        photo = message.photo[-1]
        
        # 2. ذخیره موقت تصویر
        file_path = get_unique_filename(user_id)
        await bot.download(photo, destination=file_path)
        
        logger.info(f"تصویر ذخیره شد: {file_path}")
        
        # 3. اعتبارسنجی تصویر
        is_valid, validation_msg = validate_image(str(file_path))
        if not is_valid:
            logger.warning(f"اعتبارسنجی ناموفق: {validation_msg}")
            await message.answer(formatter.format_error_message(validation_msg))
            if os.path.exists(file_path):
                os.remove(file_path)
            return
        
        # 4. ارسال پیام "در حال تحلیل"
        analyzing_msg = await message.answer(formatter.format_analyzing_message())
        
        # 5. پیش‌پردازش تصویر
        base64_image = preprocess_image(str(file_path))
        
        # 6. تحلیل با هوش مصنوعی
        analysis_result = analyzer.analyze(base64_image)
        
        # 7. رسم علامت‌ها روی چارت (اگر خطا نباشد)
        annotated_chart_path = None
        if not analysis_result.get('error'):
            try:
                annotated_chart_path = annotate_chart_with_analysis(str(file_path), analysis_result)
                logger.info(f"چارت علامت‌گذاری شد: {annotated_chart_path}")
            except Exception as e:
                logger.warning(f"خطا در علامت‌گذاری چارت: {e}")
        
        # 8. فرمت‌بندی و ارسال سیگنال
        signal_text = formatter.format_signal(analysis_result)
        keyboard = formatter.create_keyboard()
        
        await analyzing_msg.delete()
        
        # ارسال پیام متنی سیگنال کامل
        await message.answer(signal_text, reply_markup=keyboard)
        logger.info("پیام سیگنال ارسال شد")
        
        # ارسال چارت علامت‌گذاری شده (اگر موجود باشد)
        if annotated_chart_path and os.path.exists(annotated_chart_path):
            try:
                await message.answer_photo(
                    photo=types.FSInputFile(annotated_chart_path),
                    caption="📊 چارت تحلیل شده با نقاط ورود/حد ضرر/حد سود",
                )
                logger.info("چارت علامت‌گذاری شده ارسال شد")
            except Exception as e:
                logger.warning(f"خطا در ارسال چارت علامت‌گذاری شده: {e}")
        else:
            logger.info("چارت علامت‌گذاری شده موجود نیست")
        
        logger.info(f"تحلیل تکمیل شد برای کاربر {user_name}")
        
    except Exception as e:
        logger.error(f"خطا در پردازش تصویر: {e}")
        error_msg = await message.answer(formatter.format_error_message(str(e)))
        # امکان حذف خودکار پیام خطا بعد از مدتی
    
    finally:
        # 9. حذف فایل‌های موقت
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"فایل موقت حذف شد: {file_path}")
            # حذف چارت علامت‌گذاری شده
            if 'annotated_chart_path' in locals() and annotated_chart_path and os.path.exists(annotated_chart_path):
                os.remove(annotated_chart_path)
                logger.info(f"چارت علامت‌گذاری شده حذف شد: {annotated_chart_path}")
        except Exception as e:
            logger.warning(f"خطا در حذف فایل‌های موقت: {e}")


# ==================== هندلرهای Callback ====================

@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    """پردازش کلیک‌های دکمه‌های شیشه‌ای"""
    try:
        action = callback.data
        user_name = callback.from_user.full_name
        
        logger.info(f"Callback دریافت شد از {user_name}: {action}")
        
        if action == "retry_analysis":
            await callback.message.answer("📸 لطفاً عکس چارت را مجدداً ارسال کنید")
            
        elif action == "show_help":
            help_text = formatter.format_help_message()
            await callback.message.edit_text(help_text, reply_markup=None)
            
        elif action == "start_analysis":
            await callback.message.answer("📸 عکس چارت خود را ارسال کنید")
            
        elif action == "save_signal":
            await callback.message.answer("💾 سیگنال در پروفایل شما ذخیره شد (قابلیت آینده)")
            
        elif action == "share_signal":
            # اشتراک‌گذاری سیگنال
            share_text = callback.message.text
            await bot.copy_message(
                chat_id=callback.from_user.id,
                from_chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
            
        elif action == "show_stats":
            await callback.message.answer("📊 آمار استفاده (به زودی)")
            
        elif action == "calculate_leverage":
            leverage_help = """
🎚️ **ماشین حساب اهرم**

برای محاسبه اهرم مناسب، اطلاعات زیر را ارسال کنید:

📝 **فرمت پیام:**
`محاسبه اهرم [مبلغ موجودی] [قیمت ورود] [حد ضرر] [درصد ریسک] [اهرم دلخواه]`

📊 **مثال:**
`محاسبه اهرم 1000 1.0850 1.0820 2 10`

💡 **توضیحات:**
- مبلغ موجودی: موجودی حساب شما
- قیمت ورود: قیمت ورود به معامله
- حد ضرر: قیمت حد ضرر
- درصد ریسک: درصد ریسک از موجودی (1-5%)
- اهرم دلخواه: سطح اهرم مورد نظر (اختیاری)

🔔 **یا می‌توانید فقط عکس چارت ارسال کنید تا AI اهرم مناسب را پیشنهاد دهد!**
            """
            await callback.message.answer(leverage_help)
            
        elif action == "risk_management":
            risk_help = """
⚠️ **راهنمای مدیریت ریسک با اهرم**

🎯 **قوانین طلایی:**
• هرگز بیش از 2% از موجودی را ریسک نکنید
• اهرم بالا = ریسک بالا
• در نوسان زیاد اهرم کمتری استفاده کنید

📊 **سطوح اهرم پیشنهادی:**
🟢 اعتماد بالا (80%+) → 10-15x
🟡 اعتماد متوسط (60-79%) → 5-10x  
🔴 اعتماد پایین (<60%) → 1-5x

💰 **مدیریت سرمایه:**
• حساب کوچک (زیر $500): اهرم کمتر
• حساب متوسط ($500-2000): اهرم متوسط
• حساب بزرگ (بالای $2000): اهرم بالاتر

⚠️ **هشدار مهم:**
اهرم می‌تواند سود و زیان را چند برابر کند!
همیشه حد ضرر را رعایت کنید.
            """
            await callback.message.answer(risk_help)
        
        elif action == "capital_management":
            # راهنمای مدیریت سرمایه
            capital_help = """
💰 **📊 مدیریت سرمایه حرفه‌ای**

برای محاسبه دقیق حجم معامله، اطلاعات زیر را ارسال کنید:

📝 **فرمت پیام:**
`مدیریت سرمایه [موجودی] [ورود] [حد ضرر] [هدف] [درصد ریسک] [روش]`

📊 **مثال‌ها:**

1️⃣ **Fixed Risk (1% ریسک):**
`مدیریت سرمایه 1000 840.54 837.50 845.80 1 fixed`

2️⃣ **Kelly Criterion:**
`مدیریت سرمایه 1000 840.54 837.50 845.80 1 kelly`

3️⃣ **Volatility-Adjusted:**
`مدیریت سرمایه 1000 840.54 837.50 845.80 1 volatility`

🎯 **روش‌های موجود:**
• `fixed` - Fixed Risk Percentage
• `kelly` - Kelly Criterion
• `volatility` - ATR-based sizing
• `optimal` - Optimal F

💡 **یا از دکمه‌های زیر استفاده کنید:**
            """
            # ایجاد کیبورد برای انتخاب پروفایل ریسک
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            risk_profiles = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🟢 محافظه‌کارانه", callback_data="risk_conservative"),
                    InlineKeyboardButton(text="🟡 متعادل", callback_data="risk_moderate")
                ],
                [
                    InlineKeyboardButton(text="🟠 تهاجمی", callback_data="risk_aggressive"),
                    InlineKeyboardButton(text="🔴 تنظیمات من", callback_data="risk_custom")
                ]
            ])
            
            await callback.message.answer(capital_help, reply_markup=risk_profiles)
        
        elif action == "risk_conservative":
            # پروفایل محافظه‌کارانه
            await callback.message.answer(formatter.format_capital_management_settings())
        
        # ========== callbacks سطح ۲ ==========
        elif action == "show_profile":
            # نمایش پروفایل کاربر
            profile = UserService.get_profile(callback.from_user.id)
            if profile:
                profile_msg = UserService.format_profile_message(profile)
                await callback.message.edit_text(profile_msg, parse_mode='Markdown')
            else:
                await callback.message.edit_text("⚠️ لطفاً /start را بزنید.")
            
        elif action == "show_upgrade":
            # نمایش اطلاعات ارتقا
            upgrade_msg = """
👑 **ارتقای حساب - سطوح دسترسی**

━━━━━━━━━━━━━━━━━━━━━━

🆓 **سطح رایگان** (فعال)
• تحلیل چارت با AI
• ۳ تحلیل On-Chain / روز
• ۱ بک‌تست / روز
• ۵ هشدار قیمت

⭐ **سطح پریمیوم** (۵$/ماه)
• تمام امکانات رایگان
• ۲۰ تحلیل On-Chain / روز
• ۱۰ بک‌تست / روز
• ۲۰ هشدار قیمت
• هشدارهای هوشمند AI

👑 **سطح VIP** (۱۵$/ماه)
• تمام امکانات پریمیوم
• بی‌نهایت تحلیل و بک‌تست
• سیگنال‌های روزانه
• پشتیبانی ۲۴/۷

━━━━━━━━━━━━━━━━━━━━━━

💳 برای پرداخت با @admin تماس بگیرید
            """
            await callback.message.edit_text(upgrade_msg, parse_mode='Markdown')
        
        # تأیید دریافت callback
        await callback.answer()
        
    except Exception as e:
        logger.error(f"خطا در پردازش callback: {e}")
        await callback.answer("خطایی رخ داد", show_alert=True)


# ==================== هندلر پیام‌های متنی ====================

@dp.message(F.text.startswith('/') == False)
async def handle_text(message: Message):
    """پردازش پیام‌های متنی (با قابلیت محاسبه اهرم)"""
    text = message.text.lower().strip()
    
    if text in ['سلام', 'hi', 'hello', 'hey']:
        await message.answer(f"👋 سلام {message.from_user.first_name}! عکس چارت ارسال کنید 📊")
    
    elif text in ['راهنما', 'help', '؟', '?']:
        help_text = formatter.format_help_message()
        await message.answer(help_text)
    
    elif text in ['شروع', 'start', 'شروع تحلیل']:
        await message.answer("📸 عکس چارت خود را برای تحلیل ارسال کنید")
    
    elif text.startswith('محاسبه اهرم'):
        await handle_leverage_calculation(message)
    
    elif text.startswith('مدیریت سرمایه'):
        await handle_capital_management(message)
    
    else:
        # پیام نامفهوم
        await message.answer(
            "🤔 متوجه نشدم! لطفاً عکس چارت ارسال کنید یا از دستور /help استفاده کنید."
        )


async def handle_leverage_calculation(message: Message):
    """هندلر محاسبه اهرم از پیام متنی"""
    try:
        # پارس کردن ورودی
        parts = message.text.split()
        if len(parts) < 5:
            await message.answer(
                "❌ فرمت نامعتبر!\n\n"
                "📝 فرمت صحیح:\n"
                "`محاسبه اهرم [مبلغ] [ورود] [ضرر] [ریسک%] [اهرم]`\n\n"
                "📊 مثال:\n"
                "`محاسبه اهرم 1000 1.0850 1.0820 2 10`"
            )
            return
        
        # استخراج مقادیر
        account_balance = float(parts[1])
        entry_price = float(parts[2])
        stop_loss = float(parts[3])
        risk_percent = float(parts[4])
        leverage = float(parts[5]) if len(parts) > 5 else 1.0
        
        # محاسبه پوزیشن
        calc = leverage_calculator.calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            account_balance=account_balance,
            risk_percent=risk_percent,
            leverage=leverage
        )
        
        # فرمت و ارسال نتیجه
        result_text = leverage_calculator.format_position_calculation(calc)
        await message.answer(result_text)
        
    except ValueError:
        await message.answer("❌ لطفاً اعداد معتبر وارد کنید!")
    except Exception as e:
        await message.answer(f"❌ خطا در محاسبه: {str(e)}")


async def handle_capital_management(message: Message):
    """هندلر مدیریت سرمایه از پیام متنی"""
    try:
        from modules.capital_manager import CapitalManager
        
        # پارس کردن ورودی
        parts = message.text.split()
        if len(parts) < 6:
            await message.answer(
                "❌ فرمت نامعتبر!\n\n"
                "📝 فرمت صحیح:\n"
                "`مدیریت سرمایه [موجودی] [ورود] [حد ضرر] [هدف] [ریسک%] [روش]`\n\n"
                "📊 مثال:\n"
                "`مدیریت سرمایه 1000 840.54 837.50 845.80 1 fixed`\n\n"
                "🎯 روش‌ها: fixed, kelly, volatility, optimal"
            )
            return
        
        # استخراج مقادیر
        capital = float(parts[1])
        entry_price = float(parts[2])
        stop_loss = float(parts[3])
        take_profit = float(parts[4])
        risk_percent = float(parts[5])
        method = parts[6].lower() if len(parts) > 6 else 'fixed'
        
        # ایجاد مدیر سرمایه
        manager = CapitalManager(total_capital=capital, risk_per_trade=risk_percent)
        
        # محاسبه با روش مناسب
        if method == 'kelly':
            # برای Kelly نیاز به آمار داریم
            manager.update_stats(win_rate=0.55, avg_win=100, avg_loss=50)
            result = manager.calculate_kelly_criterion(entry_price, stop_loss, take_profit)
        elif method == 'volatility':
            result = manager.calculate_volatility_adjusted(entry_price, stop_loss, atr=0.5, risk_percentage=risk_percent)
        elif method == 'optimal':
            manager.update_stats(win_rate=0.55, avg_win=100, avg_loss=50)
            result = manager.calculate_optimal_f(entry_price, stop_loss)
        else:
            result = manager.calculate_fixed_risk(entry_price, stop_loss, risk_percent)
        
        # فرمت و ارسال نتیجه
        result_text = manager.format_result_message(result)
        await message.answer(result_text, parse_mode=None)
        
    except ValueError:
        await message.answer("❌ لطفاً اعداد معتبر وارد کنید!")
    except Exception as e:
        await message.answer(f"❌ خطا در محاسبه: {str(e)}")


# ==================== هندلر اسکن بازار ====================

@dp.message(Command("scan"))
async def cmd_scan_market(message: Message):
    """دستور /scan - اسکن دستی بازار"""
    user_name = message.from_user.full_name
    logger.info(f"📊 درخواست اسکن بازار از {user_name}")
    
    try:
        # ارسال پیام "در حال اسکن"
        scanning_msg = await message.answer(
            "🔍 **در حال اسکن بازار...**\n\n"
            "📈 بررسی ۱۵ ارز برتر...\n"
            "⏱️ این عملیات حدود ۳۰ ثانیه طول می‌کشد..."
        )
        
        # اجرای اسکن
        scan_result = await market_scanner.scan_market(min_confidence=60)
        
        # فرمت و ارسال نتیجه
        report = market_scanner.format_scan_report(scan_result)
        
        await scanning_msg.edit_text(report, parse_mode='HTML')
        logger.info(f"✅ اسکن بازار تکمیل شد برای {user_name}")
        
    except Exception as e:
        logger.error(f"❌ خطا در اسکن بازار: {e}")
        await message.answer(f"❌ خطا در اسکن بازار: {str(e)}")


# ==================== هندلر SMC چندتایم فریم ====================

@dp.message(Command("smc"))
async def cmd_smc_analysis(message: Message):
    """دستور /smc - تحلیل کامل SMC چندتایم فریم (Multi-Timeframe)"""
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    logger.info(f"🎯 درخواست تحلیل MTF SMC از {user_name}")

    try:
        # دریافت نماد از پیام (اختیاری)
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        symbol = args[0].upper() if args else "BTC"

        # نگاشت نمادهای رایج به نمادهای LBank
        symbol_mapping = {
            "BTC": "BTC/USDT",
            "BITCOIN": "BTC/USDT",
            "ETH": "ETH/USDT",
            "ETHEREUM": "ETH/USDT",
            "SOL": "SOL/USDT",
            "SOLANA": "SOL/USDT",
            "XRP": "XRP/USDT",
            "ADA": "ADA/USDT",
            "DOGE": "DOGE/USDT",
            "DOT": "DOT/USDT",
            "MATIC": "MATIC/USDT",
            "LTC": "LTC/USDT",
            "LINK": "LINK/USDT",
            "UNI": "UNI/USDT",
            "ATOM": "ATOM/USDT",
            "XMR": "XMR/USDT",
            "BCH": "BCH/USDT",
            "ETC": "ETC/USDT",
            "FIL": "FIL/USDT",
            "TRX": "TRX/USDT",
            "AVAX": "AVAX/USDT",
            "SHIB": "SHIB/USDT",
            "ARB": "ARB/USDT",
            "OP": "OP/USDT",
        }

        # تبدیل نماد به فرمت استاندارد
        if symbol in symbol_mapping:
            lbank_symbol = symbol_mapping[symbol]
        elif "/" in symbol:
            lbank_symbol = symbol.upper()
        else:
            lbank_symbol = f"{symbol.upper()}/USDT"

        # ارسال پیام "در حال تحلیل"
        analyzing_msg = await message.answer(
            f"🎯 تحلیل MTF SMC برای {lbank_symbol.replace('/USDT', '')}\n\n"
            "📊 دریافت داده‌های ۳ تایم‌فریم (1d, 4h, 1h)...\n"
            "⏱️ لطفاً صبر کنید (حدود ۵ ثانیه)..."
        )

        # تایم فریم‌ها برای تحلیل
        timeframes = ['1d', '4h', '1h']
        results = {}
        errors = []

        # دریافت و تحلیل هر تایم فریم
        for i, tf in enumerate(timeframes):
            try:
                # به‌روزرسانی پیام
                await analyzing_msg.edit_text(
                    f"🎯 تحلیل MTF SMC برای {lbank_symbol.replace('/USDT', '')}\n\n"
                    f"📥 دریافت داده‌های تایم‌فریم {tf}...\n"
                    f"({i+1}/3)\n"
                    "⏱️ لطفاً صبر کنید..."
                )

                # دریافت داده از LBank
                df = await lbank_client.fetch_ohlcv(
                    symbol=lbank_symbol,
                    timeframe=tf,
                    limit=500
                )

                if df.empty:
                    errors.append(f"هیچ داده‌ای برای تایم‌فریم {tf} دریافت نشد")
                    continue

                # تحلیل SMC
                smc_result = create_smc_analysis(df)
                results[tf] = smc_result

                # قیمت فعلی از آخرین کندل
                current_price = df['close'].iloc[-1]
                if tf == '1h':
                    current_price = current_price

                # تأخیر برای جلوگیری از ریت‌لیمیت
                if i < len(timeframes) - 1:
                    await asyncio.sleep(0.3)

            except Exception as e:
                logger.error(f"خطا در تحلیل تایم‌فریم {tf}: {e}")
                errors.append(f"خطا در تحلیل {tf}: {str(e)}")

        # بررسی حداقل یک تایم فریم موفق
        if not results:
            await analyzing_msg.edit_text(
                f"❌ خطا در دریافت داده‌ها:\n" +
                "\n".join(errors) +
                "\n\n💡 لطفاً مجدداً تلاش کنید."
            )
            return

        # محاسبه بایاس چندتایم فریم
        await analyzing_msg.edit_text(
            f"🎯 تحلیل MTF SMC برای {lbank_symbol.replace('/USDT', '')}\n\n"
            "🔄 ترکیب نتایج و محاسبه همگرایی...\n"
            "⏱️ لحظه‌ای..."
        )

        bias = calculate_mtf_bias(results)

        # شناسایی نواحی همگرا
        confluence = detect_confluence_zones(results)

        # محاسبه سطوح معاملاتی
        trade = calculate_trade_levels(
            symbol=lbank_symbol.replace('/USDT', ''),
            current_price=current_price,
            bias=bias,
            confluence=confluence,
            results=results
        )

        # قیمت فعلی
        if '1h' in results and results['1h']:
            current_price = results['1h'].get('market_condition', {}).get('current_price', 0)

        # فرمت و ارسال نتیجه
        await analyzing_msg.delete()

        result_text = format_mtf_analysis_message(
            symbol=lbank_symbol.replace('/USDT', ''),
            price=current_price,
            bias=bias,
            confluence=confluence,
            results=results,
            trade=trade
        )

        await message.answer(result_text, parse_mode=None)
        logger.info(f"✅ تحلیل MTF SMC تکمیل شد برای {user_name} - بایاس: {bias['direction']}")

    except Exception as e:
        logger.error(f"❌ خطا در تحلیل MTF SMC: {e}")
        await message.answer(f"❌ خطا در تحلیل SMC: {str(e)}")



# ==================== هندلر داده‌های فاندامنتال و کلان ====================

@dp.message(Command("macro"))
async def cmd_macro_data(message: Message):
    """دستور /macro - نمایش داده‌های کلان اقتصادی"""
    user_name = message.from_user.full_name
    logger.info(f"🏦 درخواست داده‌های کلان از {user_name}")

    try:
        from modules.fundamental_data import fundamental_manager
        
        loading_msg = await message.answer(
            "🏦 دریافت داده‌های کلان اقتصادی...\n"
            "⏱️ لطفاً صبر کنید..."
        )

        macro_data = await fundamental_manager.get_macro_data()
        result_text = fundamental_manager.format_macro_message(macro_data)
        
        await loading_msg.delete()
        await message.answer(result_text, parse_mode=None)
        logger.info(f"✅ داده‌های کلان ارسال شد برای {user_name}")

    except Exception as e:
        logger.error(f"❌ خطا در دریافت داده‌های کلان: {e}")
        await message.answer(f"❌ خطا: {str(e)}")


@dp.message(Command("fund"))
async def cmd_fundamentals(message: Message):
    """دستور /fund - نمایش داده‌های فاندامنتال ارز دیجیتال"""
    user_name = message.from_user.full_name
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    symbol = args[0].upper() if args else "BTC"
    
    logger.info(f"💎 درخواست فاندامنتال {symbol} از {user_name}")

    try:
        from modules.fundamental_data import fundamental_manager
        
        loading_msg = await message.answer(
            f"💎 دریافت داده‌های فاندامنتال {symbol}...\n"
            "⏱️ لطفاً صبر کنید..."
        )

        fund_data = await fundamental_manager.get_crypto_fundamentals(symbol)
        result_text = fundamental_manager.format_fundamentals_message(fund_data)
        
        await loading_msg.delete()
        await message.answer(result_text, parse_mode=None)
        logger.info(f"✅ فاندامنتال {symbol} ارسال شد")

    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        await message.answer(f"❌ خطا: {str(e)}")


@dp.message(Command("analyze_full"))
async def cmd_full_analysis(message: Message):
    """دستور /analyze_full - تحلیل کامل (تکنیکال + فاندامنتال + کلان)"""
    user_name = message.from_user.full_name
    logger.info(f"📊 درخواست تحلیل کامل از {user_name}")

    try:
        from modules.fundamental_data import fundamental_manager
        from modules.smc_engine import create_smc_analysis
        
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        symbol = args[0].upper() if args else "BTC"

        symbol_mapping = {
            "BTC": "BTC/USDT", "BITCOIN": "BTC/USDT",
            "ETH": "ETH/USDT", "ETHEREUM": "ETH/USDT",
            "SOL": "SOL/USDT", "SOLANA": "SOL/USDT",
        }
        
        lbank_symbol = symbol_mapping.get(symbol, f"{symbol}/USDT")
        if "/" not in lbank_symbol:
            lbank_symbol = f"{lbank_symbol}/USDT"

        analyzing_msg = await message.answer(
            f"📊 تحلیل کامل {symbol.replace('/USDT', '')}\n\n"
            "🔄 دریافت داده‌ها...\n"
            "⏱️ لطفاً صبر کنید..."
        )

        await analyzing_msg.edit_text(
            f"📊 تحلیل کامل {symbol.replace('/USDT', '')}\n\n"
            "📈 تحلیل تکنیکال SMC...\n"
            "⏱️ صبر کنید..."
        )

        try:
            df = await lbank_client.fetch_ohlcv(
                symbol=lbank_symbol,
                timeframe='1h',
                limit=500
            )
            if df.empty:
                raise ValueError("هیچ داده‌ای دریافت نشد")
        except Exception as e:
            await analyzing_msg.edit_text(f"❌ خطا: {str(e)}")
            return

        smc_results = create_smc_analysis(df)
        current_price = df['close'].iloc[-1]

        await analyzing_msg.edit_text(
            f"📊 تحلیل کامل {symbol.replace('/USDT', '')}\n\n"
            "💎 دریافت فاندامنتال...\n"
            "🏦 دریافت کلان...\n"
            "⏱️ صبر کنید..."
        )

        full_data = await fundamental_manager.get_full_analysis(
            symbol=symbol.replace('/USDT', ''),
            smc_results=smc_results,
            current_price=current_price
        )

        await analyzing_msg.delete()

        summary_text = fundamental_manager.format_combined_message(full_data)
        await message.answer(summary_text, parse_mode=None)
        
        if full_data.macro and full_data.macro.interest_rate > 0:
            macro_details = fundamental_manager.format_macro_message(full_data.macro)
            await message.answer(macro_details, parse_mode=None)
        
        if full_data.crypto_fundamentals and full_data.crypto_fundamentals.market_cap > 0:
            fund_details = fundamental_manager.format_fundamentals_message(full_data.crypto_fundamentals)
            await message.answer(fund_details, parse_mode=None)
        
        if full_data.smc_results:
            bias = full_data.smc_results.get('bias', {})
            direction = bias.get('direction', 'NEUTRAL')
            confidence = bias.get('confidence', 0)
            
            tech_text = (
                f"📈 تحلیل تکنیکال (SMC)\n"
                f"{'-' * 25}\n\n"
                f"🎯 جهت: {direction}\n"
                f"📊 اعتماد: {confidence}%\n"
                f"💰 قیمت: ${current_price:,.4f}"
            )
            await message.answer(tech_text, parse_mode=None)
        
        logger.info(f"✅ تحلیل کامل تکمیل شد")

    except Exception as e:
        logger.error(f"❌ خطا در تحلیل کامل: {e}")
        await message.answer(f"❌ خطا: {str(e)}")


@dp.message(Command("ai"))
async def cmd_ai_analysis(message: Message):
    """دستور /ai - تحلیل هوشمند ترکیبی با AI + سیگنال معاملاتی"""
    user_name = message.from_user.full_name
    logger.info(f"🤖 درخواست تحلیل AI از {user_name}")

    try:
        from modules.ai_integration import ai_integrated_analyzer
        from modules.ai_signal_generator import ai_signal_generator
        from modules.fundamental_data import fundamental_manager
        from modules.lbank_client import create_lbank_client
        from modules.smc_engine import create_smc_analysis

        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        symbol = args[0].upper() if args else "BTC"

        symbol_mapping = {
            "BTC": "BTC/USDT", "BITCOIN": "BTC/USDT",
            "ETH": "ETH/USDT", "ETHEREUM": "ETH/USDT",
            "SOL": "SOL/USDT", "SOLANA": "SOL/USDT",
        }

        lbank_symbol = symbol_mapping.get(symbol, f"{symbol}/USDT")
        if "/" not in lbank_symbol:
            lbank_symbol = f"{lbank_symbol}/USDT"

        # پیام بارگذاری
        loading_msg = await message.answer(
            f"🤖 تحلیل هوشمند ترکیبی {symbol.replace('/USDT', '')}\n\n"
            "🔄 ترکیب داده‌های کلان، فاندامنتال و تکنیکال...\n"
            "🎯 محاسبه سطوح معاملاتی...\n"
            "🧠 پردازش توسط هوش مصنوعی...\n"
            "⏱️ لطفاً صبر کنید..."
        )

        # ایجاد نمونه کلاینت LBank
        lbank_client = create_lbank_client()
        
        # دریافت داده‌های تکنیکال
        await loading_msg.edit_text(
            f"🤖 تحلیل هوشمند ترکیبی {symbol.replace('/USDT', '')}\n\n"
            "📈 دریافت داده‌های تکنیکال (SMC)...\n"
            "⏱️ صبر کنید..."
        )
        
        try:
            df = await lbank_client.fetch_ohlcv(
                symbol=lbank_symbol,
                timeframe='1h',
                limit=500
            )
            if df.empty:
                raise ValueError("هیچ داده‌ای دریافت نشد")
        except Exception as e:
            await loading_msg.edit_text(f"❌ خطا در دریافت داده‌های تکنیکال: {str(e)}")
            return

        smc_results = create_smc_analysis(df)
        current_price = df['close'].iloc[-1]

        # دریافت داده‌های فاندامنتال و کلان
        await loading_msg.edit_text(
            f"🤖 تحلیل هوشمند ترکیبی {symbol.replace('/USDT', '')}\n\n"
            "💎 دریافت داده‌های فاندامنتال...\n"
            "🏦 دریافت داده‌های کلان...\n"
            "⏱️ لحظه‌ای..."
        )

        # دریافت داده‌های فاندامنتال
        fund_data = await fundamental_manager.get_crypto_fundamentals(symbol.replace('/USDT', ''))
        fund_dict = None
        if fund_data:
            fund_dict = {
                'market_cap': fund_data.market_cap,
                'tvl': fund_data.tvl,
                'market_cap_change_24h': fund_data.market_cap_change_24h
            }

        # دریافت داده‌های کلان
        macro_data_obj = await fundamental_manager.get_macro_data()
        macro_dict = None
        if macro_data_obj:
            macro_dict = {
                'interest_rate': macro_data_obj.interest_rate,
                'dxy': macro_data_obj.dxy,
                'm2_change': macro_data_obj.m2_change,
                'cpi_change': macro_data_obj.cpi_change
            }

        # تولید سیگنال معاملاتی هوشمند
        await loading_msg.edit_text(
            f"🤖 تحلیل هوشمند ترکیبی {symbol.replace('/USDT', '')}\n\n"
            "🔄 تولید سیگنال معاملاتی با AI...\n"
            "🧠 تحلیل نهایی توسط Gemini...\n"
            "⏱️ تقریباً آماده..."
        )

        trading_signal = await ai_signal_generator.generate_ai_signal(
            symbol=symbol.replace('/USDT', ''),
            current_price=current_price,
            smc_result=smc_results,
            macro_data=macro_dict,
            fundamental_data=fund_dict
        )

        # تحلیل ترکیبی AI
        result = await ai_integrated_analyzer.analyze_combined(
            symbol=symbol.replace('/USDT', ''),
            smc_result=smc_results,
            current_price=current_price
        )

        # فرمت و ارسال پیام‌ها
        await loading_msg.delete()
        
        # ارسال سیگنال معاملاتی هوشمند
        signal_message = ai_signal_generator.format_signal_message(trading_signal)
        await message.answer(signal_message, parse_mode='Markdown')
        
        # ارسال تحلیل AI
        ai_message = ai_integrated_analyzer.format_combined_message(result)
        await message.answer(ai_message, parse_mode=None)

        logger.info(f"✅ تحلیل AI و سیگنال تکمیل شد: {symbol} - AI:{result.signal.value}, Signal:{trading_signal.direction.value}")

    except Exception as e:
        logger.error(f"❌ خطا در تحلیل AI: {e}")
        import traceback
        traceback.print_exc()
        await message.answer(f"❌ خطا: {str(e)}")


@dp.message(Command("signal"))
async def cmd_signal(message: Message):
    """دستور /signal - دریافت سیگنال معاملاتی هوشمند با AI"""
    user_name = message.from_user.full_name
    logger.info(f"🎯 درخواست سیگنال از {user_name}")

    try:
        from modules.ai_signal_generator import ai_signal_generator
        from modules.fundamental_data import fundamental_manager
        from modules.lbank_client import create_lbank_client
        from modules.smc_engine import create_smc_analysis

        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        symbol = args[0].upper() if args else "BTC"

        symbol_mapping = {
            "BTC": "BTC/USDT", "BITCOIN": "BTC/USDT",
            "ETH": "ETH/USDT", "ETHEREUM": "ETH/USDT",
            "SOL": "SOL/USDT", "SOLANA": "SOL/USDT",
        }

        lbank_symbol = symbol_mapping.get(symbol, f"{symbol}/USDT")
        if "/" not in lbank_symbol:
            lbank_symbol = f"{lbank_symbol}/USDT"

        # پیام بارگذاری
        loading_msg = await message.answer(
            f"🎯 تولید سیگنال {symbol.replace('/USDT', '')}\n\n"
            "📊 تحلیل تکنیکال SMC...\n"
            "💎 بررسی فاندامنتال...\n"
            "🏦 تحلیل کلان اقتصادی...\n"
            "⏱️ لطفاً صبر کنید..."
        )

        # ایجاد نمونه کلاینت LBank
        lbank_client = create_lbank_client()
        
        # دریافت داده‌های تکنیکال
        await loading_msg.edit_text(
            f"🎯 تولید سیگنال {symbol.replace('/USDT', '')}\n\n"
            "📈 دریافت داده‌های تکنیکال (SMC)...\n"
            "⏱️ صبر کنید..."
        )
        
        df = await lbank_client.fetch_ohlcv(
            symbol=lbank_symbol,
            timeframe='1h',
            limit=500
        )
        
        if df.empty:
            await loading_msg.edit_text(f"❌ خطا: هیچ داده‌ای دریافت نشد")
            return
        
        smc_result = create_smc_analysis(df)
        current_price = df['close'].iloc[-1]

        # دریافت داده‌های فاندامنتال و کلان
        await loading_msg.edit_text(
            f"🎯 تولید سیگنال {symbol.replace('/USDT', '')}\n\n"
            "💎 دریافت داده‌های فاندامنتال...\n"
            "🏦 دریافت داده‌های کلان...\n"
            "⏱️ لحظه‌ای..."
        )

        # دریافت داده‌های فاندامنتال
        fund_data = await fundamental_manager.get_crypto_fundamentals(symbol.replace('/USDT', ''))
        fund_dict = None
        if fund_data:
            fund_dict = {
                'market_cap': fund_data.market_cap,
                'tvl': fund_data.tvl,
                'market_cap_change_24h': fund_data.market_cap_change_24h
            }

        # دریافت داده‌های کلان
        macro_data_obj = await fundamental_manager.get_macro_data()
        macro_dict = None
        if macro_data_obj:
            macro_dict = {
                'interest_rate': macro_data_obj.interest_rate,
                'dxy': macro_data_obj.dxy,
                'm2_change': macro_data_obj.m2_change,
                'cpi_change': macro_data_obj.cpi_change
            }

        # تولید سیگنال هوشمند با AI
        await loading_msg.edit_text(
            f"🎯 تولید سیگنال هوشمند {symbol.replace('/USDT', '')}\n\n"
            "🔄 تحلیل توسط Gemini AI...\n"
            "📊 محاسبه سطوح معاملاتی...\n"
            "⏱️ تقریباً آماده..."
        )

        signal = await ai_signal_generator.generate_ai_signal(
            symbol=symbol.replace('/USDT', ''),
            current_price=current_price,
            smc_result=smc_result,
            macro_data=macro_dict,
            fundamental_data=fund_dict
        )

        # فرمت و ارسال پیام سیگنال
        await loading_msg.delete()
        signal_message = ai_signal_generator.format_signal_message(signal)
        await message.answer(signal_message, parse_mode='Markdown')

        logger.info(f"✅ سیگنال AI تولید شد: {symbol} - {signal.direction.value}")

    except Exception as e:
        logger.error(f"❌ خطا در تولید سیگنال: {e}")
        import traceback
        traceback.print_exc()
        await message.answer(f"❌ خطا: {str(e)}")


async def send_auto_scan():
    """ارسال اسکن خودکار به همه کاربران"""
    try:
        logger.info("🔄 اجرای اسکن خودکار بازار...")
        
        scan_result = await market_scanner.scan_market(min_confidence=65)
        
        if scan_result.get('success') and scan_result.get('opportunities'):
            report = market_scanner.format_scan_report(scan_result)
            
            # ارسال به کانال یا مدیر (در اینجا فقط لاگ)
            logger.info(f"✅ {len(scan_result['opportunities'])} فرصت یافت شد")
            
    except Exception as e:
        logger.error(f"❌ خطا در اسکن خودکار: {e}")


# ==================== تابع اصلی ====================

async def main():
    """اجرای اصلی ربات"""
    try:
        logger.info("🚀 ربات در حال راه‌اندازی...")
        
        # راه‌اندازی دیتابیس (سطح ۲)
        try:
            init_database()
            logger.info("✅ دیتابیس سطح ۲ راه‌اندازی شد")
        except Exception as db_error:
            logger.error(f"❌ خطا در راه‌اندازی دیتابیس: {db_error}")
        
        # بررسی اتصال به تلگرام
        bot_info = await bot.get_me()
        logger.info(f"✅ ربات متصل شد: @{bot_info.username}")
        
        # راه‌اندازی Scheduler برای اسکن خودکار
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            
            scheduler = AsyncIOScheduler()
            
            # بررسی فعال بودن اسکن خودکار
            auto_scan = os.getenv("AUTO_SCAN_ENABLED", "false").lower() == "true"
            scan_interval = int(os.getenv("AUTO_SCAN_INTERVAL", "60"))
            
            if auto_scan:
                scheduler.add_job(
                    send_auto_scan,
                    trigger=IntervalTrigger(minutes=scan_interval),
                    id='auto_market_scan',
                    name='اسکن خودکار بازار',
                    replace_existing=True
                )
                scheduler.start()
                logger.info(f"✅ Scheduler راه‌اندازی شد - اسکن هر {scan_interval} دقیقه")
            else:
                logger.info("ℹ️ اسکن خودکار غیرفعال است (برای فعال‌سازی AUTO_SCAN_ENABLED=true تنظیم کنید)")
                
        except ImportError:
            logger.warning("⚠️ APScheduler نصب نیست! اسکن خودکار غیرفعال است")
        
        # شروع دریافت پیام‌ها
        webhook_url = os.getenv("WEBHOOK_URL")
        if webhook_url:
            # حالت Production - Webhook
            if not AIOHTTP_AVAILABLE:
                raise RuntimeError("❌ aiohttp برای حالت webhook نصب نیست! pip install aiohttp")
            
            logger.info("🌐 اجرای در حالت Webhook (Production)")
            logger.info(f"📡 Webhook URL: {webhook_url}")
            
            # تنظیم webhook
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True
            )
            logger.info("✅ Webhook تنظیم شد")
            
            # راه‌اندازی اپلیکیشن
            app = web.Application()
            SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="")
            
            # اجرای سرور
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
            await site.start()
            
            logger.info("✅ سرور Webhook آماده دریافت درخواست‌ها است")
            
            # نگه داشتن برنامه
            try:
                await asyncio.Future()  # بی‌نهایت
            except KeyboardInterrupt:
                logger.info("⚠️ سرور متوقف شد")
            
        else:
            # حالت Development - Polling
            logger.info("💻 اجرای در حالت Polling (Development)")
            await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("⚠️ ربات متوقف شد (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ خطای بحرانی: {e}")
    finally:
        logger.info("👋 خداحافظ!")


# نقطه شروع برنامه
if __name__ == "__main__":
    # بررسی اجرای همزمان
    lock_file = Path(__file__).parent / "bot.lock"
    if lock_file.exists():
        logger.error("❌ ربات در حال اجرا است! لطفاً ابتدا نمونه قبلی را متوقف کنید.")
        logger.error(f"برای متوقف کردن: rm {lock_file}")
        sys.exit(1)
    
    # ایجاد فایل قفل
    try:
        lock_file.write_text(str(os.getpid()))
        logger.info("🔒 فایل قفل ایجاد شد")
    except Exception as e:
        logger.error(f"❌ خطا در ایجاد فایل قفل: {e}")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⚠️ برنامه متوقف شد")
    finally:
        # حذف فایل قفل
        if lock_file.exists():
            lock_file.unlink()
            logger.info("🔓 فایل قفل حذف شد")
