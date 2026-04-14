"""
ماژول مدیریت هشدارهای قیمت
سیستم هشدار دهی برای رسیدن قیمت به سطح مشخص
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

# مسیر فایل ذخیره هشدارها
ALERTS_FILE = "data/price_alerts.json"


@dataclass
class PriceAlert:
    """ساختار هشدار قیمت"""
    id: str
    user_id: int
    symbol: str
    target_price: float
    condition: str  # "above" یا "below"
    is_active: bool
    created_at: str
    triggered_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class PriceAlertManager:
    """
    مدیریت هشدارهای قیمت
    ذخیره، بررسی و ارسال هشدار
    """
    
    def __init__(self):
        self.alerts: Dict[str, PriceAlert] = {}
        self.load_alerts()
    
    def load_alerts(self):
        """بارگذاری هشدارها از فایل"""
        try:
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for alert_data in data:
                        alert = PriceAlert.from_dict(alert_data)
                        if alert.is_active:
                            self.alerts[alert.id] = alert
                    logger.info(f"✅ {len(self.alerts)} هشدار فعال بارگذاری شد")
        except Exception as e:
            logger.error(f"خطا در بارگذاری هشدارها: {e}")
    
    def save_alerts(self):
        """ذخیره هشدارها در فایل"""
        try:
            # اطمینان از وجود دایرکتوری
            os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
            
            with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
                alerts_data = [alert.to_dict() for alert in self.alerts.values()]
                json.dump(alerts_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"خطا در ذخیره هشدارها: {e}")
    
    def create_alert(self, user_id: int, symbol: str, target_price: float, 
                     condition: str) -> PriceAlert:
        """
        ایجاد هشدار جدید
        
        Args:
            user_id: آیدی کاربر
            symbol: نماد ارز
            target_price: قیمت هدف
            condition: شرط (above/below)
            
        Returns:
            هشدار ایجاد شده
        """
        import uuid
        
        alert_id = str(uuid.uuid4())[:8]
        
        alert = PriceAlert(
            id=alert_id,
            user_id=user_id,
            symbol=symbol.upper(),
            target_price=target_price,
            condition=condition,
            is_active=True,
            created_at=datetime.now().isoformat()
        )
        
        self.alerts[alert_id] = alert
        self.save_alerts()
        
        logger.info(f"✅ هشدار جدید ایجاد شد: {symbol} @ {target_price} ({condition})")
        return alert
    
    def get_user_alerts(self, user_id: int) -> List[PriceAlert]:
        """دریافت تمام هشدارهای یک کاربر"""
        return [alert for alert in self.alerts.values() if alert.user_id == user_id]
    
    def delete_alert(self, alert_id: str, user_id: int) -> bool:
        """حذف هشدار"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            if alert.user_id == user_id:
                del self.alerts[alert_id]
                self.save_alerts()
                return True
        return False
    
    def check_alerts(self, current_prices: Dict[str, float]) -> List[PriceAlert]:
        """
        بررسی هشدارها و یافتن هشدارهای فعال شده
        
        Args:
            current_prices: دیکشنری قیمت‌های فعلی
            
        Returns:
            لیست هشدارهای فعال شده
        """
        triggered = []
        
        for alert_id, alert in list(self.alerts.items()):
            if not alert.is_active:
                continue
            
            symbol = alert.symbol.upper()
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            
            # بررسی شرط
            should_trigger = False
            if alert.condition == "above" and current_price >= alert.target_price:
                should_trigger = True
            elif alert.condition == "below" and current_price <= alert.target_price:
                should_trigger = True
            
            if should_trigger:
                alert.is_active = False
                alert.triggered_at = datetime.now().isoformat()
                triggered.append(alert)
                logger.info(f"🔔 هشدار فعال شد: {symbol} @ {alert.target_price}")
        
        if triggered:
            self.save_alerts()
        
        return triggered
    
    def format_alert_list(self, user_id: int) -> str:
        """فرمت‌بندی لیست هشدارها برای نمایش"""
        alerts = self.get_user_alerts(user_id)
        
        if not alerts:
            return "🔔 هیچ هشدار فعالی ندارید.\n\n" \
                   "برای تنظیم هشدار جدید از دستور زیر استفاده کنید:\n" \
                   "/alert BTC 95000 above"
        
        message = "🔔 **هشدارهای قیمت شما:**\n" \
                  "─" * 30 + "\n\n"
        
        for i, alert in enumerate(alerts, 1):
            emoji = "🟢" if alert.condition == "above" else "🔴"
            status = "⏳ فعال" if alert.is_active else "✅ فعال شده"
            
            message += f"{i}. **{alert.symbol}**\n"
            message += f"   {emoji} قیمت: `${alert.target_price:,.2f}`\n"
            message += f"   شرط: وقتی قیمت {alert.condition} این سطح شود\n"
            message += f"   وضعیت: {status}\n"
            message += f"   ID: `{alert.id}`\n\n"
        
        message += "─" * 30 + "\n" \
                   "برای حذف هشدار از دستور زیر استفاده کنید:\n" \
                   "/delalert [ID]"
        
        return message


# نمونه جهانی مدیریت هشدارها
alert_manager = PriceAlertManager()
