import uuid
import requests
import base64
import json
import datetime
from typing import Optional

class YooKassaPayment:
    def __init__(self, shop_id: str, secret_key: str):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.api_url = "https://api.yookassa.ru/v3"
    
    def _get_headers(self):
        """Получение заголовков для запросов к API"""
        credentials = f"{self.shop_id}:{self.secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(uuid.uuid4())
        }
    
    def create_payment(self, amount: int, description: str, user_id: int, return_url: str = None) -> Optional[dict]:
        """
        Создание платежа
        amount - сумма в копейках (1000 рублей = 100000 копеек)
        """
        payment_data = {
            "amount": {
                "value": f"{amount / 100:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url or "https://t.me/your_bot"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id)
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/payments",
                headers=self._get_headers(),
                json=payment_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка создания платежа: {response.text}")
                return None
                
        except Exception as e:
            print(f"Ошибка при создании платежа: {e}")
            return None
    
    def check_payment_status(self, payment_id: str) -> Optional[dict]:
        """Проверка статуса платежа"""
        try:
            response = requests.get(
                f"{self.api_url}/payments/{payment_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка проверки платежа: {response.text}")
                return None
                
        except Exception as e:
            print(f"Ошибка при проверке платежа: {e}")
            return None
    
    def create_subscription(self, amount: int, user_id: int, description: str = "Подписка на канал") -> Optional[dict]:
        """Создание автоплатежа (подписки)"""
        payment_data = {
            "amount": {
                "value": f"{amount / 100:.2f}",
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/your_bot"
            },
            "capture": True,
            "save_payment_method": True,  # Сохраняем способ оплаты для автоплатежей
            "description": description,
            "metadata": {
                "user_id": str(user_id),
                "subscription": "true"
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/payments",
                headers=self._get_headers(),
                json=payment_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка создания подписки: {response.text}")
                return None
                
        except Exception as e:
            print(f"Ошибка при создании подписки: {e}")
            return None
    
    def charge_saved_payment_method(self, payment_method_id: str, amount: int, user_id: int) -> Optional[dict]:
        """Списание с сохраненного способа оплаты (автоплатеж)"""
        payment_data = {
            "amount": {
                "value": f"{amount / 100:.2f}",
                "currency": "RUB"
            },
            "payment_method_id": payment_method_id,
            "capture": True,
            "description": "Автоплатеж за подписку",
            "metadata": {
                "user_id": str(user_id),
                "auto_payment": "true"
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/payments",
                headers=self._get_headers(),
                json=payment_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка автоплатежа: {response.text}")
                return None
                
        except Exception as e:
            print(f"Ошибка при автоплатеже: {e}")
            return None


# Пример простой системы платежей (заглушка для тестирования)
class MockPaymentSystem:
    """Простая заглушка для тестирования без реальных платежей"""
    
    def __init__(self):
        self.payments = {}
    
    def create_payment(self, amount: int, description: str, user_id: int) -> dict:
        payment_id = str(uuid.uuid4())
        self.payments[payment_id] = {
            "id": payment_id,
            "status": "pending",
            "amount": amount,
            "user_id": user_id,
            "description": description,
            "confirmation": {
                "confirmation_url": f"https://mock-payment.example.com/pay/{payment_id}"
            }
        }
        return self.payments[payment_id]
    
    def check_payment_status(self, payment_id: str) -> Optional[dict]:
        return self.payments.get(payment_id)
    
    def simulate_successful_payment(self, payment_id: str):
        """Имитация успешной оплаты (для тестирования)"""
        if payment_id in self.payments:
            self.payments[payment_id]["status"] = "succeeded"
            return True
        return False


class RobokassaPayment:
    def __init__(self, merchant_login: str, password1: str, password2: str, test_mode: bool = True):
        self.merchant_login = merchant_login
        self.password1 = password1  # Пароль #1 для формирования подписи
        self.password2 = password2  # Пароль #2 для проверки подписи
        self.test_mode = test_mode
        
        if test_mode:
            self.pay_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
            self.api_url = "https://auth.robokassa.ru/Merchant/WebService/Service.asmx"
        else:
            self.pay_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
            self.api_url = "https://auth.robokassa.ru/Merchant/WebService/Service.asmx"
    
    def _generate_signature_pay(self, out_sum: float, inv_id: int) -> str:
        """Генерация подписи для оплаты"""
        import hashlib
        
        # mrh_login:OutSum:InvId:mrh_pass1
        signature_string = f"{self.merchant_login}:{out_sum}:{inv_id}:{self.password1}"
        return hashlib.md5(signature_string.encode()).hexdigest().upper()
    
    def _generate_signature_result(self, out_sum: float, inv_id: int) -> str:
        """Генерация подписи для проверки результата"""
        import hashlib
        
        # OutSum:InvId:mrh_pass2
        signature_string = f"{out_sum}:{inv_id}:{self.password2}"
        return hashlib.md5(signature_string.encode()).hexdigest().upper()
    
    def create_payment(self, amount: int, description: str, user_id: int) -> Optional[dict]:
        """
        Создание платежа
        amount - сумма в копейках (1000 рублей = 100000 копеек)
        """
        try:
            out_sum = amount / 100  # Переводим в рубли
            inv_id = int(f"{user_id}{int(datetime.datetime.now().timestamp())}")  # Уникальный ID заказа
            
            # Генерируем подпись
            signature = self._generate_signature_pay(out_sum, inv_id)
            
            # Параметры для оплаты
            payment_params = {
                'MrchLogin': self.merchant_login,
                'OutSum': out_sum,
                'InvId': inv_id,
                'Desc': description,
                'SignatureValue': signature,
                'Culture': 'ru',
                'IsTest': 1 if self.test_mode else 0
            }
            
            # Формируем URL для оплаты
            params_string = '&'.join([f"{key}={value}" for key, value in payment_params.items()])
            payment_url = f"{self.pay_url}?{params_string}"
            
            return {
                'id': str(inv_id),
                'status': 'pending',
                'amount': amount,
                'user_id': user_id,
                'description': description,
                'confirmation': {
                    'confirmation_url': payment_url
                },
                'metadata': {
                    'out_sum': out_sum,
                    'inv_id': inv_id,
                    'signature': signature
                }
            }
            
        except Exception as e:
            print(f"Ошибка создания платежа Робокасса: {e}")
            return None
    
    def check_payment_status(self, payment_id: str) -> Optional[dict]:
        """Проверка статуса платежа через Робокассу"""
        try:
            import xml.etree.ElementTree as ET
            
            # Для проверки статуса используем OpState
            inv_id = int(payment_id)
            
            # Генерируем подпись для запроса статуса
            import hashlib
            signature_string = f"{self.merchant_login}:{inv_id}:{self.password2}"
            signature = hashlib.md5(signature_string.encode()).hexdigest().upper()
            
            # Параметры запроса
            params = {
                'MerchantLogin': self.merchant_login,
                'InvoiceID': inv_id,
                'Signature': signature
            }
            
            # Формируем URL для проверки
            url = f"{self.api_url}/OpState"
            
            # В реальной реализации здесь должен быть HTTP запрос к API
            # Для демонстрации возвращаем заглушку
            return {
                'id': payment_id,
                'status': 'pending',  # pending, succeeded, failed
                'amount': 100000,
                'description': 'Тестовый платеж'
            }
            
        except Exception as e:
            print(f"Ошибка проверки платежа Робокасса: {e}")
            return None
    
    def verify_payment_result(self, out_sum: float, inv_id: int, signature: str) -> bool:
        """Проверка подписи результата платежа"""
        expected_signature = self._generate_signature_result(out_sum, inv_id)
        return signature.upper() == expected_signature
    
    def create_subscription(self, amount: int, user_id: int, description: str = "Подписка на канал") -> Optional[dict]:
        """
        Создание подписки (рекуррентного платежа)
        Робокасса поддерживает рекуррентные платежи через отдельный сервис
        """
        # Для рекуррентных платежей нужно использовать Робокасса Рекуррент
        # Это более сложная настройка, требующая отдельного договора
        
        # Пока создаем обычный платеж
        return self.create_payment(amount, description, user_id)
    
    def charge_saved_payment_method(self, payment_method_id: str, amount: int, user_id: int) -> Optional[dict]:
        """
        Списание с сохраненного способа оплаты (рекуррентный платеж)
        Требует настройки Робокасса Рекуррент
        """
        # Это заглушка - для реальной реализации нужен Робокасса Рекуррент
        print(f"Попытка рекуррентного платежа: {amount} копеек для пользователя {user_id}")
        
        # Имитация неудачного автоплатежа (пока не настроен)
        return None
