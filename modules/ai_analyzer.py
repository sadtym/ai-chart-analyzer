"""
ماژول تحلیل هوشمند چارت با استفاده از هوش مصنوعی
پشتیبانی از OpenAI و Google Gemini

💡 برای استفاده رایگان، GEMINI_API_KEY را تنظیم کنید
"""

import json
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 📦 وارد کردن تنظیمات
# ═══════════════════════════════════════════════════════════════

try:
    from config import (
        AI_PROVIDER,
        OPENAI_API_KEY, OPENAI_MODEL,
        GEMINI_API_KEY, GEMINI_MODEL,
        SYSTEM_PROMPT
    )
except ImportError:
    # حالت تست - مقادیر پیش‌فرض
    AI_PROVIDER = "gemini"
    OPENAI_API_KEY = None
    OPENAI_MODEL = "gpt-4o"
    GEMINI_API_KEY = None
    GEMINI_MODEL = "gemini-1.5-flash"
    SYSTEM_PROMPT = ""


# ═══════════════════════════════════════════════════════════════
# 🧠 کلاس تحلیلگر چارت
# ═══════════════════════════════════════════════════════════════

class ChartAnalyzer:
    """کلاس اصلی تحلیل چارت با هوش مصنوعی"""
    
    def __init__(self):
        """راه‌اندازی تحلیلگر بر اساس تنظیمات"""
        self.provider = AI_PROVIDER
        self.client = None
        self.model = None
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"❌ AI_PROVIDER نامعتبر: {self.provider}")
    
    def _init_openai(self):
        """راه‌اندازی OpenAI"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = OPENAI_MODEL
            logger.info(f"✅ تحلیلگر OpenAI راه‌اندازی شد: {self.model}")
        except ImportError:
            logger.error("❌ کتابخانه openai نصب نیست! اجرای: pip install openai")
            raise
    
    def _init_gemini(self):
        """راه‌اندازی Google Gemini"""
        try:
            import google.generativeai as genai
            self.client = genai
            self.client.configure(api_key=GEMINI_API_KEY)
            self.model = GEMINI_MODEL
            logger.info(f"✅ تحلیلگر Gemini راه‌اندازی شد: {self.model}")
        except ImportError:
            logger.error("❌ کتابخانه google-generativeai نصب نیست!")
            logger.error("اجرای: pip install google-generativeai")
            raise
    
    def analyze(self, base64_image: str) -> Dict[str, Any]:
        """
        ارسال تصویر به هوش مصنوعی و دریافت تحلیل
        
        Args:
            base64_image: تصویر به صورت base64
            
        Returns:
            دیکشنری حاوی نتیجه تحلیل
        """
        try:
            logger.info(f"🚀 شروع تحلیل با {self.provider.upper()}...")
            
            if self.provider == "openai":
                return self._analyze_with_openai(base64_image)
            elif self.provider == "gemini":
                return self._analyze_with_gemini(base64_image)
                
        except Exception as e:
            logger.error(f"❌ خطا در تحلیل: {e}")
            return self._create_default_result(f"خطای سیستمی: {str(e)}")
    
    def _analyze_with_openai(self, base64_image: str) -> Dict[str, Any]:
        """تحلیل با OpenAI GPT-4o"""
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "این تصویر چارت را با دقت بسیار بالا تحلیل کن و اطلاعات زیر را استخراج نمایید:\n"
                                    "- نماد معاملاتی\n"
                                    "- تایم‌فریم\n"
                                    "- روند قیمت\n"
                                    "- نقاط ورود، حد ضرر و حد سود\n"
                                    "- توضیح تحلیل"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        logger.info("✅ پاسخ OpenAI دریافت شد")
        
        result = json.loads(content)
        
        if self._validate_result(result):
            return result
        else:
            return self._create_default_result("نتیجه تحلیل نامعتبر است")
    
    def _analyze_with_gemini(self, base64_image: str) -> Dict[str, Any]:
        """تحلیل با Google Gemini (رایگان!)"""
        import google.generativeai as genai
        
        # تبدیل base64 به تصویر
        image_data = base64.b64decode(base64_image)
        
        # ایجاد مدل
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=SYSTEM_PROMPT
        )
        
        # ارسال درخواست - فرمت جدید اسکالپ
        response = model.generate_content([
            {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
        ])
        
        # استخراج متن از پاسخ
        content = response.text
        logger.info("✅ پاسخ Gemini دریافت شد")
        
        # حذف علامت‌های markdown اگر وجود داشته باشد
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        result = json.loads(content)
        
        if self._validate_result(result):
            return result
        else:
            return self._create_default_result("نتیجه تحلیل نامعتبر است")
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """
        اعتبارسنجی نتیجه تحلیل SMC با قابلیت دو زبانه
        شامل فیلدهای فارسی و انگلیسی
        """
        # فیلدهای مورد نیاز - پشتیبانی از هر دو فرمت
        required_fields = ['signal', 'setup', 'confidence', 'reasoning']
        
        # بررسی فیلدهای ورود، حد ضرر و حد سود
        price_fields = ['entry', 'sl', 'tp']
        
        for field in required_fields + price_fields:
            if field not in result:
                logger.warning(f"⚠️ فیلد {field} در نتیجه وجود ندارد، مقدار پیش‌فرض تنظیم می‌شود")
                if field in price_fields:
                    result[field] = "N/A"
                elif field == 'reasoning':
                    result[field] = "تحلیل کامل نشده"
        
        # بررسی سیگنال
        signal = str(result.get('signal', '')).upper()
        valid_signals = ['BUY', 'SELL', 'HOLD', 'WAIT']
        if signal not in valid_signals:
            logger.warning(f"❌ سیگنال نامعتبر: {signal}")
            return False
        
        # اگر سیگنال WAIT یا HOLD است، اعتبارسنجی قیمت لازم نیست
        if signal in ['WAIT', 'HOLD']:
            logger.info(f"ℹ️ سیگنال {signal} - نیازی به اعتبارسنجی قیمت نیست")
            return True
        
        # فیلدهای قیمت برای BUY/SELL
        price_fields = ['entry', 'sl']
        for field in price_fields:
            if field not in result:
                logger.warning(f"❌ فیلد {field} برای سیگنال {signal} لازم است")
                return False
        
        # بررسی منطقی بودن مقادیر
        try:
            # تابع کمکی برای تبدیل قیمت (شامل محدوده)
            def parse_price(price_value):
                """تبدیل قیمت به عدد، پشتیبانی از محدوده"""
                price_str = str(price_value).replace(',', '').strip()
                
                # اگر محدوده است (مثل "2955.00-2960.00")، میانگین بگیر
                if '-' in price_str:
                    parts = price_str.split('-')
                    try:
                        low = float(parts[0].strip())
                        high = float(parts[1].strip())
                        return (low + high) / 2
                    except (ValueError, IndexError):
                        return None
                
                # اگر عدد منفرد است
                try:
                    return float(price_str)
                except ValueError:
                    return None
            
            entry = parse_price(result['entry'])
            sl = parse_price(result['sl'])
            
            # بررسی اینکه قیمت‌ها معتبر باشند
            if entry is None or sl is None:
                logger.warning("❌ مقادیر قیمت نامعتبر هستند")
                return False
            
            if entry <= 0 or sl <= 0:
                logger.warning("❌ مقادیر قیمت نامعتبر هستند")
                return False
            
            confidence = int(str(result.get('confidence', 50)).replace('%', ''))
            
            if not (0 <= confidence <= 100):
                logger.warning("❌ درصد اعتماد باید بین 0 تا 100 باشد")
                return False
            
            # اعتبارسنجی اهرم
            if 'leverage_recommendation' in result:
                try:
                    leverage = float(str(result['leverage_recommendation']))
                    if leverage < 1.0 or leverage > 100.0:
                        logger.warning(f"⚠️ اهرم {leverage} خارج از محدوده مجاز (1-100x)")
                        result['leverage_recommendation'] = min(max(leverage, 1.0), 50.0)
                except (ValueError, TypeError):
                    result['leverage_recommendation'] = 5.0
            
            # بررسی RR اگر TP موجود باشد
            tp = result.get('tp') or result.get('tp1')
            if tp:
                tp_value = parse_price(tp)
                if tp_value is None:
                    logger.warning("❌ مقدار TP نامعتبر است")
                    tp_value = 0
                
                bias = str(result.get('bias', '')).lower()
                
                if bias == 'long':
                    risk = entry - sl
                    reward = tp_value - entry
                elif bias == 'short':
                    risk = sl - entry
                    reward = entry - tp_value
                else:
                    risk = 1
                    reward = 0
                
                if risk > 0:
                    rr = reward / risk
                    result['rr_ratio'] = round(rr, 2)
                    
                    if rr < 1.5:
                        logger.warning(f"⚠️ RR ({rr:.2f}) کمتر از 1.5 است")
                    elif rr >= 2.0:
                        logger.info(f"✅ RR عالی: 1:{rr:.2f}")
            
            # اعتبارسنجی فیلدهای جدید SMC
            # فیلدهای قدیمی
            old_smc_fields = ['structure_analysis', 'ob_zone', 'fvg_zone', 'rsi_status']
            # فیلدهای جدید فارسی
            new_smc_fields = ['structure', 'zones', 'momentum', 'decision_reasoning']
            
            for field in old_smc_fields:
                if field not in result:
                    result[field] = "تشخیص داده نشد"
            
            # نگاشت فیلدهای جدید به قدیمی برای سازگاری
            field_mapping = {
                'structure': 'structure_analysis',
                'zones': 'ob_zone',  # zones شامل OB و FVG است
                'momentum': 'rsi_status',
                'decision_reasoning': 'reasoning'
            }
            
            for new_field, old_field in field_mapping.items():
                if new_field in result and old_field in result:
                    # اگر فیلد قدیمی خالی یا نامشخص است، از فیلد جدید استفاده کن
                    if result[old_field] in ["تشخیص داده نشد", "نامشخص", "ندارد", "", None]:
                        result[old_field] = result[new_field]
            
            # فیلد confluence_factors
            if 'confluence_factors' not in result:
                result['confluence_factors'] = []
            
            # ═══════════════════════════════════════════════════════
            # 📊 اعتبارسنجی و پردازش تحلیل مولتی تایم‌فریم (MTF)
            # ═══════════════════════════════════════════════════════
            
            mtf_data = result.get('mtf_analysis', {})
            if mtf_data:
                # اعتبارسنجی فیلدهای MTF
                required_mtf_fields = ['htf_trend', 'ltf_trend', 'alignment']
                for field in required_mtf_fields:
                    if field not in mtf_data:
                        mtf_data[field] = "NEUTRAL"
                
                # تنظیم اعتماد بر اساس هم‌جهتی
                alignment = str(mtf_data.get('alignment', '')).upper()
                htf_trend = str(mtf_data.get('htf_trend', '')).upper()
                ltf_trend = str(mtf_data.get('ltf_trend', '')).upper()
                
                # محاسبه تأثیر هم‌جهتی روی اعتماد
                if alignment == 'ALIGNED':
                    # هم‌جهت: افزایش اعتماد
                    alignment_bonus = 10
                    logger.info("🎯 MTF: ساختار هم‌جهت است، اعتماد افزایش می‌یابد")
                elif alignment == 'DIVERGENT':
                    # واگرا: کاهش اعتماد
                    alignment_bonus = -15
                    # حداکثر اعتماد برای معاملات واگرا
                    if confidence > 60:
                        confidence = 60
                    logger.warning("⚠️ MTF: ساختار واگرا است، اعتماد کاهش می‌یابد")
                else:
                    # رنج یا نامشخص
                    alignment_bonus = -5
                    logger.warning("⚠️ MTF: وضعیت نامشخص است")
                
                # اعمال تأثیر هم‌جهتی
                if 'confidence' in result:
                    result['confidence'] = max(10, min(98, confidence + alignment_bonus))
                
                # ذخیره اطلاعات MTF در نتیجه اصلی برای نمایش
                result['mtf_trend'] = htf_trend
                result['ltf_trend'] = ltf_trend
                result['mtf_alignment'] = alignment
                result['alignment_bonus'] = alignment_bonus
                
                # توضیحات ساختار
                result['htf_structure_desc'] = mtf_data.get('htf_structure_description', '')
                result['ltf_structure_desc'] = mtf_data.get('ltf_structure_description', '')
                result['alignment_reasoning'] = mtf_data.get('alignment_reasoning', '')
            else:
                # اگر MTF وجود ندارد، مقادیر پیش‌فرض تنظیم کن
                result['mtf_analysis'] = {
                    'htf_trend': 'NEUTRAL',
                    'ltf_trend': 'NEUTRAL',
                    'alignment': 'CHOPPY',
                    'htf_structure_description': 'تحلیل MTF موجود نیست',
                    'ltf_structure_description': 'تحلیل MTF موجود نیست',
                    'alignment_reasoning': 'اطلاعات کافی برای تحلیل چند تایم‌فریم نیست'
                }
                result['mtf_trend'] = 'NEUTRAL'
                result['ltf_trend'] = 'NEUTRAL'
                result['mtf_alignment'] = 'CHOPPY'
                result['alignment_bonus'] = 0
                
        except (ValueError, TypeError) as e:
            logger.warning(f"❌ خطا در اعتبارسنجی اعداد: {e}")
            return False
        
        return True
    
    def calculate_dynamic_confidence(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        محاسبه Confidence پویا بر اساس فاکتورهای تحلیل
        
        این متد می‌تواند توسط AI یا به صورت خودکار فراخوانی شود
        """
        base_score = 50
        confidence = result.get('confidence', base_score)
        
        # تحلیل فاکتورهای confluence - استفاده از فیلدهای جدید فارسی
        reasoning = str(result.get('reasoning', '') + ' ' + str(result.get('decision_reasoning', ''))).lower()
        structure = str(result.get('structure_analysis', '') + ' ' + str(result.get('structure', ''))).lower()
        zones = str(result.get('ob_zone', '') + ' ' + str(result.get('zones', ''))).lower()
        momentum = str(result.get('rsi_status', '') + ' ' + str(result.get('momentum', ''))).lower()
        
        # اضافه کردن امتیاز بر اساس فاکتورها
        additions = 0
        
        # روند و ساختار
        if any(word in reasoning + structure for word in ['روند', 'صعودی', 'نزولی', 'bullish', 'bearish', 'hh', 'hl', 'll', 'lh', 'سقف', 'کف']):
            additions += 10
        
        # Order Block - جستجو در هر دو زبان
        if any(word in reasoning + structure + zones for word in ['اردر بلاک', 'order block', 'ob', 'demand zone', 'supply zone', 'ناحیه تقاضا', 'ناحیه عرضه']):
            additions += 15
        
        # Fair Value Gap - جستجو در هر دو زبان
        if any(word in reasoning + structure + zones for word in ['fvg', 'imbalance', 'gap', 'شکاف ارزش', 'شکاف']):
            additions += 10
        
        # RSI Divergence - جستجو در هر دو زبان
        if any(word in momentum + reasoning for word in ['واگرایی', 'divergence', 'اشباع خرید', 'اشباع فروش', 'overbought', 'oversold']):
            additions += 10
        
        # Liquidity - جستجو در هر دو زبان
        if any(word in reasoning + structure + zones for word in ['لیکوئیدیتی', 'liquidity', 'sweep', 'pool', 'stop run', 'نقدینگی', 'سوئینگ']):
            additions += 10
        
        # Rejection/Pin Bar - جستجو در هر دو زبان
        if any(word in reasoning for word in ['رد شده', 'rejection', 'pin bar', 'shooting star', 'hammer', 'engulfing', 'کندل']):
            additions += 8
        
        # BOS/CHOCH - جستجو در هر دو زبان
        if any(word in structure for word in ['bos', 'choch', 'break of structure', 'شکست ساختار', 'تغییر ماهیت', 'bosh', 'choch']):
            additions += 12
        
        # بررسی ساختار بازار
        if 'رنج' in reasoning or 'range' in reasoning or 'چاپل' in reasoning:
            subtractions = 15
        else:
            subtractions = 0
        
        # عدم ساختار واضح
        if 'نامشخص' in structure or 'unclear' in structure or 'مشخص نیست' in reasoning:
            subtractions += 20
        
        # مقاومت/حمایت قوی
        if any(word in reasoning + momentum for word in ['مقاومت', 'support', 'resistance', 'حمایت']):
            subtractions += 5
        
        # محاسبه نهایی
        calculated_confidence = min(98, max(10, confidence + additions - subtractions))
        
        # ذخیره در نتیجه
        result['confidence'] = calculated_confidence
        result['confidence_breakdown'] = {
            'base': base_score,
            'additions': additions,
            'subtractions': subtractions,
            'ai_confidence': confidence,
            'calculated': calculated_confidence
        }
        
        logger.info(f"🎯 Confidence محاسبه شد: {confidence} → {calculated_confidence} (+{additions}/-{subtractions})")
        
        return result
    
    def _create_default_result(self, error_message: str) -> Dict[str, Any]:
        """ایجاد نتیجه پیش‌فرض در صورت خطا - فرمت اسکالپ حرفه‌ای"""
        return {
            "bias": "Range",
            "setup": f"خطا در تحلیل: {error_message}",
            "entry": "0",
            "sl": "0",
            "tp": "0",
            "confidence": "0",
            "key_level": "نامشخص",
            "reasoning": "تحلیل با خطا مواجه شد",
            "error": True
        }
    
    def get_token_usage(self) -> Dict[str, int]:
        """دریافت آمار مصرف توکن"""
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


# ═══════════════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("🤖 تست ماژول تحلیل چارت")
    print("=" * 60)
    
    # بررسی تنظیمات
    print(f"\n📋 تنظیمات فعلی:")
    print(f"   AI Provider: {AI_PROVIDER}")
    print(f"   OpenAI Key: {'✅ تنظیم شده' if OPENAI_API_KEY else '❌ تنظیم نشده'}")
    print(f"   Gemini Key: {'✅ تنظیم شده' if GEMINI_API_KEY else '❌ تنظیم نشده'}")
    
    try:
        analyzer = ChartAnalyzer()
        print("\n✅ تحلیلگر با موفقیت راه‌اندازی شد!")
        print(f"   Provider: {analyzer.provider}")
        print(f"   Model: {analyzer.model}")
        
        # تست ساختار پیش‌فرض
        result = analyzer._create_default_result("تست خطا")
        print(f"\n📊 ساختار نتیجه:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except ValueError as e:
        print(f"\n❌ خطا: {e}")
        print("\n💡 برای استفاده رایگان:")
        print("   1. به https://aistudio.google.com بروید")
        print("   2. API Key بسازید")
        print("   3. GEMINI_API_KEY را تنظیم کنید")
