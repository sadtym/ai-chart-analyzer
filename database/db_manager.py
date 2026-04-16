# -*- coding: utf-8 -*-
"""
مدیریت پایگاه داده SQLite برای ربات تلگرام
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

# مسیر پایگاه داده
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'bot_database.db')

def get_connection():
    """ایجاد اتصال به پایگاه داده"""
    return sqlite3.connect(DB_PATH)

def init_database():
    """ایجاد جداول پایگاه داده"""
    conn = get_connection()
    cursor = conn.cursor()

    # جدول کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            access_level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # جدول لاگ درخواست‌ها برای Rate Limiting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # جدول هشدارها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            condition TEXT,
            price REAL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # جدول بک‌تست‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backtests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            strategy_name TEXT,
            symbol TEXT,
            timeframe TEXT,
            results TEXT,  -- JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # جدول واچ‌لیست
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            notes TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()

class UserManager:
    """مدیریت کاربران"""

    @staticmethod
    def add_user(user_id: int, username: str = None, first_name: str = None):
        """افزودن کاربر جدید"""
        conn = get_connection()
        try:
            conn.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_user(user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        conn = get_connection()
        try:
            cursor = conn.execute('''
                SELECT user_id, username, first_name, access_level, created_at, last_active
                FROM users WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'access_level': row[3],
                    'created_at': row[4],
                    'last_active': row[5]
                }
            return None
        finally:
            conn.close()

    @staticmethod
    def increment_request_count(user_id: int, request_type: str):
        """افزایش شمارنده درخواست"""
        conn = get_connection()
        try:
            conn.execute('''
                INSERT INTO request_logs (user_id, request_type)
                VALUES (?, ?)
            ''', (user_id, request_type))
            conn.commit()
        finally:
            conn.close()

class AlertManagerDB:
    """مدیریت هشدارهای پایگاه داده"""

    @staticmethod
    def add_alert(user_id: int, symbol: str, condition: str, price: float):
        """افزودن هشدار جدید"""
        conn = get_connection()
        try:
            conn.execute('''
                INSERT INTO alerts (user_id, symbol, condition, price)
                VALUES (?, ?, ?, ?)
            ''', (user_id, symbol, condition, price))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_user_alerts(user_id: int) -> List[Dict]:
        """دریافت هشدارهای کاربر"""
        conn = get_connection()
        try:
            cursor = conn.execute('''
                SELECT id, symbol, condition, price, is_active, created_at
                FROM alerts WHERE user_id = ? AND is_active = 1
            ''', (user_id,))
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'id': row[0],
                    'symbol': row[1],
                    'condition': row[2],
                    'price': row[3],
                    'is_active': row[4],
                    'created_at': row[5]
                })
            return alerts
        finally:
            conn.close()

class BacktestManager:
    """مدیریت بک‌تست‌ها"""

    @staticmethod
    def save_backtest(user_id: int, strategy_name: str, symbol: str, timeframe: str, results: Dict):
        """ذخیره نتیجه بک‌تست"""
        conn = get_connection()
        try:
            conn.execute('''
                INSERT INTO backtests (user_id, strategy_name, symbol, timeframe, results)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, strategy_name, symbol, timeframe, json.dumps(results)))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_user_backtests(user_id: int) -> List[Dict]:
        """دریافت بک‌تست‌های کاربر"""
        conn = get_connection()
        try:
            cursor = conn.execute('''
                SELECT id, strategy_name, symbol, timeframe, results, created_at
                FROM backtests WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            backtests = []
            for row in cursor.fetchall():
                backtests.append({
                    'id': row[0],
                    'strategy_name': row[1],
                    'symbol': row[2],
                    'timeframe': row[3],
                    'results': json.loads(row[4]),
                    'created_at': row[5]
                })
            return backtests
        finally:
            conn.close()

class WatchlistManager:
    """مدیریت واچ‌لیست"""

    @staticmethod
    def add_to_watchlist(user_id: int, symbol: str, notes: str = None):
        """افزودن نماد به واچ‌لیست"""
        conn = get_connection()
        try:
            conn.execute('''
                INSERT INTO watchlists (user_id, symbol, notes)
                VALUES (?, ?, ?)
            ''', (user_id, symbol, notes))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_watchlist(user_id: int) -> List[Dict]:
        """دریافت واچ‌لیست کاربر"""
        conn = get_connection()
        try:
            cursor = conn.execute('''
                SELECT id, symbol, notes, added_at
                FROM watchlists WHERE user_id = ?
                ORDER BY added_at DESC
            ''', (user_id,))
            watchlist = []
            for row in cursor.fetchall():
                watchlist.append({
                    'id': row[0],
                    'symbol': row[1],
                    'notes': row[2],
                    'added_at': row[3]
                })
            return watchlist
        finally:
            conn.close()

    @staticmethod
    def remove_from_watchlist(user_id: int, symbol: str):
        """حذف نماد از واچ‌لیست"""
        conn = get_connection()
        try:
            conn.execute('''
                DELETE FROM watchlists WHERE user_id = ? AND symbol = ?
            ''', (user_id, symbol))
            conn.commit()
        finally:
            conn.close()

# مقداردهی اولیه پایگاه داده در زمان import
init_database()