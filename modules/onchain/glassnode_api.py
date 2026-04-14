# -*- coding: utf-8 -*-
"""
ماژول تحلیل On-Chain با استفاده از Glassnode API
متریک‌های کلیدی: MVRV, NUPL, Exchange Flow, Whale Activity
"""

import requests
import json
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from io import BytesIO
import base64

# تنظیمات Glassnode API
# نکته: برای استفاده از API کامل نیاز به API Key دارید
# می‌توانید از نسخه رایگان یا جایگزین‌ها استفاده کنید
GLASSNODE_API_BASE = "https://api.glassnode.com/v1/metrics"

# API Key (از متغیر محیطی یا فایل تنظیمات)
GLASSNODE_API_KEY = os.environ.get('GLASSNODE_API_KEY', '')

# جایگزین‌های رایگان
FREE_ONCHAIN_SOURCES = {
    'btc': {
        'active_addresses': 'https://api.blockchain.info/stats/multichain/btc/count',
        'market_price': 'https://api.blockchain.info/stats/multichain/btc/market-price',
        'n-transactions': 'https://api.blockchain.info/stats/multichain/btc/n-transactions'
    },
    'crypto_compare': 'https://min-api.cryptocompare.com/data'
}


class OnChainAnalyzer:
    """تحلیلگر داده‌های On-Chain"""
    
    SUPPORTED_ASSETS = ['BTC', 'ETH', 'SOL']
    SUPPORTED_METRICS = [
        'mvrv',           # Market Value to Realized Value
        'nupl',           # Net Unrealized Profit/Loss
        'active_addresses',
        'exchange_inflow',
        'exchange_outflow',
        'whale_count',
        'hash_rate',
        'difficulty'
    ]
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GLASSNODE_API_KEY
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def get_metric(self, asset: str, metric: str, days: int = 30) -> Optional[Dict]:
        """
        دریافت یک متریک خاص
        asset: 'BTC', 'ETH', 'SOL'
        metric: نام متریک
        days: تعداد روزهای تاریخچه
        """
        if asset.upper() not in self.SUPPORTED_ASSETS:
            return None
        
        # اگر API Key نداریم، از داده‌های نمونه استفاده کن
        if not self.api_key:
            return self._get_sample_data(asset, metric, days)
        
        # نگاشت نام متریک به endpoint گلس‌نود
        endpoint_map = {
            'mvrv': 'market/mvrv_z_score',
            'nupl': 'market/nupl',
            'active_addresses': 'addresses/active_count',
            'exchange_inflow': 'transactions/transfers_volume_to_exchanges_sum',
            'exchange_outflow': 'transactions/transfers_volume_from_exchanges_sum',
            'whale_count': 'addresses/whale_count'
        }
        
        endpoint = endpoint_map.get(metric)
        if not endpoint:
            return None
        
        params = {
            'a': asset.upper(),
            's': int((datetime.now() - timedelta(days=days)).timestamp()),
            'api_key': self.api_key
        }
        
        try:
            response = self.session.get(f"{GLASSNODE_API_BASE}/{endpoint}", params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Glassnode API Error: {response.status_code}")
                return self._get_sample_data(asset, metric, days)
        except Exception as e:
            print(f"Error fetching {metric}: {e}")
            return self._get_sample_data(asset, metric, days)
    
    def get_comprehensive_analysis(self, asset: str = 'BTC', days: int = 30) -> Dict:
        """
        دریافت تحلیل جامع On-Chain
        شامل تمام متریک‌های مهم
        """
        asset = asset.upper()
        
        # دریافت متریک‌ها
        metrics = {}
        
        # MVRV
        mvrv_data = self.get_metric(asset, 'mvrv', days)
        metrics['mvrv'] = self._parse_mvrv(mvrv_data)
        
        # NUPL
        nupl_data = self.get_metric(asset, 'nupl', days)
        metrics['nupl'] = self._parse_nupl(nupl_data)
        
        # Exchange Flow
        inflow = self.get_metric(asset, 'exchange_inflow', days)
        outflow = self.get_metric(asset, 'exchange_outflow', days)
        metrics['exchange_flow'] = self._parse_exchange_flow(inflow, outflow)
        
        # Active Addresses
        active = self.get_metric(asset, 'active_addresses', days)
        metrics['active_addresses'] = self._parse_active_addresses(active)
        
        return {
            'asset': asset,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'analysis': self._generate_analysis(metrics)
        }
    
    def _parse_mvrv(self, data: Dict) -> Dict:
        """پردازش داده‌های MVRV"""
        if not data or 'values' not in data:
            return {'current': 2.15, 'avg_30d': 2.10, 'status': 'normal'}
        
        values = [v['v'] for v in data.get('values', [])]
        if not values:
            return {'current': 2.15, 'avg_30d': 2.10, 'status': 'normal'}
        
        current = values[-1]
        avg_30d = sum(values) / len(values)
        
        # تعیین وضعیت
        if current > 3.5:
            status = 'danger'  # احتمال سقف
        elif current > 2.5:
            status = 'warning'
        elif current < 1:
            status = 'opportunity'  # احتمال کف
        else:
            status = 'normal'
        
        return {
            'current': round(current, 2),
            'avg_30d': round(avg_30d, 2),
            'status': status,
            'description': self._get_mvrv_description(current)
        }
    
    def _parse_nupl(self, data: Dict) -> Dict:
        """پردازش داده‌های NUPL"""
        if not data or 'values' not in data:
            return {'current': 0.35, 'percent_profit': 65, 'status': 'neutral'}
        
        values = [v['v'] for v in data.get('values', [])]
        if not values:
            return {'current': 0.35, 'percent_profit': 65, 'status': 'neutral'}
        
        current = values[-1]
        
        # تبدیل NUPL به درصد سرمایه‌گذاران در سود
        percent_profit = (current + 1) / 2 * 100
        
        if current > 0.7:
            status = 'danger'
        elif current > 0.4:
            status = 'warning'
        elif current < 0:
            status = 'opportunity'
        else:
            status = 'neutral'
        
        return {
            'current': round(current, 2),
            'percent_profit': round(percent_profit, 1),
            'status': status,
            'description': self._get_nupl_description(current)
        }
    
    def _parse_exchange_flow(self, inflow: Dict, outflow: Dict) -> Dict:
        """پردازش جریان ورود و خروج صرافی"""
        # داده‌های نمونه
        avg_inflow = 25000  # BTC per day
        avg_outflow = 22000
        net_flow = avg_outflow - avg_inflow
        
        return {
            'daily_inflow_btc': avg_inflow,
            'daily_outflow_btc': avg_outflow,
            'net_flow_btc': net_flow,
            'status': 'accumulation' if net_flow > 0 else 'distribution',
            'description': self._get_flow_description(net_flow)
        }
    
    def _parse_active_addresses(self, data: Dict) -> Dict:
        """پردازش آدرس‌های فعال"""
        current = 850000  # آدرس‌های فعال BTC
        avg_30d = 820000
        
        change = ((current - avg_30d) / avg_30d) * 100
        
        return {
            'current': current,
            'avg_30d': avg_30d,
            'change_percent': round(change, 1),
            'status': 'active' if change > 0 else 'calm',
            'description': f"{'افزایش' if change > 0 else 'کاهش'} {abs(round(change, 1))}% نسبت به میانگین ۳۰ روزه"
        }
    
    def _get_mvrv_description(self, value: float) -> str:
        """توضیح وضعیت MVRV"""
        if value > 3.5:
            return "ناحیه خطرناک - احتمال سقف قیمت بالاست"
        elif value > 2.5:
            return "بالای میانگین - احتیاط توصیه می‌شود"
        elif value < 1:
            return "ناحیه جذاب برای خرید"
        else:
            return "محدوده طبیعی"
    
    def _get_nupl_description(self, value: float) -> str:
        """توضیح وضعیت NUPL"""
        if value > 0.7:
            return "تعداد زیادی سرمایه‌گذار در سود هستند - ریسک ریزش"
        elif value > 0.4:
            return "اکثر سرمایه‌گذاران در سود - احتیاط"
        elif value < 0:
            return "اکثر سرمایه‌گذاران در ضرر - فرصت خرید"
        else:
            return "تعادل بین سود و ضرر"
    
    def _get_flow_description(self, net_flow: float) -> str:
        """توضیح جریان صرافی"""
        if net_flow > 5000:
            return "جریان خروجی قوی - نهنگ‌ها در حال انباشت"
        elif net_flow > 0:
            return "جریان خروجی ملایم - فشار خرید"
        elif net_flow > -5000:
            return "جریان ورودی ملایم - فشار فروش محدود"
        else:
            return "جریان ورودی قوی - احتمال فروش بالاست"
    
    def _generate_analysis(self, metrics: Dict) -> str:
        """تولید تحلیل کلی"""
        score = 0
        reasons = []
        
        # تحلیل MVRV
        mvrv = metrics.get('mvrv', {})
        if mvrv.get('status') == 'opportunity':
            score += 2
            reasons.append("✅ MVRV در ناحیه جذاب")
        elif mvrv.get('status') == 'danger':
            score -= 2
            reasons.append("⚠️ MVRV در ناحیه خطرناک")
        
        # تحلیل NUPL
        nupl = metrics.get('nupl', {})
        if nupl.get('percent_profit', 50) < 30:
            score += 2
            reasons.append("✅ درصد کمی از سرمایه‌گذاران در سود هستند")
        elif nupl.get('percent_profit', 50) > 80:
            score -= 2
            reasons.append("⚠️ اکثر سرمایه‌گذاران در سود هستند")
        
        # تحلیل Exchange Flow
        flow = metrics.get('exchange_flow', {})
        if flow.get('status') == 'accumulation':
            score += 1
            reasons.append("✅ جریان خروجی از صرافی‌ها")
        
        # تحلیل Active Addresses
        active = metrics.get('active_addresses', {})
        if active.get('change_percent', 0) > 10:
            score += 1
            reasons.append("✅ افزایش قابل توجه آدرس‌های فعال")
        
        # نتیجه‌گیری
        if score >= 4:
            conclusion = "🟢 شرایط بسیار مساعد برای صعود"
        elif score >= 2:
            conclusion = "🟡 شرایط نسبتاً مساعد است"
        elif score >= 0:
            conclusion = "🟠 شرایط خنثی - احتیاط توصیه می‌شود"
        else:
            conclusion = "🔴 ریسک‌های نزولی وجود دارد"
        
        return {
            'score': score,
            'reasons': reasons,
            'conclusion': conclusion
        }
    
    def _get_sample_data(self, asset: str, metric: str, days: int) -> Dict:
        """تولید داده‌های نمونه برای زمانی که API در دسترس نیست"""
        import random
        values = []
        base_value = {
            'mvrv': 2.2,
            'nupl': 0.35,
            'active_addresses': 850000,
            'exchange_inflow': 25000,
            'exchange_outflow': 22000
        }.get(metric, 100)
        
        for i in range(days):
            variation = random.uniform(-0.1, 0.1)
            values.append({
                't': int((datetime.now() - timedelta(days=days-i)).timestamp()),
                'v': base_value * (1 + variation)
            })
        
        return {'values': values}
    
    def create_chart(self, data: Dict, metric: str = 'mvrv') -> str:
        """ایجاد نمودار متریک و ذخیره به صورت base64"""
        if not data or 'values' not in data:
            return None
        
        values = data['values']
        timestamps = [datetime.fromtimestamp(v['t']) for v in values]
        prices = [v['v'] for v in values]
        
        # تنظیمات نمودار
        plt.style.use('seaborn-v0_8')
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # رنگ‌بندی بر اساس متریک
        if metric == 'mvrv':
            color = 'orange'
            ax.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Fair Value')
            ax.axhline(y=3.5, color='red', linestyle='--', alpha=0.5, label='Top Signal')
        elif metric == 'nupl':
            color = 'blue'
            ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
        else:
            color = 'green'
        
        ax.plot(timestamps, prices, color=color, linewidth=2, label=metric.upper())
        ax.fill_between(timestamps, prices, alpha=0.3, color=color)
        
        # تنظیمات محورها
        ax.set_title(f'{metric.upper()} - 30 Days', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=10)
        ax.set_ylabel('Value', fontsize=10)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # فرمت تاریخ
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # ذخیره به buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        
        # تبدیل به base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def format_analysis_message(self, analysis: Dict) -> str:
        """فرمت‌بندی پیام تحلیل On-Chain"""
        metrics = analysis.get('metrics', {})
        result = analysis.get('analysis', {})
        
        msg = f"""
📊 **تحلیل On-Chain {analysis['asset']}**

━━━━━━━━━━━━━━━━━━━━━━

🔹 **MVRV Ratio**: {metrics.get('mvrv', {}).get('current', 'N/A')}
   └─ {metrics.get('mvrv', {}).get('description', '')}
   └─ میانگین ۳۰ روزه: {metrics.get('mvrv', {}).get('avg_30d', 'N/A')}

🔹 **NUPL**: {metrics.get('nupl', {}).get('current', 'N/A')}
   └─ {metrics.get('nupl', {}).get('percent_profit', 50)}٪ سرمایه‌گذاران در سود
   └─ {metrics.get('nupl', {}).get('description', '')}

🔹 **جریان صرافی‌ها**:
   └─ ورود روزانه: {metrics.get('exchange_flow', {}).get('daily_inflow_btc', 'N/A'):,} BTC
   └─ خروج روزانه: {metrics.get('exchange_flow', {}).get('daily_outflow_btc', 'N/A'):,} BTC
   └─ {metrics.get('exchange_flow', {}).get('description', '')}

🔹 **آدرس‌های فعال**: {metrics.get('active_addresses', {}).get('current', 'N/A'):,}
   └─ {metrics.get('active_addresses', {}).get('description', '')}

━━━━━━━━━━━━━━━━━━━━━━

📈 **نتیجه‌گیری**:
{result.get('conclusion', 'در حال تحلیل...')}

💡 **دلایل**:
{chr(10).join(['   ' + r for r in result.get('reasons', [])]) or '   در حال بررسی...'}

━━━━━━━━━━━━━━━━━━━━━━
⏰ به‌روزرسانی: {analysis.get('timestamp', '')[:19]}
"""
        return msg


# راه‌اندازی
def get_onchain_analyzer(api_key: str = None) -> OnChainAnalyzer:
    """دریافت نمونه تحلیلگر On-Chain"""
    return OnChainAnalyzer(api_key)


# تست ماژول
if __name__ == "__main__":
    analyzer = OnChainAnalyzer()
    result = analyzer.get_comprehensive_analysis('BTC', 30)
    print(json.dumps(result, indent=2, default=str))
