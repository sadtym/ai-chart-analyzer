"""
ماژول محاسبه‌گر اهرم و مدیریت ریسک
محاسبه اندازه پوزیشن و سطح اهرم مناسب بر اساس سرمایه و ریسک

Author: MiniMax Agent
"""

import math
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """سطوح ریسک"""
    CONSERVATIVE = "محافظه‌کارانه"
    MODERATE = "متوسط"
    AGGRESSIVE = "پرخطر"


class VolatilityLevel(Enum):
    """سطوح نوسان"""
    LOW = "کم"
    MEDIUM = "متوسط"
    HIGH = "بالا"


@dataclass
class LeverageRecommendation:
    """توصیه اهرم"""
    recommended_leverage: float
    risk_level: RiskLevel
    position_size_percent: float
    max_loss_percent: float
    reasoning: str
    warning: str = ""


@dataclass
class PositionCalculation:
    """محاسبه پوزیشن"""
    entry_price: float
    stop_loss: float
    account_balance: float
    risk_percent: float
    leverage: float
    position_size: float
    required_margin: float
    potential_profit: float
    potential_loss: float
    rr_ratio: float


class LeverageCalculator:
    """کلاس اصلی محاسبه اهرم و ریسک"""
    
    def __init__(self):
        """راه‌اندازی محاسبه‌گر"""
        self.max_leverage = 100  # حداکثر اهرم مجاز
        self.min_leverage = 1    # حداقل اهرم
        
        # درصدهای ریسک پیشنهادی بر اساس سطح ریسک
        self.risk_percentages = {
            RiskLevel.CONSERVATIVE: 1.0,   # 1% ریسک
            RiskLevel.MODERATE: 2.0,       # 2% ریسک
            RiskLevel.AGGRESSIVE: 5.0      # 5% ریسک
        }
    
    def calculate_position_size(
        self, 
        entry_price: float, 
        stop_loss: float, 
        account_balance: float, 
        risk_percent: float,
        leverage: float = 1.0
    ) -> PositionCalculation:
        """
        محاسبه اندازه پوزیشن با اهرم
        
        Args:
            entry_price: قیمت ورود
            stop_loss: حد ضرر
            account_balance: موجودی حساب
            risk_percent: درصد ریسک از موجودی
            leverage: سطح اهرم
            
        Returns:
            نتیجه محاسبه پوزیشن
        """
        try:
            # محاسبه فاصله قیمت (ریسک)
            price_risk = abs(entry_price - stop_loss)
            
            if price_risk == 0:
                raise ValueError("قیمت ورود و حد ضرر نمی‌توانند برابر باشند")
            
            # محاسبه مقدار پول در معرض ریسک
            risk_amount = (account_balance * risk_percent) / 100
            
            # محاسبه اندازه پوزیشن (بدون اهرم)
            base_position_size = risk_amount / price_risk
            
            # اعمال اهرم
            leveraged_position_size = base_position_size * leverage
            
            # محاسبه مارجین مورد نیاز
            required_margin = leveraged_position_size * entry_price / leverage
            
            # محاسبه سود/زیان احتمالی
            if entry_price > stop_loss:  # Long position
                profit_price = entry_price + (entry_price - stop_loss) * 2  # TP = 2x SL
                potential_profit = (profit_price - entry_price) * leveraged_position_size
                potential_loss = (entry_price - stop_loss) * leveraged_position_size
            else:  # Short position
                profit_price = stop_loss - (stop_loss - entry_price) * 2  # TP = 2x SL
                potential_profit = (entry_price - profit_price) * leveraged_position_size
                potential_loss = (stop_loss - entry_price) * leveraged_position_size
            
            # محاسبه نسبت RR
            rr_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
            
            return PositionCalculation(
                entry_price=entry_price,
                stop_loss=stop_loss,
                account_balance=account_balance,
                risk_percent=risk_percent,
                leverage=leverage,
                position_size=leveraged_position_size,
                required_margin=required_margin,
                potential_profit=potential_profit,
                potential_loss=potential_loss,
                rr_ratio=rr_ratio
            )
            
        except Exception as e:
            raise ValueError(f"خطا در محاسبه پوزیشن: {str(e)}")
    
    def analyze_volatility(self, confidence: int, price_range: float = 0.0) -> VolatilityLevel:
        """
        تحلیل سطح نوسان بر اساس اعتماد تحلیل
        
        Args:
            confidence: درصد اعتماد تحلیل (0-100)
            price_range: محدوده قیمت (اختیاری)
            
        Returns:
            سطح نوسان
        """
        if confidence >= 80:
            return VolatilityLevel.LOW
        elif confidence >= 60:
            return VolatilityLevel.MEDIUM
        else:
            return VolatilityLevel.HIGH
    
    def recommend_leverage(
        self, 
        confidence: int, 
        volatility: VolatilityLevel,
        account_balance: float = 1000,
        risk_level: RiskLevel = RiskLevel.MODERATE
    ) -> LeverageRecommendation:
        """
        توصیه سطح اهرم مناسب بر اساس شرایط
        
        Args:
            confidence: درصد اعتماد تحلیل
            volatility: سطح نوسان
            account_balance: موجودی حساب
            risk_level: سطح ریسک کاربر
            
        Returns:
            توصیه اهرم
        """
        # محاسبه اهرم پایه بر اساس اعتماد
        base_leverage = self._calculate_base_leverage(confidence)
        
        # تنظیم بر اساس نوسان
        volatility_multiplier = self._get_volatility_multiplier(volatility)
        
        # تنظیم بر اساس سطح ریسک
        risk_multiplier = self._get_risk_multiplier(risk_level)
        
        # محاسبه اهرم نهایی
        recommended_leverage = min(
            base_leverage * volatility_multiplier * risk_multiplier,
            self.max_leverage
        )
        
        # محاسبه درصد پوزیشن
        position_size_percent = self.risk_percentages[risk_level]
        
        # محاسبه حداکثر زیان
        max_loss_percent = position_size_percent
        
        # ایجاد توضیح
        reasoning = self._create_reasoning(confidence, volatility, recommended_leverage)
        
        # هشدارها
        warning = self._create_warning(recommended_leverage, volatility)
        
        return LeverageRecommendation(
            recommended_leverage=recommended_leverage,
            risk_level=risk_level,
            position_size_percent=position_size_percent,
            max_loss_percent=max_loss_percent,
            reasoning=reasoning,
            warning=warning
        )
    
    def _calculate_base_leverage(self, confidence: int) -> float:
        """محاسبه اهرم پایه بر اساس اعتماد"""
        if confidence >= 90:
            return 20.0
        elif confidence >= 80:
            return 15.0
        elif confidence >= 70:
            return 10.0
        elif confidence >= 60:
            return 5.0
        elif confidence >= 50:
            return 3.0
        else:
            return 1.0
    
    def _get_volatility_multiplier(self, volatility: VolatilityLevel) -> float:
        """تنظیم ضریب بر اساس نوسان"""
        multipliers = {
            VolatilityLevel.LOW: 1.5,      # اهرم بالاتر برای نوسان کم
            VolatilityLevel.MEDIUM: 1.0,   # بدون تغییر
            VolatilityLevel.HIGH: 0.5      # اهرم کمتر برای نوسان بالا
        }
        return multipliers[volatility]
    
    def _get_risk_multiplier(self, risk_level: RiskLevel) -> float:
        """تنظیم ضریب بر اساس سطح ریسک"""
        multipliers = {
            RiskLevel.CONSERVATIVE: 0.7,   # اهرم کمتر برای ریسک پایین
            RiskLevel.MODERATE: 1.0,       # بدون تغییر
            RiskLevel.AGGRESSIVE: 1.3      # اهرم بالاتر برای ریسک بالا
        }
        return multipliers[risk_level]
    
    def _create_reasoning(self, confidence: int, volatility: VolatilityLevel, leverage: float) -> str:
        """ایجاد توضیح توصیه"""
        confidence_text = "بسیار بالا" if confidence >= 80 else "متوسط" if confidence >= 60 else "پایین"
        volatility_text = volatility.value
        
        return f"""
📊 **تحلیل شرایط:**
• اعتماد تحلیل: {confidence_text} ({confidence}%)
• سطح نوسان: {volatility_text}
• اهرم پیشنهادی: {leverage:.1f}x

💡 **منطق:**
با توجه به سطح اعتماد {confidence}% و نوسان {volatility_text}، 
اهرم {leverage:.1f}x برای مدیریت بهینه ریسک مناسب است.
        """.strip()
    
    def _create_warning(self, leverage: float, volatility: VolatilityLevel) -> str:
        """ایجاد هشدار مناسب"""
        warnings = []
        
        if leverage > 20:
            warnings.append("⚠️ اهرم بالا! مدیریت ریسک بسیار مهم است")
        
        if leverage > 50:
            warnings.append("🚨 اهرم بسیار بالا! فقط برای معامله‌گران حرفه‌ای")
        
        if volatility == VolatilityLevel.HIGH:
            warnings.append("📈 نوسان بالا - از اهرم کمتر استفاده کنید")
        
        if not warnings:
            warnings.append("✅ اهرم مناسب برای شرایط فعلی")
        
        return "\n".join(warnings)
    
    def format_leverage_analysis(self, recommendation: LeverageRecommendation) -> str:
        """فرمت‌بندی تحلیل اهرم"""
        return f"""
🎯 **توصیه اهرم**

📈 **اهرم پیشنهادی:** `{recommendation.recommended_leverage:.1f}x`
🎚️ **سطح ریسک:** {recommendation.risk_level.value}
💰 **اندازه پوزیشن:** {recommendation.position_size_percent}% از موجودی
📉 **حداکثر زیان:** {recommendation.max_loss_percent}%

{recommendation.reasoning}

{recommendation.warning}
        """.strip()
    
    def format_position_calculation(self, calc: PositionCalculation) -> str:
        """فرمت‌بندی محاسبه پوزیشن"""
        return f"""
💼 **محاسبه پوزیشن با اهرم**

💵 **موجودی حساب:** ${calc.account_balance:,.2f}
🎯 **قیمت ورود:** ${calc.entry_price:,.4f}
❌ **حد ضرر:** ${calc.stop_loss:,.4f}
⚖️ **اهرم:** {calc.leverage:.1f}x
📊 **ریسک:** {calc.risk_percent}%

━━━━━━━━━━━━━━━━━━━━━
💰 **محاسبات:**
📦 **اندازه پوزیشن:** {calc.position_size:,.4f}
🔒 **مارجین مورد نیاز:** ${calc.required_margin:,.2f}
📈 **سود احتمالی:** ${calc.potential_profit:,.2f}
📉 **زیان احتمالی:** ${calc.potential_loss:,.2f}
⚡ **نسبت RR:** 1:{calc.rr_ratio:.2f}
━━━━━━━━━━━━━━━━━━━━━
        """.strip()


# ═══════════════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🧮 تست محاسبه‌گر اهرم")
    print("=" * 60)
    
    calculator = LeverageCalculator()
    
    # تست توصیه اهرم
    print("\n🎯 تست توصیه اهرم:")
    recommendation = calculator.recommend_leverage(
        confidence=75,
        volatility=VolatilityLevel.MEDIUM,
        account_balance=1000,
        risk_level=RiskLevel.MODERATE
    )
    
    print(calculator.format_leverage_analysis(recommendation))
    
    # تست محاسبه پوزیشن
    print("\n💼 تست محاسبه پوزیشن:")
    calc = calculator.calculate_position_size(
        entry_price=1.0850,
        stop_loss=1.0820,
        account_balance=1000,
        risk_percent=2.0,
        leverage=10.0
    )
    
    print(calculator.format_position_calculation(calc))