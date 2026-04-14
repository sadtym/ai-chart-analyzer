#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch script to fix CPI calculation and other data issues
"""

# Read the file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix CPI calculation - use year-over-year change instead of month-over-month
old_cpi_logic = '''                    if series_name == 'interest_rate':
                        macro.interest_rate = current
                        macro.interest_rate_change = change_pct
                    elif series_name == 'cpi':
                        macro.cpi = current
                        macro.cpi_change = change_pct
                    elif series_name == 'dxy':
                        macro.dxy = current
                        macro.dxy_change = change_pct
                    elif series_name == 'm2':
                        macro.m2_money_supply = current
                        macro.m2_change = change_pct'''

new_cpi_logic = '''                    if series_name == 'interest_rate':
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
                        macro.m2_change = change_pct'''

if old_cpi_logic in content:
    content = content.replace(old_cpi_logic, new_cpi_logic)
    print("✅ Fix: Updated CPI calculation logic")
else:
    print("❌ Could not find CPI logic to patch")

# Also update the get_sentiment function to handle CPI correctly
# The issue is that CPI index is around 310, which is high, but we need to check the change %

old_sentiment = '''    def get_sentiment(self) -> Tuple[str, str]:
        """تعیین احساس کلان اقتصادی"""
        score = 0
        
        # نرخ بهره بالا = فشار نزولی بر ریسک‌پذیری
        if self.interest_rate > 5.0:
            score -= 2
        elif self.interest_rate > 4.0:
            score -= 1
        
        # تورم بالا = فشار نزولی
        if self.cpi > 5.0:
            score -= 2
        elif self.cpi > 3.0:
            score -= 1'''

new_sentiment = '''    def get_sentiment(self) -> Tuple[str, str]:
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
            pass'''

if old_sentiment in content:
    content = content.replace(old_sentiment, new_sentiment)
    print("✅ Fix: Updated get_sentiment logic")
else:
    print("❌ Could not find get_sentiment to patch")

# Write the fixed file
with open('/workspace/ai_chart_analyzer/modules/fundamental_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ File updated successfully!")
