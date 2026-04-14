"""
ماژول مدیریت سرمایه و محاسبه حجم معامله
شامل فرمول‌های مختلف مدیریت ریسک

🎯 هدف: محاسبه دقیق حجم معامله بر اساس مدیریت سرمایه حرفه‌ای
"""

import math
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CapitalManagementResult:
    """نتیجه محاسبات مدیریت سرمایه"""
    position_size: float  # حجم معامله (لات یا واحد)
    risk_amount: float    # مبلغ ریسک
    risk_percentage: float # درصد ریسک از سرمایه
    reward_amount: float  # مبلغ سود هدف
    reward_percentage: float # درصد سود از سرمایه
    leverage_needed: float   # اهرم مورد نیاز
    rr_ratio: float          # نسبت ریسک به ریوارد
    max_loss: float          # حداکثر ضرر قابل قبول
    recommended_leverage: int # اهرم پیشنهادی
    capital_after_loss: float # سرمایه پس از ضرر
    capital_after_win: float  # سرمایه پس از سود
    formulas_used: str       # فرمول‌های استفاده شده
    warnings: list           # هشدارها


class CapitalManager:
    """
    کلاس مدیریت سرمایه با فرمول‌های حرفه‌ای
    
    پشتیبانی از:
    - Fixed Risk Percentage (FRP)
    - Kelly Criterion
    - Volatility-based Sizing (ATR)
    - Fixed Fractional
    - Optimal F
    """
    
    # درصدهای پیشنهادی ریسک
    RECOMMENDED_RISK_PERCENTAGES = {
        'conservative': 0.5,   # 0.5% - بسیار محافظه‌کارانه
        'moderate': 1.0,       # 1% - متعادل
        'aggressive': 2.0,     # 2% - تهاجمی
        'very_aggressive': 3.0 # 3% - بسیار تهاجمی
    }
    
    # حداکثر اهرم مجاز برای هر سطح ریسک
    MAX_LEVERAGE_BY_RISK = {
        'conservative': 5,
        'moderate': 10,
        'aggressive': 20,
        'very_aggressive': 50
    }
    
    def __init__(self, total_capital: float = 1000.0, risk_per_trade: float = 1.0):
        """
        راه‌اندازی مدیریت سرمایه
        
        Args:
            total_capital: کل سرمایه موجود (به دلار)
            risk_per_trade: درصد ریسک به ازای هر معامله (پیش‌فرض: 1%)
        """
        self.total_capital = total_capital
        self.risk_per_trade = risk_per_trade
        self.win_rate = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0
        
    def update_stats(self, win_rate: float, avg_win: float, avg_loss: float):
        """
        به‌روزرسانی آمار معاملات برای محاسبات Kelly و Optimal F
        
        Args:
            win_rate: نرخ برد (درصد اعشاری، مثل 0.55)
            avg_win: میانگین سود در معاملات برنده
            avg_loss: میانگین ضرر در معاملات بازنده
        """
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
    
    def calculate_fixed_risk(
        self,
        entry_price: float,
        stop_loss: float,
        risk_percentage: Optional[float] = None
    ) -> CapitalManagementResult:
        """
        محاسبه حجم معامله با روش Fixed Risk Percentage (FRP)
        
        فرمول:
        Position Size = (Capital × Risk%) / (Entry - SL)
        
        Args:
            entry_price: قیمت ورود
            stop_loss: حد ضرر
            risk_percentage: درصد ریسک (پیش‌فرض: مقدار تنظیم شده)
            
        Returns:
            CapitalManagementResult: نتیجه محاسبات
        """
        risk_pct = risk_percentage or self.risk_per_trade
        risk_amount = self.total_capital * (risk_pct / 100)
        
        # محاسبه فاصله قیمت
        price_distance = abs(entry_price - stop_loss)
        
        if price_distance <= 0:
            return self._create_error_result("فاصله قیمت ورود تا حد ضرر نامعتبر است")
        
        # محاسبه حجم معامله
        position_size = risk_amount / price_distance
        
        # محاسبه سود هدف (RR 2:1 پیش‌فرض)
        reward_amount = risk_amount * 2
        reward_price = entry_price + reward_size_to_price(reward_amount, position_size, entry_price, stop_loss)
        
        # محاسبه اهرم مورد نیاز
        notional_value = position_size * entry_price
        leverage_needed = notional_value / self.total_capital if self.total_capital > 0 else 0
        
        # محاسبه سرمایه پس از معامله
        capital_after_loss = self.total_capital - risk_amount
        capital_after_win = self.total_capital + reward_amount
        
        return CapitalManagementResult(
            position_size=round(position_size, 4),
            risk_amount=round(risk_amount, 2),
            risk_percentage=risk_pct,
            reward_amount=round(reward_amount, 2),
            reward_percentage=round(risk_pct * 2, 2),
            leverage_needed=round(leverage_needed, 2),
            rr_ratio=2.0,
            max_loss=risk_amount,
            recommended_leverage=min(int(leverage_needed), 50),
            capital_after_loss=round(capital_after_loss, 2),
            capital_after_win=round(capital_after_win, 2),
            formulas_used="Fixed Risk Percentage (FRP)",
            warnings=self._generate_warnings(risk_pct, leverage_needed)
        )
    
    def calculate_kelly_criterion(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        win_rate: Optional[float] = None,
        leverage_cap: int = 10
    ) -> CapitalManagementResult:
        """
        محاسبه حجم معامله با فرمول Kelly Criterion
        
        فرمول:
        Kelly % = W - [(1-W) / R]
        حيث:
        W = نرخ برد
        R = نسبت میانگین سود به میانگین ضرر
        
        Args:
            entry_price: قیمت ورود
            stop_loss: حد ضرر
            take_profit: هدف سود
            win_rate: نرخ برد (اختیاری)
            leverage_cap: محدودیت اهرم
            
        Returns:
            CapitalManagementResult: نتیجه محاسبات
        """
        w = win_rate or self.win_rate
        r = abs(take_profit - entry_price) / abs(entry_price - stop_loss) if entry_price != stop_loss else 2
        
        # فرمول Kelly
        kelly_pct = w - ((1 - w) / r)
        
        # Kelly کسری (فقط 50% Kelly برای امنیت بیشتر)
        half_kelly = kelly_pct * 0.5
        
        # محدود کردن به حداکثر 2%
        safe_kelly = min(max(half_kelly, 0.001), 0.02)
        
        # استفاده از Kelly محاسبه شده
        risk_amount = self.total_capital * safe_kelly
        price_distance = abs(entry_price - stop_loss)
        
        if price_distance <= 0:
            return self._create_error_result("فاصله قیمت نامعتبر")
        
        position_size = risk_amount / price_distance
        
        # محاسبات تکمیلی
        notional_value = position_size * entry_price
        leverage_needed = notional_value / self.total_capital if self.total_capital > 0 else 0
        
        return CapitalManagementResult(
            position_size=round(position_size, 4),
            risk_amount=round(risk_amount, 2),
            risk_percentage=round(safe_kelly * 100, 3),
            reward_amount=round(risk_amount * r, 2),
            reward_percentage=round(safe_kelly * r * 100, 2),
            leverage_needed=round(leverage_needed, 2),
            rr_ratio=round(r, 2),
            max_loss=risk_amount,
            recommended_leverage=min(int(leverage_needed), leverage_cap),
            capital_after_loss=round(self.total_capital - risk_amount, 2),
            capital_after_win=round(self.total_capital + (risk_amount * r), 2),
            formulas_used=f"Kelly Criterion (W={w:.1%}, R={r:.2f})",
            warnings=self._generate_warnings(safe_kelly * 100, leverage_needed)
        )
    
    def calculate_volatility_adjusted(
        self,
        entry_price: float,
        stop_loss: float,
        atr: float,
        atr_multiplier: float = 1.5,
        risk_percentage: float = 1.0
    ) -> CapitalManagementResult:
        """
        محاسبه حجم معامله بر اساس نوسانات (ATR-based)
        
        فرمول:
        Position Size = (Capital × Risk%) / (SL Distance × ATR Multiplier)
        
        Args:
            entry_price: قیمت ورود
            stop_loss: حد ضرر
            atr: میانگین دامنه واقعی (Average True Range)
            atr_multiplier: ضریب ATR برای تنظیم فاصله SL
            risk_percentage: درصد ریسک
            
        Returns:
            CapitalManagementResult: نتیجه محاسبات
        """
        # استفاده از ATR برای تنظیم حد ضرر
        adjusted_sl_distance = abs(entry_price - stop_loss)
        
        if adjusted_sl_distance <= 0:
            return self._create_error_result("فاصله قیمت نامعتبر")
        
        # فاصله نهایی حد ضرر
        final_sl_distance = max(adjusted_sl_distance, atr * 0.5)
        
        # محاسبه ریسک
        risk_amount = self.total_capital * (risk_percentage / 100)
        
        # حجم معامله
        position_size = risk_amount / final_sl_distance
        
        # محاسبات تکمیلی
        notional_value = position_size * entry_price
        leverage_needed = notional_value / self.total_capital if self.total_capital > 0 else 0
        
        # سود هدف (2R)
        reward_amount = risk_amount * 2
        
        return CapitalManagementResult(
            position_size=round(position_size, 4),
            risk_amount=round(risk_amount, 2),
            risk_percentage=risk_percentage,
            reward_amount=round(reward_amount, 2),
            reward_percentage=round(risk_percentage * 2, 2),
            leverage_needed=round(leverage_needed, 2),
            rr_ratio=2.0,
            max_loss=risk_amount,
            recommended_leverage=min(int(leverage_needed), 20),
            capital_after_loss=round(self.total_capital - risk_amount, 2),
            capital_after_win=round(self.total_capital + reward_amount, 2),
            formulas_used=f"Volatility-Adjusted (ATR={atr}, Multiplier={atr_multiplier}x)",
            warnings=self._generate_warnings(risk_percentage, leverage_needed, atr)
        )
    
    def calculate_optimal_f(
        self,
        entry_price: float,
        stop_loss: float,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> CapitalManagementResult:
        """
        محاسبه با روش Optimal F
        
        فرمول Optimal F:
        f* = (P(W/L) - (1-P)) / W
        حيث:
        P = نرخ برد
        W = میانگین سود
        L = میانگین ضرر
        
        Args:
            entry_price: قیمت ورود
            stop_loss: حد ضرر
            win_rate: نرخ برد
            avg_win: میانگین سود
            avg_loss: میانگین ضرر
            
        Returns:
            CapitalManagementResult: نتیجه محاسبات
        """
        w = win_rate or self.win_rate
        aw = avg_win or self.avg_win
        al = abs(avg_loss or self.avg_loss)
        
        if aw <= 0 or al <= 0:
            # استفاده از FRP اگر داده‌ها کافی نیست
            return self.calculate_fixed_risk(entry_price, stop_loss)
        
        # فرمول Optimal F
        win_loss_ratio = aw / al
        optimal_f = (w * win_loss_ratio - (1 - w)) / win_loss_ratio
        
        # محدود کردن Optimal F (حداکثر 25%)
        safe_optimal_f = min(max(optimal_f, 0.01), 0.25)
        
        # استفاده از half-optimal-F برای امنیت
        half_optimal = safe_optimal_f * 0.5
        
        # محاسبه حجم
        price_distance = abs(entry_price - stop_loss)
        if price_distance <= 0:
            return self._create_error_result("فاصله قیمت نامعتبر")
        
        risk_amount = self.total_capital * half_optimal
        position_size = risk_amount / price_distance
        
        # محاسبات تکمیلی
        notional_value = position_size * entry_price
        leverage_needed = notional_value / self.total_capital if self.total_capital > 0 else 0
        
        return CapitalManagementResult(
            position_size=round(position_size, 4),
            risk_amount=round(risk_amount, 2),
            risk_percentage=round(half_optimal * 100, 3),
            reward_amount=round(risk_amount * win_loss_ratio, 2),
            reward_percentage=round(half_optimal * win_loss_ratio * 100, 2),
            leverage_needed=round(leverage_needed, 2),
            rr_ratio=round(win_loss_ratio, 2),
            max_loss=risk_amount,
            recommended_leverage=min(int(leverage_needed), 20),
            capital_after_loss=round(self.total_capital - risk_amount, 2),
            capital_after_win=round(self.total_capital + (risk_amount * win_loss_ratio), 2),
            formulas_used=f"Optimal F (P={w:.1%}, W/L={win_loss_ratio:.2f})",
            warnings=self._generate_warnings(half_optimal * 100, leverage_needed)
        )
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        method: str = 'fixed_risk',
        risk_percentage: float = 1.0,
        leverage_cap: int = 10
    ) -> CapitalManagementResult:
        """
        محاسبه جامع حجم معامله
        
        Args:
            entry_price: قیمت ورود
            stop_loss: حد ضرر
            take_profit: هدف سود
            method: روش محاسبه (fixed_risk, kelly, volatility, optimal_f)
            risk_percentage: درصد ریسک
            leverage_cap: محدودیت اهرم
            
        Returns:
            CapitalManagementResult: نتیجه کامل
        """
        methods = {
            'fixed_risk': self.calculate_fixed_risk,
            'kelly': lambda e, s: self.calculate_kelly_criterion(e, s, take_profit, leverage_cap=leverage_cap),
            'volatility': lambda e, s: self.calculate_volatility_adjusted(e, s, atr=0.5, risk_percentage=risk_percentage),
            'optimal_f': lambda e, s: self.calculate_optimal_f(e, s)
        }
        
        if method not in methods:
            return self._create_error_result(f"روش نامعتبر: {method}")
        
        return methods[method](entry_price, stop_loss)
    
    def get_recommended_settings(self, risk_profile: str = 'moderate') -> Dict[str, Any]:
        """
        دریافت تنظیمات پیشنهادی بر اساس پروفایل ریسک
        
        Args:
            risk_profile: پروفایل ریسک (conservative, moderate, aggressive, very_aggressive)
            
        Returns:
            Dict: تنظیمات پیشنهادی
        """
        profiles = {
            'conservative': {
                'risk_per_trade': 0.5,
                'max_leverage': 5,
                'min_rr_required': 1.5,
                'max_daily_loss': 3.0,
                'description': 'بسیار محافظه‌کارانه - برای مبتدیان'
            },
            'moderate': {
                'risk_per_trade': 1.0,
                'max_leverage': 10,
                'min_rr_required': 1.5,
                'max_daily_loss': 5.0,
                'description': 'متعادل - برای معامله‌گران متوسط'
            },
            'aggressive': {
                'risk_per_trade': 2.0,
                'max_leverage': 20,
                'min_rr_required': 1.0,
                'max_daily_loss': 10.0,
                'description': 'تهاجمی - برای معامله‌گران حرفه‌ای'
            },
            'very_aggressive': {
                'risk_per_trade': 3.0,
                'max_leverage': 50,
                'min_rr_required': 0.75,
                'max_daily_loss': 15.0,
                'description': 'بسیار تهاجمی - فقط برای حرفه‌ای‌ها'
            }
        }
        
        return profiles.get(risk_profile, profiles['moderate'])
    
    def format_result_message(self, result: CapitalManagementResult) -> str:
        """
        فرمت‌بندی نتیجه به صورت پیام قابل خواندن
        
        Args:
            result: نتیجه محاسبات
            
        Returns:
            str: پیام فرمت‌شده
        """
        if result.formulas_used == "Error":
            return f"❌ خطا: {result.warnings[0] if result.warnings else 'خطای نامشخص'}"
        
        message = f"""
━━━━━━━━━━━━━━━━━━━
📊 **نتایج مدیریت سرمایه**

💰 **سرمایه کل:** ${self.total_capital:,.2f}

📈 **حجم معامله:** {result.position_size:.4f}
💵 **مبلغ ریسک:** ${result.risk_amount:,.2f} ({result.risk_percentage}%)

🎯 **سود هدف:** ${result.reward_amount:,.2f} ({result.reward_percentage}%)
📉 **حداکثر ضرر:** ${result.max_loss:,.2f}

⚖️ **نسبت R/R:** 1:{result.rr_ratio}
🔧 **اهرم مورد نیاز:** {result.leverage_needed}x
🎚️ **اهرم پیشنهادی:** {result.recommended_leverage}x

📊 **فرمول استفاده شده:**
{result.formulas_used}

📈 **سرمایه پس از سود:** ${result.capital_after_win:,.2f}
📉 **سرمایه پس از ضرر:** ${result.capital_after_loss:,.2f}
━━━━━━━━━━━━━━━━━━━
"""
        # اضافه کردن هشدارها
        if result.warnings:
            message += "⚠️ **هشدارها:**\n"
            for warning in result.warnings:
                message += f"• {warning}\n"
        
        return message
    
    def _generate_warnings(
        self,
        risk_percentage: float,
        leverage_needed: float,
        atr: float = None
    ) -> list:
        """تولید هشدارها بر اساس محاسبات"""
        warnings = []
        
        if risk_percentage > 2.0:
            warnings.append("⚠️ ریسک بالا! توصیه می‌شود حداکثر 2% ریسک کنید")
        
        if leverage_needed > 20:
            warnings.append("⚠️ اهرم بسیار بالا! ریسک لیکوئیدیتی افزایش می‌یابد")
        
        if leverage_needed > 50:
            warnings.append("🚨 اهرم خطرناک! احتمال لیکوئید شدن بسیار بالاست")
        
        if atr and leverage_needed > 10:
            warnings.append(f"⚠️ با نوسانات فعلی (ATR={atr})، اهرم بالا ریسکی است")
        
        return warnings
    
    def _create_error_result(self, error_message: str) -> CapitalManagementResult:
        """ایجاد نتیجه خطا"""
        return CapitalManagementResult(
            position_size=0,
            risk_amount=0,
            risk_percentage=0,
            reward_amount=0,
            reward_percentage=0,
            leverage_needed=0,
            rr_ratio=0,
            max_loss=0,
            recommended_leverage=1,
            capital_after_loss=self.total_capital,
            capital_after_win=self.total_capital,
            formulas_used="Error",
            warnings=[error_message]
        )


def risk_size_to_price(risk_amount: float, position_size: float, entry_price: float, sl_price: float) -> float:
    """
    تبدیل مبلغ ریسک به فاصله قیمت
    
    Args:
        risk_amount: مبلغ ریسک
        position_size: حجم معامله
        entry_price: قیمت ورود
        sl_price: قیمت حد ضرر
        
    Returns:
        float: فاصله قیمت
    """
    if position_size <= 0:
        return 0
    return risk_amount / position_size


def reward_size_to_price(reward_amount: float, position_size: float, entry_price: float, sl_price: float) -> float:
    """
    تبدیل مبلغ سود به فاصله قیمت
    
    Args:
        reward_amount: مبلغ سود
        position_size: حجم معامله
        entry_price: قیمت ورود
        sl_price: قیمت حد ضرر
        
    Returns:
        float: فاصله قیمت
    """
    if position_size <= 0:
        return 0
    return reward_amount / position_size


def calculate_rr_ratio(take_profit: float, entry_price: float, stop_loss: float) -> float:
    """
    محاسبه نسبت ریسک به ریوارد
    
    Args:
        take_profit: قیمت هدف سود
        entry_price: قیمت ورود
        stop_loss: قیمت حد ضرر
        
    Returns:
        float: نسبت R/R
    """
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    
    if risk <= 0:
        return 0
    
    return round(reward / risk, 2)


# ═══════════════════════════════════════════════════════════════
# 🧪 تست ماژول
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 تست ماژول مدیریت سرمایه")
    print("=" * 60)
    
    # تنظیمات اولیه
    manager = CapitalManager(total_capital=1000.0, risk_per_trade=1.0)
    
    # داده‌های نمونه
    entry_price = 840.54
    stop_loss = 837.50
    take_profit = 845.80
    
    print(f"\n📊 سرمایه: ${manager.total_capital}")
    print(f"📍 ورود: {entry_price}")
    print(f"❌ حد ضرر: {stop_loss}")
    print(f"🎯 هدف: {take_profit}")
    
    # تست Fixed Risk
    print("\n" + "=" * 40)
    print("📌 روش Fixed Risk Percentage:")
    print("=" * 40)
    result = manager.calculate_fixed_risk(entry_price, stop_loss)
    print(manager.format_result_message(result))
    
    # تست Kelly Criterion
    print("\n" + "=" * 40)
    print("📌 روش Kelly Criterion:")
    print("=" * 40)
    manager.update_stats(win_rate=0.55, avg_win=100, avg_loss=50)
    result = manager.calculate_kelly_criterion(entry_price, stop_loss, take_profit)
    print(manager.format_result_message(result))
    
    # تست Optimal F
    print("\n" + "=" * 40)
    print("📌 روش Optimal F:")
    print("=" * 40)
    result = manager.calculate_optimal_f(entry_price, stop_loss)
    print(manager.format_result_message(result))
    
    # تست Volatility-Adjusted
    print("\n" + "=" * 40)
    print("📌 روش Volatility-Adjusted:")
    print("=" * 40)
    result = manager.calculate_volatility_adjusted(entry_price, stop_loss, atr=0.5)
    print(manager.format_result_message(result))
    
    # تنظیمات پیشنهادی
    print("\n" + "=" * 40)
    print("📋 تنظیمات پیشنهادی:")
    print("=" * 40)
    for profile in ['conservative', 'moderate', 'aggressive']:
        settings = manager.get_recommended_settings(profile)
        print(f"\n🔹 {profile.upper()}:")
        print(f"   ریسک: {settings['risk_per_trade']}%")
        print(f"   حداکثر اهرم: {settings['max_leverage']}x")
        print(f"   حداقل RR: 1:{settings['min_rr_required']}")
        print(f"   {settings['description']}")
    
    print("\n✅ تست تکمیل شد!")