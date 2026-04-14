"""
ماژول فرمت‌بندی و ارسال سیگنال‌های معاملاتی
شامل قالب‌های مختلف پیام و دکمه‌های تعاملی
"""

from typing import Dict, Any, List
from datetime import datetime
from config import SIGNAL_EMOJIS


class SignalFormatter:
    """کلاس فرمت‌بندی سیگنال‌های معاملاتی"""
    
    @staticmethod
    def format_signal(data: Dict[str, Any]) -> str:
        """
        فرمت‌بندی تحلیل SMC حرفه‌ای به صورت پیام کوتاه و سریع برای تلگرام
        شامل تحلیل مولتی تایم‌فریم
        
        Args:
            data: دیکشنری اطلاعات تحلیل با ساختار Smart Money Concepts
            
        Returns:
            رشته پیام فرمت‌شده
        """
        # استخراج اطلاعات اصلی از تحلیل SMC
        bias = data.get('bias', 'نامشخص')
        entry = data.get('entry', '0')
        sl = data.get('sl', '0')
        tp = data.get('tp', '0')
        confidence = data.get('confidence', '0')
        
        # اطلاعات SMC جدید
        structure = data.get('structure', 'نامشخص')
        zones = data.get('zones', 'شناسایی نشد')
        momentum = data.get('momentum', 'نامشخص')
        decision_reasoning = data.get('decision_reasoning', data.get('reasoning', ''))
        
        # اطلاعات مولتی تایم‌فریم
        mtf_trend = data.get('mtf_trend', 'NEUTRAL').upper()
        ltf_trend = data.get('ltf_trend', 'NEUTRAL').upper()
        mtf_alignment = data.get('mtf_alignment', 'CHOPPY').upper()
        htf_desc = data.get('htf_structure_desc', '')
        ltf_desc = data.get('ltf_structure_desc', '')
        alignment_reasoning = data.get('alignment_reasoning', '')
        
        # انتخاب ایموجی و جهت بر اساس bias
        bias_lower = bias.lower().strip()
        
        if bias_lower == 'short':
            direction_emoji = '📉'
            direction_text = 'SHORT'
            direction_full = 'فروش'
            color_emoji = '🔴'
        elif bias_lower == 'long':
            direction_emoji = '📈'
            direction_text = 'LONG'
            direction_full = 'خرید'
            color_emoji = '🟢'
        else:
            direction_emoji = '⚖️'
            direction_text = 'RANGE'
            direction_full = 'خنثی'
            color_emoji = '🟡'
        
        # فرمت قیمت‌ها - نمایش دقیق بدون گرد کردن
        def format_price(price: str) -> str:
            try:
                price_str = str(price).strip()
                if price_str.replace('.', '').replace('-', '').isdigit():
                    return price_str
                return price_str
            except (ValueError, TypeError):
                return str(price)
        
        entry_fmt = format_price(entry)
        sl_fmt = format_price(sl)
        tp_fmt = format_price(tp)
        
        # اطلاعات اهرم
        leverage_recommendation = data.get('leverage_recommendation')
        leverage_reasoning = data.get('leverage_reasoning', '')
        risk_warning = data.get('risk_warning', '')
        
        # محاسبه RR
        try:
            entry_val = float(entry)
            sl_val = float(sl)
            tp_val = float(tp)
            
            if bias_lower == 'long':
                risk = entry_val - sl_val
                reward = tp_val - entry_val
            elif bias_lower == 'short':
                risk = sl_val - entry_val
                reward = entry_val - tp_val
            else:
                risk = 0
                reward = 0
            
            if risk > 0:
                rr = round(reward / risk, 2)
                rr_text = f"⚡ RR 1:{rr}"
            else:
                rr_text = "⚡ RR -"
        except:
            rr_text = "⚡ RR -"
        
        # ═══════════════════════════════════════════════════════
        # 🎯 نمایش تحلیل مولتی تایم‌فریم
        # ═══════════════════════════════════════════════════════
        
        # ترجمه وضعیت‌ها به فارسی
        trend_translation = {
            'BULLISH': ('صعودی', '🟢'),
            'BEARISH': ('نزولی', '🔴'),
            'NEUTRAL': ('خنثی', '⚪')
        }
        
        alignment_translation = {
            'ALIGNED': ('✅ هم‌جهت (قدرتمند)', 'هم‌جهت'),
            'DIVERGENT': ('⚠️ واگرا (ریسک بالا)', 'واگرا'),
            'CHOPPY': ('🔴 رنج (صبر کنید)', 'رنج')
        }
        
        htf_text, htf_emoji = trend_translation.get(mtf_trend, ('نامشخص', '⚪'))
        ltf_text, ltf_emoji = trend_translation.get(ltf_trend, ('نامشخص', '⚪'))
        align_text, align_name = alignment_translation.get(mtf_alignment, ('نامشخص', 'نامشخص'))
        
        # ساخت بخش MTF
        mtf_section = f"""
🔄 **تحلیل مولتی تایم‌فریم:**

📊 **ساختار اصلی (HTF):** {htf_emoji} {htf_text}
   {htf_desc}

📍 **ساختار فعلی (LTF):** {ltf_emoji} {ltf_text}
   {ltf_desc}

🎯 **هم‌جهتی:** {align_text}
   {alignment_reasoning}
"""
        
        # ساخت بخش اهرم
        leverage_section = ""
        if leverage_recommendation:
            leverage_section = f"""
🎚️ **اهرم پیشنهادی:** `{leverage_recommendation}x`
💡 **دلیل اهرم:**
{leverage_reasoning}
"""
            if risk_warning:
                leverage_section += f"⚠️ {risk_warning}\n"
        
        # ساخت پیام حرفه‌ای با جزئیات SMC کامل و MTF
        message = f"""{direction_emoji} **{direction_text}** | 🎯 اعتماد: {confidence}%
{color_emoji} **SMC Analysis**

{mtf_section}
━━━━━━━━━━━━━━━━━━━
📊 **ساختار بازار:**
{structure}

🎯 **نواحی کلیدی:**
{zones}

⚡ **مومنتوم:**
{momentum}

━━━━━━━━━━━━━━━━━━━
💰 **سطوح معاملاتی:**
🟢 **ورود:** `{entry_fmt}`
🔴 **استاپ:** `{sl_fmt}`
🎯 **هدف:** `{tp_fmt}`
{rr_text}

━━━━━━━━━━━━━━━━━━━
🧠 **دلیل تصمیم‌گیری:**
{decision_reasoning}
{leverage_section}
━━━━━━━━━━━━━━━━━━━
⚠️ **این تحلیل بر اساس Smart Money Concepts است | مدیریت ریسک ضروری**
        """.strip()
        
        return message
    
    @staticmethod
    def create_keyboard(signal_id: str = None) -> dict:
        """
        ایجاد کیبورد شیشه‌ای برای تعامل (با قابلیت اهرم)
        
        Args:
            signal_id: شناسه منحصر به فرد سیگنال
            
        Returns:
            دیکشنری کیبورد تلگرام
        """
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 تحلیل مجدد", callback_data="retry_analysis"),
                InlineKeyboardButton(text="📊 آمار", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton(text="🎚️ محاسبه اهرم", callback_data="calculate_leverage"),
                InlineKeyboardButton(text="💰 مدیریت سرمایه", callback_data="capital_management")
            ],
            [
                InlineKeyboardButton(text="🔗 اشتراک‌گذاری", callback_data="share_signal"),
                InlineKeyboardButton(text="⚠️ مدیریت ریسک", callback_data="risk_management")
            ]
        ])
        
        return keyboard
    
    @staticmethod
    def format_error_message(error_text: str) -> str:
        """
        فرمت‌بندی پیام خطا
        
        Args:
            error_text: متن خطا
            
        Returns:
            پیام خطای فرمت‌شده
        """
        return f"""
{SIGNAL_EMOJIS['error']} **خطا در پردازش**

متأسفانه در تحلیل چارت خطایی رخ داد:

`{error_text}`

لطفاً موارد زیر را بررسی کنید:
• تصویر واضح و با کیفیت باشد
• چارت قیمت در تصویر مشخص باشد
• مجدداً تلاش کنید

@{'AI_Chart_Bot'}
        """.strip()
    
    @staticmethod
    def format_analyzing_message() -> str:
        """
        فرمت‌بندی پیام در حال تحلیل
        
        Returns:
            پیام وضعیت تحلیل
        """
        return f"""
{SIGNAL_EMOJIS['analyzing']} **در حال تحلیل چارت...**

لطفاً صبر کنید تا چارت شما توسط هوش مصنوعی بررسی شود.

⏱️ معمولاً این فرآیند 10-20 ثانیه طول می‌کشد...
        """.strip()
    
    @staticmethod
    def format_welcome_message() -> str:
        """
        فرمت‌بندی پیام خوشامدگویی
        
        Returns:
            پیام خوشامدگویی
        """
        return f"""
👋 **سلام دوست عزیز!**

به ربات *تحلیل گر هوشمند چارت* خوش آمدید! 🎉

با ارسال عکس چارت قیمت، تحلیل حرفه‌ای دریافت کنید:

✅ تشخیص خودکار نماد و تایم‌فریم
✅ شناسایی روند و الگوهای قیمتی
✅ تعیین نقاط ورود، حد ضرر و حد سود
✅ محاسبه نسبت ریسک به ریوارد

📸 **همین حالا عکس چارت خود را ارسال کنید!**

⚠️ *توجه: این ربات فقط جنبه کمکی دارد و تصمیم نهایی با شماست.*
        """.strip()
    
    @staticmethod
    def format_help_message() -> str:
        """
        فرمت‌بندی راهنمای استفاده
        
        Returns:
            پیام راهنما
        """
        return f"""
📖 **راهنمای استفاده**

**ارسال چارت:**
عکس چارت قیمت را از صرافی یا پلتفرم معاملاتی بگیرید و ارسال کنید.

**نکات مهم:**
• تصویر باید واضح باشد
• محورهای قیمت و زمان مشخص باشند
• بهتر است کندل‌ها واضح باشند

**خروجی تحلیل:**
• نماد معاملاتی
• جهت روند (صعودی/نزولی)
• نقاط ورود و خروج
• حد ضرر و حد سود
• توضیح تحلیل

برای شروع، عکس چارت ارسال کنید! 📸
        """.strip()
    
    @staticmethod
    def format_capital_management(
        capital: float,
        position_size: float,
        risk_amount: float,
        risk_percentage: float,
        reward_amount: float,
        reward_percentage: float,
        rr_ratio: float,
        leverage_needed: float,
        capital_after_loss: float,
        capital_after_win: float,
        method: str = "Fixed Risk"
    ) -> str:
        """
        فرمت‌بندی نتایج مدیریت سرمایه
        
        Args:
            capital: سرمایه کل
            position_size: حجم معامله
            risk_amount: مبلغ ریسک
            risk_percentage: درصد ریسک
            reward_amount: مبلغ سود
            reward_percentage: درصد سود
            rr_ratio: نسبت ریسک به ریوارد
            leverage_needed: اهرم مورد نیاز
            capital_after_loss: سرمایه پس از ضرر
            capital_after_win: سرمایه پس از سود
            method: روش محاسبه
            
        Returns:
            پیام فرمت‌شده مدیریت سرمایه
        """
        return f"""
━━━━━━━━━━━━━━━━━━━
💰 **📊 مدیریت سرمایه**

💵 **سرمایه کل:** `${capital:,.2f}`
📈 **حجم معامله:** `{position_size:.4f}`

💸 **مدیریت ریسک:**
├─ مبلغ ریسک: `${risk_amount:,.2f}`
├─ درصد ریسک: `{risk_percentage}%`
├─ حداکثر ضرر: `${risk_amount:,.2f}`
└─ سود هدف: `${reward_amount:,.2f}`

⚖️ **نسبت R/R:** 1:{rr_ratio}
🎚️ **اهرم مورد نیاز:** {leverage_needed}x

📊 **فرمول:** {method}

📉 **سرمایه پس از ضرر:** `${capital_after_loss:,.2f}`
📈 **سرمایه پس از سود:** `${capital_after_win:,.2f}`
━━━━━━━━━━━━━━━━━━━
⚠️ *مدیریت سرمایه = موفقیت در ترید* ⚠️
        """.strip()
    
    @staticmethod
    def format_capital_management_settings() -> str:
        """
        فرمت‌بندی راهنمای تنظیمات مدیریت سرمایه
        
        Returns:
            پیام راهنما
        """
        return f"""
━━━━━━━━━━━━━━━━━━━
📖 **راهنمای مدیریت سرمایه**

**🟢 محافظه‌کارانه (Conservative)**
• ریسک: 0.5% per trade
• حداکثر اهرم: 5x
• حداقل RR: 1:1.5
• مناسب برای: مبتدیان

**🟡 متعادل (Moderate) - پیشنهادی**
• ریسک: 1.0% per trade
• حداکثر اهرم: 10x
• حداقل RR: 1:1.5
• مناسب برای: اکثر معامله‌گران

**🟠 تهاجمی (Aggressive)**
• ریسک: 2.0% per trade
• حداکثر اهرم: 20x
• حداقل RR: 1:1
• مناسب برای: حرفه‌ای‌ها

**🔴 بسیار تهاجمی (Very Aggressive)**
• ریسک: 3.0% per trade
• حداکثر اهرم: 50x
• حداقل RR: 1:0.75
• مناسب برای: فقط حرفه‌ای‌ها

**📐 فرمول‌های موجود:**
• Fixed Risk Percentage (FRP)
• Kelly Criterion
• Volatility-Adjusted (ATR)
• Optimal F

**⚠️ هشدار:**
هرگز بیش از 2% سرمایه را در یک معامله ریسک نکنید!
━━━━━━━━━━━━━━━━━━━
        """.strip()
