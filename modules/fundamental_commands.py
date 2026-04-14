# -*- coding: utf-8 -*-
"""
دستورات فاندامنتال و کلان اقتصادی
Fundamental & Macro Commands
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

import logging
logger = logging.getLogger(__name__)

# ایجاد روتر
fundamental_router = Router()

# ==================== هندلرهای داده‌های فاندامنتال و کلان ====================

@fundamental_router.message(Command("macro"))
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


@fundamental_router.message(Command("fund"))
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


@fundamental_router.message(Command("analyze_full"))
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

        # وارد کردن lbank_client
        from modules.lbank_client import lbank_client

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


@fundamental_router.message(Command("ai"))
async def cmd_ai_analysis(message: Message):
    """دستور /ai - تحلیل هوشمند ترکیبی با AI"""
    user_name = message.from_user.full_name
    logger.info(f"🤖 درخواست تحلیل AI از {user_name}")

    try:
        from modules.ai_integration import ai_integrated_analyzer
        from modules.lbank_client import lbank_client

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
            "🧠 پردازش توسط هوش مصنوعی...\n"
            "⏱️ لطفاً صبر کنید..."
        )

        # دریافت داده‌های تکنیکال
        await loading_msg.edit_text(
            f"🤖 تحلیل هوشمند ترکیبی {symbol.replace('/USDT', '')}\n\n"
            "📈 دریافت داده‌های تکنیکال...\n"
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

        from modules.smc_engine import create_smc_analysis
        smc_results = create_smc_analysis(df)
        current_price = df['close'].iloc[-1]

        # تحلیل ترکیبی AI
        await loading_msg.edit_text(
            f"🤖 تحلیل هوشمند ترکیبی {symbol.replace('/USDT', '')}\n\n"
            "💎 دریافت داده‌های فاندامنتال...\n"
            "🏦 دریافت داده‌های کلان...\n"
            "🧠 ترکیب و تحلیل توسط AI...\n"
            "⏱️ صبر کنید..."
        )

        result = await ai_integrated_analyzer.analyze_combined(
            symbol=symbol.replace('/USDT', ''),
            smc_results=smc_results,
            current_price=current_price
        )

        # فرمت و ارسال پیام
        await loading_msg.delete()
        ai_message = ai_integrated_analyzer.format_combined_message(result)
        await message.answer(ai_message, parse_mode=None)

        logger.info(f"✅ تحلیل AI تکمیل شد: سیگنال={result.signal.value}")

    except Exception as e:
        logger.error(f"❌ خطا در تحلیل AI: {e}")
        import traceback
        traceback.print_exc()
        await message.answer(f"❌ خطا: {str(e)}")


# Export
__all__ = ['fundamental_router']
