import asyncio
import datetime
import logging
from typing import List
from telegram import Bot
from telegram.error import TelegramError
from database import Database
from payment_system import YooKassaPayment, MockPaymentSystem, RobokassaPayment

class SubscriptionManager:
    def __init__(self, bot: Bot, db: Database, payment_system, paid_channel_id: str):
        self.bot = bot
        self.db = db
        self.payment_system = payment_system
        self.paid_channel_id = paid_channel_id  # ID платного канала (без @)
        self.logger = logging.getLogger(__name__)
    
    async def check_and_process_expired_subscriptions(self):
        """Проверка и обработка истекших подписок"""
        try:
            expired_subscriptions = self.db.get_expired_subscriptions()
            
            for subscription in expired_subscriptions:
                user_id = subscription['user_id']
                
                # Попытка автоплатежа
                success = await self._try_auto_payment(user_id)
                
                if not success:
                    # Если автоплатеж неудачен, удаляем из канала
                    await self._remove_user_from_channel(user_id)
                    await self._notify_user_subscription_expired(user_id)
                    
                    # Деактивируем подписку в БД
                    self.db.deactivate_subscription(user_id)
                    
                    self.logger.info(f"Подписка пользователя {user_id} истекла и деактивирована")
                else:
                    self.logger.info(f"Автоплатеж для пользователя {user_id} успешен")
        
        except Exception as e:
            self.logger.error(f"Ошибка при проверке подписок: {e}")
    
    async def _try_auto_payment(self, user_id: int) -> bool:
        """Попытка автоплатежа"""
        try:
            # Здесь должна быть логика получения сохраненного способа оплаты
            
            if isinstance(self.payment_system, YooKassaPayment):
                # Для реальной ЮKassa нужно сохранять payment_method_id после первой оплаты
                # payment_method_id = self._get_saved_payment_method(user_id)
                # if payment_method_id:
                #     result = self.payment_system.charge_saved_payment_method(
                #         payment_method_id, 100000, user_id
                #     )
                #     return result and result.get('status') == 'succeeded'
                return False  # Пока не реализовано
            
            elif isinstance(self.payment_system, RobokassaPayment):
                # Для Робокассы рекуррентные платежи требуют отдельного сервиса "Робокасса Рекуррент"
                # payment_method_id = self._get_saved_payment_method(user_id)
                # if payment_method_id:
                #     result = self.payment_system.charge_saved_payment_method(
                #         payment_method_id, 100000, user_id
                #     )
                #     return result and result.get('status') == 'succeeded'
                return False  # Пока не реализовано
            
            elif isinstance(self.payment_system, MockPaymentSystem):
                # Имитация автоплатежа
                payment = self.payment_system.create_payment(100000, "Автоплатеж", user_id)
                # Автоматически помечаем как успешный для тестирования
                self.payment_system.simulate_successful_payment(payment['id'])
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка автоплатежа для пользователя {user_id}: {e}")
            return False
    
    async def _remove_user_from_channel(self, user_id: int):
        """Удаление пользователя из платного канала"""
        try:
            await self.bot.ban_chat_member(
                chat_id=self.paid_channel_id,  # Используем chat_id напрямую
                user_id=user_id
            )
            # Сразу разбаниваем, чтобы пользователь мог снова подписаться
            await self.bot.unban_chat_member(
                chat_id=self.paid_channel_id,
                user_id=user_id
            )
            self.logger.info(f"Пользователь {user_id} удален из канала")
            
        except TelegramError as e:
            self.logger.error(f"Ошибка удаления пользователя {user_id} из канала: {e}")
    
    async def _notify_user_subscription_expired(self, user_id: int):
        """Уведомление пользователя об истечении подписки"""
        try:
            message = """🔔 Ваша подписка на канал истекла!
            
Для продолжения доступа к эксклюзивному контенту, пожалуйста, продлите подписку.

Нажмите /start чтобы оформить новую подписку."""
            
            await self.bot.send_message(chat_id=user_id, text=message)
            
        except TelegramError as e:
            self.logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
    
    async def add_user_to_channel(self, user_id: int) -> bool:
        """Добавление пользователя в платный канал"""
        try:
            # Создаем инвайт-ссылку для пользователя
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=self.paid_channel_id,  # Используем chat_id напрямую
                member_limit=1,  # Только для одного пользователя
                expire_date=datetime.datetime.now() + datetime.timedelta(hours=1)  # Действует час
            )
            
            # Отправляем ссылку пользователю
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Поздравляем! Оплата прошла успешно.\n\n"
                     f"Вот ваша персональная ссылка для доступа к каналу:\n"
                     f"{invite_link.invite_link}\n\n"
                     f"⚠️ Ссылка действует 1 час и только для вас."
            )
            
            return True
            
        except TelegramError as e:
            self.logger.error(f"Ошибка добавления пользователя {user_id} в канал: {e}")
            return False
    
    async def notify_subscription_expiring_soon(self, days_before: int = 3):
        """Уведомление о скором истечении подписки"""
        try:
            # Находим подписки, которые истекают через N дней
            future_date = datetime.datetime.now() + datetime.timedelta(days=days_before)
            
            # Здесь нужно добавить метод в Database для поиска подписок по дате
            # expiring_soon = self.db.get_subscriptions_expiring_before(future_date)
            
            # for subscription in expiring_soon:
            #     await self._notify_user_subscription_expiring(subscription['user_id'], days_before)
            
        except Exception as e:
            self.logger.error(f"Ошибка уведомления о скором истечении: {e}")
    
    async def _notify_user_subscription_expiring(self, user_id: int, days_left: int):
        """Уведомление конкретного пользователя о скором истечении"""
        try:
            message = f"""⏰ Ваша подписка истекает через {days_left} дня!
            
Не забудьте продлить подписку, чтобы не потерять доступ к эксклюзивному контенту.

При активном автоплатеже продление произойдет автоматически."""
            
            await self.bot.send_message(chat_id=user_id, text=message)
            
        except TelegramError as e:
            self.logger.error(f"Ошибка отправки уведомления о скором истечении пользователю {user_id}: {e}")


async def run_subscription_checker(subscription_manager: SubscriptionManager):
    """Фоновая задача для проверки подписок"""
    while True:
        try:
            await subscription_manager.check_and_process_expired_subscriptions()
            # Проверяем каждый час
            await asyncio.sleep(3600)
            
        except Exception as e:
            logging.error(f"Ошибка в фоновой задаче проверки подписок: {e}")
            await asyncio.sleep(300)  # При ошибке ждем 5 минут
