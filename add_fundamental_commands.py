#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت اضافه کردن دستورات فاندامنتال به bot.py
"""

import re

# محتوای دستورات جدید
new_commands = '''
# ==================== هندلر داده‌های فاندامنتال و کلان ====================

@dp.message(Command("macro"))
async def cmd_macro_data(message: Message):
    """دستور /macro - نمایش داده‌های کلان اقتصادی"""
    user_name = message.from_user.full_name
    logger.info(f"🏦 درخواست داده‌های کلان از {user_name}")

    try:
        from modules.fundamental_data import fundamental_manager
        
        loading_msg = await message.answer(
            "🏦 دریافت داده‌های کلان اقتصادی...\\n"
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
            f"💎 دریافت داده‌های فاندامنتال {symbol}...\\n"
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

        from modules.lbank_client import lbank_client

        analyzing_msg = await message.answer(
            f"📊 تحلیل کامل {symbol.replace('/USDT', '')}\\n\\n"
            "🔄 دریافت داده‌ها...\\n"
            "⏱️ لطفاً صبر کنید..."
        )

        await analyzing_msg.edit_text(
            f"📊 تحلیل کامل {symbol.replace('/USDT', '')}\\n\\n"
            "📈 تحلیل تکنیکال SMC...\\n"
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
            f"📊 تحلیل کامل {symbol.replace('/USDT', '')}\\n\\n"
            "💎 دریافت فاندامنتال...\\n"
            "🏦 دریافت کلان...\\n"
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
                f"📈 تحلیل تکنیکال (SMC)\\n"
                f"{'-' * 25}\\n\\n"
                f"🎯 جهت: {direction}\\n"
                f"📊 اعتماد: {confidence}%\\n"
                f"💰 قیمت: ${current_price:,.4f}"
            )
            await message.answer(tech_text, parse_mode=None)
        
        logger.info(f"✅ تحلیل کامل تکمیل شد")

    except Exception as e:
        logger.error(f"❌ خطا در تحلیل کامل: {e}")
        await message.answer(f"❌ خطا: {str(e)}")


'''

# خواندن فایل اصلی
with open('/workspace/ai_chart_analyzer/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# یافتن محل قرار دادن کد جدید (قبل از async def send_auto_scan)
marker = 'async def send_auto_scan():'
if marker in content:
    # اضافه کردن قبل از تابع send_auto_scan
    new_content = content.replace(marker, new_commands + marker)
    
    with open('/workspace/ai_chart_analyzer/bot.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ دستورات فاندامنتال با موفقیت به bot.py اضافه شدند")
else:
    print("❌ marker یافت نشد")
