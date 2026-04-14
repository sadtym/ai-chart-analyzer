# -*- coding: utf-8 -*-
"""
سرویس مدیریت کاربران و سطوح دسترسی
پشتیبانی از: ثبت‌نام، بررسی دسترسی، Rate Limiting
"""

from datetime import datetime
from database.db_manager import UserManager, get_connection
from typing import Dict, Optional
import json


# سطوح دسترسی
ACCESS_LEVELS = {
    'free': 1,
    'premium': 2,
    'vip': 3
}

# محدودیت‌های هر سطح
ACCESS_LIMITS = {
    1: {  # رایگان
        'onchain_per_day': 3,
        'backtest_per_day': 1,
        'alerts_count': 5,
        'features': ['basic_analysis', 'price_alerts']
    },
    2: {  # پریمیوم
        'onchain_per_day': 20,
        'backtest_per_day': 10,
        'alerts_count': 20,
        'features': ['basic_analysis', 'price_alerts', 'onchain_analysis', 'advanced_alerts']
    },
    3: {  # VIP
        'onchain_per_day': 100,
        'backtest_per_day': 50,
        'alerts_count': 100,
        'features': ['basic_analysis', 'price_alerts', 'onchain_analysis', 
                     'advanced_alerts', 'backtesting', 'priority_support']
    }
}


class AccessControl:
    """کنترل دسترسی کاربران"""
    
    @staticmethod
    def get_user_level(user_id: int) -> int:
        """دریافت سطح دسترسی کاربر"""
        user = UserManager.get_user(user_id)
        return user['access_level'] if user else 1
    
    @staticmethod
    def can_access(user_id: int, feature: str) -> tuple:
        """
        بررسی دسترسی کاربر به یک ویژگی
        Returns: (has_access: bool, message: str)
        """
        user = UserManager.get_user(user_id)
        if not user:
            return False, "⚠️ کاربر یافت نشد. لطفاً /start را بزنید."
        
        level = user['access_level']
        limits = ACCESS_LIMITS.get(level, ACCESS_LIMITS[1])
        
        if feature in limits['features']:
            return True, "✅ دسترسی مجاز"
        
        # بررسی محدودیت روزانه
        if feature == 'onchain':
            remaining = AccessControl.check_daily_limit(user_id, 'onchain')
            if remaining <= 0:
                return False, "🚫 محدودیت روزانه آنچین به اتمام رسید.\nبرای ارتقا /upgrade را بزنید."
        
        if feature == 'backtesting':
            remaining = AccessControl.check_daily_limit(user_id, 'backtest')
            if remaining <= 0:
                return False, "🚫 محدودیت روزانه بک‌تست به اتمام رسید.\nبرای ارتقا /upgrade را بزنید."
        
        # اگر ویژگی در لیست نیست، پیام ارتقا بده
        upgrade_msg = AccessControl.get_upgrade_message(feature)
        return False, upgrade_msg
    
    @staticmethod
    def get_upgrade_message(feature: str) -> str:
        """پیام پیشنهاد ارتقا"""
        messages = {
            'onchain': "🔐 برای دسترسی به تحلیل On-Chain:\n\n"
                      "📊 سطح فعلی شما: رایگان\n"
                      "📈 سطح پریمیوم: ۲۰ درخواست آنچین/روز + تحلیل پیشرفته\n\n"
                      "برای ارتقا با @admin تماس بگیرید.",
            
            'backtesting': "🔐 برای دسترسی به سیستم Backtesting:\n\n"
                          "📊 سطح فعلی شما: رایگان\n"
                          "📈 سطح VIP: بی‌نهایت بک‌تست + استراتژی‌های پیشرفته\n\n"
                          "برای ارتقا با @admin تماس بگیرید.",
            
            'advanced_alerts': "🔐 برای دسترسی به هشدارهای هوشمند:\n\n"
                              "📊 سطح فعلی شما: رایگان\n"
                              "📈 سطح پریمیوم: هشدارهای هوشمند مبتنی بر AI\n\n"
                              "برای ارتقا با @admin تماس بگیرید."
        }
        return messages.get(feature, "🔐 این ویژگی برای سطح بالاتر است.\nبرای ارتقا /upgrade را بزنید.")
    
    @staticmethod
    def check_daily_limit(user_id: int, limit_type: str) -> int:
        """بررسی محدودیت روزانه کاربر"""
        user = UserManager.get_user(user_id)
        if not user:
            return 0
        
        level = user['access_level']
        daily_limit = ACCESS_LIMITS[level].get(f'{limit_type}_per_day', 0)
        
        # محاسبه استفاده امروز
        conn = get_connection()
        try:
            today_start = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.execute('''
                SELECT COUNT(*) FROM request_logs 
                WHERE user_id = ? AND request_type = ? 
                AND date(timestamp) = ?
            ''', (user_id, limit_type, today_start))
            
            used = cursor.fetchone()[0]
            return max(0, daily_limit - used)
        finally:
            conn.close()
    
    @staticmethod
    def log_request(user_id: int, request_type: str):
        """ثبت درخواست برای Rate Limiting"""
        UserManager.increment_request_count(user_id, request_type)


class UserService:
    """سرویس‌های کاربری"""
    
    @staticmethod
    def register_user(user_id: int, username: str = None, first_name: str = None) -> Dict:
        """
        ثبت‌نام کاربر جدید
        Returns: user info dict
        """
        UserManager.add_user(user_id, username, first_name)
        user = UserManager.get_user(user_id)
        return user
    
    @staticmethod
    def get_profile(user_id: int) -> Optional[Dict]:
        """دریافت پروفایل کامل کاربر"""
        user = UserManager.get_user(user_id)
        if not user:
            return None
        
        # افزودن آمار
        stats = UserManager.get_user_stats(user_id)
        limits = ACCESS_LIMITS.get(user['access_level'], ACCESS_LIMITS[1])
        
        profile = {
            'user_id': user['user_id'],
            'username': user['username'],
            'first_name': user['first_name'],
            'join_date': user['join_date'],
            'access_level': user['access_level'],
            'access_name': UserService.get_level_name(user['access_level']),
            'stats': stats,
            'limits': limits,
            'remaining_daily': {
                'onchain': AccessControl.check_daily_limit(user_id, 'onchain'),
                'backtest': AccessControl.check_daily_limit(user_id, 'backtest')
            }
        }
        return profile
    
    @staticmethod
    def get_level_name(level: int) -> str:
        """نام سطح دسترسی"""
        names = {1: 'رایگان', 2: 'پریمیوم', 3: 'VIP'}
        return names.get(level, 'نامشخص')
    
    @staticmethod
    def format_profile_message(profile: Dict) -> str:
        """فرمت‌بندی پیام پروفایل"""
        level_names = {
            1: '🆓 رایگان',
            2: '⭐ پریمیوم',
            3: '👑 VIP'
        }
        
        msg = f"""
👤 **پروفایل کاربری**

🆔 شناسه: `{profile['user_id']}`
📛 نام: {profile.get('first_name', 'ناشناس')}
📅 تاریخ عضویت: {profile['join_date'][:10]}
🏷️ سطح دسترسی: {level_names.get(profile['access_level'], 'نامشخص')}

📊 **آمار استفاده:**
• کل درخواست‌ها: {profile['stats']['request_count']}
• هشدارهای فعال: {profile['stats']['active_alerts']}
• بک‌تست‌های انجام شده: {profile['stats']['backtest_count']}

📈 **محدودیت‌های روزانه:**
• تحلیل آنچین: {profile['remaining_daily']['onchain']} / {ACCESS_LIMITS[profile['access_level']]['onchain_per_day']}
• بک‌تست: {profile['remaining_daily']['backtest']} / {ACCESS_LIMITS[profile['access_level']]['backtest_per_day']}

💼 **لیست ارزها:**
{'، '.join(profile['stats']['watchlist']) if profile['stats']['watchlist'] else 'خالی'}
"""
        return msg
    
    @staticmethod
    def update_settings(user_id: int, settings: Dict) -> bool:
        """بروزرسانی تنظیمات کاربر"""
        user = UserManager.get_user(user_id)
        if not user:
            return False
        
        current_settings = user.get('settings', {})
        current_settings.update(settings)
        
        conn = get_connection()
        try:
            conn.execute(
                'UPDATE users SET settings = ? WHERE user_id = ?',
                (json.dumps(current_settings), user_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def get_watchlist(user_id: int) -> list:
        """دریافت لیست ارزهای مورد علاقه"""
        from database.db_manager import WatchlistManager
        return WatchlistManager.get_all(user_id)
    
    @staticmethod
    def add_to_watchlist(user_id: int, symbol: str) -> tuple:
        """افزودن نماد به لیست"""
        from database.db_manager import WatchlistManager
        success = WatchlistManager.add(user_id, symbol.upper())
        if success:
            return True, f"✅ {symbol.upper()} به لیست ارزها اضافه شد"
        return False, f"⚠️ {symbol.upper()} قبلاً در لیست وجود دارد"
    
    @staticmethod
    def remove_from_watchlist(user_id: int, symbol: str) -> tuple:
        """حذف نماد از لیست"""
        from database.db_manager import WatchlistManager
        success = WatchlistManager.remove(user_id, symbol.upper())
        if success:
            return True, f"✅ {symbol.upper()} از لیست حذف شد"
        return False, f"⚠️ {symbol.upper()} در لیست یافت نشد"


class FeatureChecker:
    """بررسی‌کننده ویژگی‌ها برای دستورات"""
    
    @staticmethod
    def require_onchain(user_id: int) -> tuple:
        """بررسی دسترسی به آنچین"""
        return AccessControl.can_access(user_id, 'onchain_analysis')
    
    @staticmethod
    def require_backtest(user_id: int) -> tuple:
        """بررسی دسترسی به بک‌تست"""
        return AccessControl.can_access(user_id, 'backtesting')
    
    @staticmethod
    def require_premium(user_id: int) -> tuple:
        """بررسی حداقل سطح پریمیوم"""
        user = UserManager.get_user(user_id)
        if not user:
            return False, "⚠️ لطفاً /start را بزنید."
        if user['access_level'] < 2:
            return False, "🔐 این ویژگی برای سطح پریمیوم و بالاتر است."
        return True, "✅ دسترسی مجاز"
    
    @staticmethod
    def require_vip(user_id: int) -> tuple:
        """بررسی سطح VIP"""
        user = UserManager.get_user(user_id)
        if not user:
            return False, "⚠️ لطفاً /start را بزنید."
        if user['access_level'] < 3:
            return False, "👑 این ویژگی فقط برای کاربران VIP است."
        return True, "✅ دسترسی مجاز"
