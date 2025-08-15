import sqlite3
import datetime
from typing import Optional, List

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица подписок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    payment_id TEXT,
                    amount INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица платежей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    payment_id TEXT UNIQUE,
                    amount INTEGER,
                    status TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_date TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Добавление пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def create_subscription(self, user_id: int, payment_id: str, amount: int = 100000):
        """Создание подписки (amount в копейках, 100000 = 1000 рублей)"""
        end_date = datetime.datetime.now() + datetime.timedelta(days=30)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO subscriptions (user_id, start_date, end_date, payment_id, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, datetime.datetime.now(), end_date, payment_id, amount))
            conn.commit()
    
    def get_user_subscription(self, user_id: int) -> Optional[dict]:
        """Получение активной подписки пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND is_active = 1 AND end_date > ?
                ORDER BY end_date DESC LIMIT 1
            ''', (user_id, datetime.datetime.now()))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'start_date': row[2],
                    'end_date': row[3],
                    'is_active': row[4],
                    'payment_id': row[5],
                    'amount': row[6]
                }
            return None
    
    def deactivate_subscription(self, user_id: int):
        """Деактивация подписки"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE subscriptions 
                SET is_active = 0 
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
    
    def get_expired_subscriptions(self) -> List[dict]:
        """Получение списка истекших подписок"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, end_date FROM subscriptions 
                WHERE is_active = 1 AND end_date <= ?
            ''', (datetime.datetime.now(),))
            
            rows = cursor.fetchall()
            return [{'user_id': row[0], 'end_date': row[1]} for row in rows]
    
    def add_payment(self, user_id: int, payment_id: str, amount: int, status: str = 'pending'):
        """Добавление записи о платеже"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (user_id, payment_id, amount, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, payment_id, amount, status))
            conn.commit()
    
    def update_payment_status(self, payment_id: str, status: str):
        """Обновление статуса платежа"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if status == 'paid':
                cursor.execute('''
                    UPDATE payments 
                    SET status = ?, paid_date = ?
                    WHERE payment_id = ?
                ''', (status, datetime.datetime.now(), payment_id))
            else:
                cursor.execute('''
                    UPDATE payments 
                    SET status = ?
                    WHERE payment_id = ?
                ''', (status, payment_id))
            conn.commit()
