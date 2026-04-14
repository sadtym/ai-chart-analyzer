"""
ماژول رسم علامت‌های معاملاتی روی چارت
نقاط ورود، حد ضرر و حد سود را روی تصویر چارت نمایش می‌دهد
همچنین سیگنال متنی کامل را روی چارت می‌نویسد
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

# مسیر پروژه
PROJECT_ROOT = Path(__file__).parent.parent
CHARTS_DIR = PROJECT_ROOT / "charts"


class ChartAnnotator:
    """کلاس رسم علامت‌های معاملاتی روی چارت"""
    
    # رنگ‌ها
    COLORS = {
        'entry': '#00FF00',      # سبز برای ورود
        'sl': '#FF0000',         # قرمز برای حد ضرر
        'tp': '#00BFFF',         # آبی برای حد سود
        'text_light': '#FFFFFF', # متن روشن
        'text_dark': '#000000',  # متن تیره
        'grid': 'rgba(255,255,255,0.3)'
    }
    
    def __init__(self, chart_image_path: str):
        """
        راه‌اندازی annotator
        
        Args:
            chart_image_path: مسیر فایل تصویر چارت
        """
        self.original_path = chart_image_path
        self.image = Image.open(chart_image_path).convert('RGB')
        self.width, self.height = self.image.size
        self.draw = ImageDraw.Draw(self.image)
        
        # بررسی روشن یا تاریک بودن چارت
        self.is_dark_theme = self._detect_chart_theme()
        
        # تنظیم فونت
        self.font_size = max(12, int(self.height * 0.02))
        self.font = self._load_font()
    
    def _detect_chart_theme(self) -> bool:
        """تشخیص روشن یا تاریک بودن تم چارت"""
        # بررسی رنگ پس‌زمینه گوشه‌ها
        corners = [
            (10, 10),
            (self.width - 10, 10),
            (10, self.height - 10),
            (self.width - 10, self.height - 10)
        ]
        
        total_brightness = 0
        for x, y in corners:
            pixel = self.image.getpixel((x, y))
            brightness = sum(pixel[:3]) / 3
            total_brightness += brightness
        
        avg_brightness = total_brightness / 4
        return avg_brightness < 128  # اگر میانگین روشنایی کمتر از 128 باشد، تم تاریک است
    
    def _load_font(self, size: int = None):
        """بارگذاری فونت"""
        try:
            font_size = size if size else self.font_size
            
            # تلاش برای فونت‌های مختلف
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/System/Library/Fonts/Helvetica.ttc',  # macOS
                'arial.ttf',  # Windows fallback
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, font_size)
            
            return ImageFont.load_default()
            
        except Exception:
            return ImageFont.load_default()
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """تبدیل رنگ hex به RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _parse_price(self, price_str: str) -> float:
        """تبدیل رشته قیمت به عدد"""
        try:
            # حذف کاما و فضای خالی
            cleaned = str(price_str).replace(',', '').replace(' ', '').strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def _estimate_price_range(self) -> Tuple[float, float]:
        """تخمین بازه قیمتی چارت از روی نام فایل یا پیکسل‌ها"""
        # روش 1: استخراج از نام فایل
        filename = os.path.basename(self.original_path)
        import re
        
        # جستجوی قیمت‌ها در نام فایل
        price_pattern = r'(\d+\.?\d*)'
        prices = re.findall(price_pattern, filename)
        
        if prices:
            price_values = [float(p) for p in prices]
            min_price = min(price_values)
            max_price = max(price_values)
            if max_price > min_price:
                return (min_price, max_price)
        
        # روش 2: حدس بر اساس قیمت‌های معمول
        return (100, 200)  # پیش‌فرض
    
    def _price_to_y_position(self, price: float, min_price: float, max_price: float) -> int:
        """تبدیل قیمت به موقعیت عمودی روی تصویر"""
        price_range = max_price - min_price
        if price_range == 0:
            return int(self.height * 0.5)
        
        # محاسبه موقعیت (چارت‌ها معمولاً قیمت پایین در پایین است)
        normalized = (price - min_price) / price_range
        y = self.height - int(normalized * (self.height * 0.9)) - int(self.height * 0.05)
        return max(10, min(self.height - 10, y))
    
    def _draw_text_box(self, text: str, x: int, y: int, bg_color: Tuple[int, int, int], 
                       text_color: Tuple[int, int, int], padding: int = 10):
        """رسم یک کادر متنی"""
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # رسم پس‌زمینه کادر
        self.draw.rectangle(
            [x, y, x + text_width + padding * 2, y + text_height + padding * 2],
            fill=bg_color,
            outline=text_color,
            width=1
        )
        
        # رسم متن
        self.draw.text(
            (x + padding, y + padding),
            text,
            fill=text_color,
            font=self.font
        )
    
    def _draw_signal_text(self, analysis_data: Dict[str, Any], min_price: float, max_price: float):
        """رسم کادر سیگنال متنی روی چارت (نسخه حرفه‌ای)"""
        try:
            bias = analysis_data.get('bias', 'N/A')
            setup = analysis_data.get('setup', 'N/A')
            confidence = analysis_data.get('confidence', 0)
            entry = analysis_data.get('entry', 'N/A')
            sl = analysis_data.get('sl', 'N/A')
            tp = analysis_data.get('tp', 'N/A')
            key_level = analysis_data.get('key_level', 'N/A')
            reasoning = analysis_data.get('reasoning', 'N/A')
            
            # محاسبه RR
            try:
                entry_val = float(str(entry).replace(',', ''))
                sl_val = float(str(sl).replace(',', ''))
                tp_val = float(str(tp).replace(',', ''))
                
                if bias.lower() == 'long':
                    risk = entry_val - sl_val
                    reward = tp_val - entry_val
                elif bias.lower() == 'short':
                    risk = sl_val - entry_val
                    reward = entry_val - tp_val
                else:
                    risk = 1
                    reward = 0
                
                rr = round(reward / risk, 2) if risk > 0 else 0
                rr_text = f"RR 1:{rr}"
            except:
                rr_text = "RR -"
            
            # انتخاب رنگ بر اساس bias
            if bias.lower() == 'short':
                header_color = (255, 50, 50)  # قرمز
                header_text = f"📉 SHORT | {confidence}%"
            elif bias.lower() == 'long':
                header_color = (50, 255, 50)  # سبز
                header_text = f"📈 LONG | {confidence}%"
            else:
                header_color = (255, 200, 50)  # زرد
                header_text = f"⚖️ RANGE | {confidence}%"
            
            # رنگ پس‌زمینه (نیمه شفاف سیاه)
            bg_color = (0, 0, 0, 180)
            
            # تبدیل تصویر به RGBA برای شفافیت
            if self.image.mode != 'RGBA':
                self.image = self.image.convert('RGBA')
            
            # ساخت تصویر شفاف برای overlay
            overlay = Image.new('RGBA', self.image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # اندازه کادر
            box_height = 95
            box_y = 10
            padding = 10
            
            # رسم کادر نیمه‌شفاف
            overlay_draw.rectangle(
                [5, box_y, self.width - 5, box_y + box_height],
                fill=(0, 0, 0, 160),
                outline=header_color,
                width=2
            )
            
            # تبدیل به RGB برای ذخیره
            self.image = self.image.convert('RGB')
            self.draw = ImageDraw.Draw(self.image)
            
            # فونت کوچک‌تر برای متن
            small_font_size = max(10, int(self.height * 0.015))
            small_font = self._load_font(size=small_font_size)
            
            # رسم متن سیگنال
            text_color = (255, 255, 255)
            
            # سطر اول: header
            self.draw.text((15, box_y + 5), header_text, fill=header_color, font=small_font)
            
            # سطر دوم: setup
            setup_text = f"Setup: {setup[:40]}..." if len(str(setup)) > 40 else f"Setup: {setup}"
            self.draw.text((15, box_y + 28), setup_text, fill=text_color, font=small_font)
            
            # سطر سوم: قیمت‌ها - نمایش دقیق بدون گرد کردن
            entry_display = f"{float(entry):.6f}".rstrip('0').rstrip('.') if str(entry).replace('.', '').isdigit() else str(entry)
            sl_display = f"{float(sl):.6f}".rstrip('0').rstrip('.') if str(sl).replace('.', '').isdigit() else str(sl)
            tp_display = f"{float(tp):.6f}".rstrip('0').rstrip('.') if str(tp).replace('.', '').isdigit() else str(tp)
            prices_text = f"Entry: {entry_display} | SL: {sl_display} | TP: {tp_display} | {rr_text}"
            self.draw.text((15, box_y + 51), prices_text, fill=text_color, font=small_font)
            
            # سطر چهارم: سطح کلیدی
            key_text = f"Key: {key_level[:50]}" if len(str(key_level)) > 50 else f"Key: {key_level}"
            self.draw.text((15, box_y + 70), key_text, fill=text_color, font=small_font)
            
        except Exception as e:
            print(f"❌ خطا در رسم سیگنال متنی: {e}")
    
    def annotate_chart(self, analysis_data: Dict[str, Any]) -> str:
        """
        رسم علامت‌های معاملاتی روی چارت
        
        Args:
            analysis_data: دیتای تحلیل شامل entry, sl, tp
            
        Returns:
            مسیر فایل خروجی
        """
        try:
            # استخراج قیمت‌ها
            entry_price = self._parse_price(analysis_data.get('entry', 0))
            sl_price = self._parse_price(analysis_data.get('sl', 0))
            tp_price = self._parse_price(analysis_data.get('tp', 0))
            
            if entry_price == 0 and sl_price == 0:
                return self.original_path
            
            # محاسبه بازه قیمتی
            prices = [p for p in [entry_price, sl_price, tp_price] if p > 0]
            if not prices:
                return self.original_path
            
            min_price = min(prices) * 0.98
            max_price = max(prices) * 1.02
            
            # ابتدا سیگنال متنی را رسم کن (روی چارت)
            if not analysis_data.get('error'):
                self._draw_signal_text(analysis_data, min_price, max_price)
            
            # رسم خط ورود
            if entry_price > 0:
                self._draw_horizontal_line(
                    entry_price, min_price, max_price,
                    self.COLORS['entry'],
                    'ENTRY',
                    offset=0
                )
            
            # رسم حد ضرر
            if sl_price > 0:
                self._draw_horizontal_line(
                    sl_price, min_price, max_price,
                    self.COLORS['sl'],
                    'SL',
                    offset=30
                )
            
            # رسم حد سود
            if tp_price > 0:
                self._draw_horizontal_line(
                    tp_price, min_price, max_price,
                    self.COLORS['tp'],
                    'TP',
                    offset=60
                )
            
            # ذخیره تصویر
            output_path = CHARTS_DIR / f"annotated_{os.path.basename(self.original_path)}"
            self.image.save(str(output_path), quality=95, optimize=True)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ خطا در annotate_chart: {e}")
            return self.original_path
    
    def _draw_horizontal_line(self, price: float, min_price: float, max_price: float, 
                             hex_color: str, label: str, offset: int = 0):
        """رسم خط افقی روی چارت"""
        y = self._price_to_y_position(price, min_price, max_price)
        rgb_color = self._hex_to_rgb(hex_color)
        
        # رسم خط افقی (چند پیکسل عرض)
        line_width = 3
        for i in range(line_width):
            self.draw.line(
                [(0, y + i + offset), (self.width, y + i + offset)],
                fill=rgb_color,
                width=2
            )
        
        # رسم دایره در انتهای خط
        circle_radius = 8
        self.draw.ellipse(
            [self.width - 40, y + offset - circle_radius,
             self.width - 40 + circle_radius * 2, y + offset + circle_radius],
            outline=rgb_color,
            width=2
        )
        
        # اضافه کردن متن
        text_color = self.COLORS['text_light'] if self.is_dark_theme else self.COLORS['text_dark']
        
        # پس‌زمینه متن
        price_display = f"{price:.6f}".rstrip('0').rstrip('.') if isinstance(price, (int, float)) else str(price)
        text_str = f"{label}: {price_display}"
        
        # محاسبه اندازه متن
        bbox = self.draw.textbbox((0, 0), text_str, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # رسم پس‌زمینه متن
        bg_padding = 4
        self.draw.rectangle(
            [5, y + offset - text_height//2 - bg_padding,
             5 + text_width + bg_padding * 2, y + offset + text_height//2 + bg_padding],
            fill=rgb_color
        )
        
        # رسم متن
        self.draw.text(
            (5 + bg_padding, y + offset - text_height//2),
            text_str,
            fill=text_color,
            font=self.font
        )


def annotate_chart_with_analysis(chart_path: str, analysis_data: Dict[str, Any]) -> str:
    """
    تابع کمکی برای علامت‌گذاری چارت
    
    Args:
        chart_path: مسیر تصویر چارت
        analysis_data: دیتای تحلیل
        
    Returns:
        مسیر تصویر علامت‌گذاری شده
    """
    annotator = ChartAnnotator(chart_path)
    return annotator.annotate_chart(analysis_data)


if __name__ == "__main__":
    # تست ماژول
    import json
    
    print("=" * 60)
    print("🧪 تست Chart Annotator با سیگنال متنی")
    print("=" * 60)
    
    # تست با داده نمونه
    test_data = {
        "bias": "Short",
        "setup": "Liquidity grab + rejection at 121.65",
        "entry": "121.80",
        "sl": "122.10",
        "tp": "121.20",
        "confidence": 78
    }
    
    chart_path = "/workspace/user_input_files/Screenshot_20251224-091008.png"
    
    if os.path.exists(chart_path):
        result = annotate_chart_with_analysis(chart_path, test_data)
        print(f"✅ چارت با سیگنال متنی علامت‌گذاری شد: {result}")
        print(f"📊 اکنون چارت شامل:")
        print("   - کادر سیگنال در بالای چارت")
        print("   - خط سبز برای Entry")
        print("   - خط قرمز برای SL")
        print("   - خط آبی برای TP")
    else:
        print(f"❌ فایل یافت نشد: {chart_path}")
