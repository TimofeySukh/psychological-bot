import asyncio
import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

from database import Database
from payment_system import MockPaymentSystem, YooKassaPayment, RobokassaPayment
from subscription_manager import SubscriptionManager, run_subscription_checker

# Загружаем переменные окружения
load_dotenv()

# Настройки бота из .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
FREE_CHANNEL_LINK = os.getenv('FREE_CHANNEL_LINK')
PAID_CHANNEL_LINK = os.getenv('PAID_CHANNEL_LINK')
PAID_CHANNEL_ID = os.getenv('PAID_CHANNEL_ID')

# Настройки платежей из .env
USE_REAL_PAYMENTS = os.getenv('USE_REAL_PAYMENTS', 'False').lower() == 'true'
PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'mock')

# Робокасса
ROBOKASSA_MERCHANT_LOGIN = os.getenv('ROBOKASSA_MERCHANT_LOGIN')
ROBOKASSA_PASSWORD1 = os.getenv('ROBOKASSA_PASSWORD1')
ROBOKASSA_PASSWORD2 = os.getenv('ROBOKASSA_PASSWORD2')
ROBOKASSA_TEST_MODE = os.getenv('ROBOKASSA_TEST_MODE', 'True').lower() == 'true'

# ЮKassa
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

# База данных
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot_database.db')

# Инициализация компонентов
db = Database(DATABASE_PATH)

if USE_REAL_PAYMENTS:
    if PAYMENT_PROVIDER == "robokassa":
        payment_system = RobokassaPayment(
            ROBOKASSA_MERCHANT_LOGIN, 
            ROBOKASSA_PASSWORD1, 
            ROBOKASSA_PASSWORD2,
            ROBOKASSA_TEST_MODE
        )
    elif PAYMENT_PROVIDER == "yookassa":
        payment_system = YooKassaPayment(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
    else:
        payment_system = MockPaymentSystem()
else:
    payment_system = MockPaymentSystem()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Тексты сообщений
WELCOME_TEXT = """Привет! Это Ольга Сухова и мой бот-ассистент, я благодарю тебя за интерес к моему каналу и помогу тебе во всём, что касается присоединению к каналу и твоему комфортному нахождению в нём."""

ABOUT_CHANNEL_TEXT = """Мой канал — для тех, кто не прячется за оправданиями и не списывает всё подряд на «плохое настроение», а хочет осознанно и целостно подойти к своему здоровью — и телесному, и ментальному."""

PHILOSOPHY_TEXT = """Моя внутренняя философия проста: тело и голова работают в связке, и лечить одно без другого — всё равно что чинить крышу, игнорируя дырявый фундамент.

Всё, о чём я рассказываю, основано на моём личном опыте и профессиональных знаниях. Но важно помнить: мои материалы не заменяют врачей, психотерапию или спорт, а ведут и направляют к себе и своему пути."""

WHAT_I_GIVE_TEXT = """Я хочу вам дать место еженедельного апгрейда, через понимание своей уникальности — без гонки за чужим «успешным успехом» и без завышенных требований к себе, но и без тихого болота, где «принятие себя» становится поводом ничего не делать."""

CHANNEL_CONTENT_TEXT = """Каждый месяц мы разбираем одну тему — о здоровье, психике или жизненных ролях.
Вас ждёт:
- 5–7 постов в месяц
- подробный гайд по теме
- полезные лайфхаки
- практические задания"""

SUBSCRIPTION_INFO_TEXT = """💰 Стоимость: 1 000 ₽ в месяц
📅 Списания: раз в месяц с привязанной карты, продление — автоматическое.
🛠 После оплаты: вы получите ссылку на закрытый канал.
❌ Отмена: в любой момент через команду /subscription.
🌍 Оплата из-за рубежа: напишите в службу заботы — поможем оплатить с иностранной карты."""

DOCUMENTS_TEXT = """Осталась последняя формальность!

Необходимо принять условия оферты, политики обработки персональных данных и предоставить согласие на их обработку.

1. Договор оферты
2. Политика обработки персональных данных
3. Согласие на обработку персональных данных"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при вызове команды /start."""
    user = update.effective_user
    
    # Добавляем пользователя в БД
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    keyboard = [
        [InlineKeyboardButton("Про что мой канал", callback_data="about_channel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_TEXT, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия кнопок."""
    query = update.callback_query
    await query.answer()

    if query.data == "about_channel":
        keyboard = [
            [InlineKeyboardButton("А что ещё?", callback_data="philosophy")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=ABOUT_CHANNEL_TEXT, reply_markup=reply_markup)
    
    elif query.data == "philosophy":
        keyboard = [
            [InlineKeyboardButton("Что хочу вам дать?", callback_data="what_i_give")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=PHILOSOPHY_TEXT, reply_markup=reply_markup)
    
    elif query.data == "what_i_give":
        keyboard = [
            [InlineKeyboardButton("Что внутри канала?", callback_data="channel_content")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=WHAT_I_GIVE_TEXT, reply_markup=reply_markup)
    
    elif query.data == "channel_content":
        keyboard = [
            [InlineKeyboardButton("Как оформить подписку?", callback_data="subscription_info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=CHANNEL_CONTENT_TEXT, reply_markup=reply_markup)
    
    elif query.data == "subscription_info":
        keyboard = [
            [InlineKeyboardButton("Далее", callback_data="documents")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=SUBSCRIPTION_INFO_TEXT, reply_markup=reply_markup)
    
    elif query.data == "documents":
        keyboard = [
            [InlineKeyboardButton("Принято", callback_data="accepted")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text=DOCUMENTS_TEXT, reply_markup=reply_markup)
    
    elif query.data == "accepted":
        keyboard = [
            [InlineKeyboardButton("Перейти к оплате подписки", callback_data="payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text="Отлично! Теперь можно перейти к оплате.", reply_markup=reply_markup)
    
    elif query.data == "payment":
        user_id = query.from_user.id
        
        # Проверяем, есть ли уже активная подписка
        subscription = db.get_user_subscription(user_id)
        if subscription:
            await query.message.reply_text(
                text="✅ У вас уже есть активная подписка! "
                     f"Действует до: {subscription['end_date']}"
            )
            return
        
        # Создаем платеж
        payment = payment_system.create_payment(
            amount=100000,  # 1000 рублей в копейках
            description="Подписка на канал Ольги Суховой",
            user_id=user_id
        )
        
        if payment:
            # Сохраняем информацию о платеже в БД
            db.add_payment(
                user_id=user_id,
                payment_id=payment['id'],
                amount=100000,
                status='pending'
            )
            
            if USE_REAL_PAYMENTS:
                # Для реальных платежей отправляем ссылку на оплату
                payment_url = payment['confirmation']['confirmation_url']
                keyboard = [
                    [InlineKeyboardButton("💳 Оплатить", url=payment_url)],
                    [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_payment_{payment['id']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    text="💳 Для оплаты подписки нажмите кнопку ниже.\n\n"
                         "После успешной оплаты нажмите 'Проверить оплату'.",
                    reply_markup=reply_markup
                )
            else:
                # Для тестирования автоматически помечаем платеж как успешный
                payment_system.simulate_successful_payment(payment['id'])
                await process_successful_payment(payment['id'], query)
        else:
            await query.message.reply_text(
                text="❌ Ошибка создания платежа. Попробуйте позже или обратитесь в поддержку."
            )
    
    elif query.data.startswith("check_payment_"):
        payment_id = query.data.replace("check_payment_", "")
        await check_payment_status(payment_id, query)
    
    elif query.data == "cancel_subscription":
        user_id = query.from_user.id
        
        # Деактивируем подписку
        db.deactivate_subscription(user_id)
        
        # Удаляем из канала
        try:
            bot = query.bot
            subscription_manager = SubscriptionManager(bot, db, payment_system, PAID_CHANNEL_ID)
            await subscription_manager._remove_user_from_channel(user_id)
            
            await query.message.reply_text(
                text="✅ Подписка отменена. Автоплатежи остановлены.\n\n"
                     "Вы можете оформить новую подписку в любое время, нажав /start"
            )
        except Exception as e:
            logging.error(f"Ошибка при отмене подписки: {e}")
            await query.message.reply_text(
                text="✅ Подписка отменена. Автоплатежи остановлены."
            )
    
    else:
        await query.message.reply_text(text=f"Неизвестная команда: {query.data}")

async def check_payment_status(payment_id: str, query):
    """Проверка статуса платежа"""
    payment_info = payment_system.check_payment_status(payment_id)
    
    if payment_info and payment_info.get('status') == 'succeeded':
        await process_successful_payment(payment_id, query)
    else:
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{payment_id}")],
            [InlineKeyboardButton("💳 Оплатить заново", callback_data="payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            text="⏳ Оплата еще не поступила. Проверьте еще раз через несколько минут.",
            reply_markup=reply_markup
        )

async def process_successful_payment(payment_id: str, query):
    """Обработка успешной оплаты"""
    user_id = query.from_user.id
    
    # Обновляем статус платежа в БД
    db.update_payment_status(payment_id, 'paid')
    
    # Создаем подписку
    db.create_subscription(user_id, payment_id, 100000)
    
    # Добавляем пользователя в канал (если subscription_manager инициализирован)
    try:
        bot = query.bot
        subscription_manager = SubscriptionManager(bot, db, payment_system, PAID_CHANNEL_ID)
        success = await subscription_manager.add_user_to_channel(user_id)
        
        if success:
            await query.message.reply_text(
                text="🎉 Отлично! Оплата прошла успешно.\n\n"
                     "Вы получили персональную ссылку для доступа к каналу. "
                     "Подписка активна на 30 дней с автоматическим продлением.\n\n"
                     "Для управления подпиской используйте команду /subscription"
            )
        else:
            await query.message.reply_text(
                text="✅ Оплата прошла успешно, но возникла проблема с добавлением в канал. "
                     "Обратитесь в поддержку для получения доступа."
            )
    except Exception as e:
        logging.error(f"Ошибка при обработке успешной оплаты: {e}")
        await query.message.reply_text(
            text="✅ Оплата прошла успешно! Скоро вы получите доступ к каналу."
        )

async def subscription_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для управления подпиской"""
    user_id = update.effective_user.id
    subscription = db.get_user_subscription(user_id)
    
    if subscription:
        keyboard = [
            [InlineKeyboardButton("❌ Отменить подписку", callback_data="cancel_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=f"📋 Ваша подписка:\n\n"
                 f"Статус: {'✅ Активна' if subscription['is_active'] else '❌ Неактивна'}\n"
                 f"Действует до: {subscription['end_date']}\n"
                 f"Стоимость: {subscription['amount'] / 100} ₽\n\n"
                 f"Автоплатеж включен. Подписка будет автоматически продлена.",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🛒 Оформить подписку", callback_data="about_channel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text="❌ У вас нет активной подписки.\n\n"
                 "Хотите оформить подписку на канал?",
            reply_markup=reply_markup
        )

async def get_chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Временная команда для получения chat_id каналов"""
    try:
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        chat_title = getattr(update.effective_chat, 'title', 'Без названия')
        user_name = update.effective_user.first_name if update.effective_user else "Неизвестный"
        
        message = f"🆔 **Информация о чате:**\n\n"
        message += f"📱 Chat ID: `{chat_id}`\n"
        message += f"📋 Тип чата: {chat_type}\n"
        message += f"📝 Название: {chat_title}\n"
        message += f"👤 Запросил: {user_name}\n\n"
        
        if chat_type == "private":
            message += "📝 **Для получения ID канала:**\n"
            message += "1️⃣ Добавьте бота в ваш приватный канал как администратора\n"
            message += "2️⃣ Дайте боту права: 'Приглашать пользователей' и 'Банить пользователей'\n"
            message += "3️⃣ Отправьте команду `/get_chat_id` в канале\n"
            message += "4️⃣ Скопируйте полученный Chat ID\n"
            message += "5️⃣ Вставьте его в переменную PAID_CHANNEL_ID в main.py"
        elif chat_type in ["group", "supergroup"]:
            message += "✅ **Это группа!**\n"
            message += f"Используйте этот Chat ID: `{chat_id}`"
        elif chat_type == "channel":
            message += "🎯 **Это канал!**\n"
            message += f"✅ Используйте этот Chat ID: `{chat_id}`\n"
            message += "⚠️ Убедитесь, что бот является администратором канала!"
        else:
            message += f"❓ Неизвестный тип чата: {chat_type}"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        # Дублируем в логи для разработчика
        logging.info(f"Chat ID запрошен: {chat_id}, тип: {chat_type}, название: {chat_title}")
        
    except Exception as e:
        error_message = f"❌ Ошибка при получении информации о чате:\n`{str(e)}`"
        await update.message.reply_text(error_message, parse_mode='Markdown')
        logging.error(f"Ошибка в get_chat_id_command: {e}")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Тестовая команда для проверки работы бота"""
    await update.message.reply_text(
        "🤖 Бот работает!\n\n"
        "Доступные команды:\n"
        "• /start - главное меню\n"
        "• /subscription - управление подпиской\n"
        "• /get_chat_id - получить ID чата\n"
        "• /test - эта команда"
    )

def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscription", subscription_command))
    application.add_handler(CommandHandler("get_chat_id", get_chat_id_command))  # Временная команда
    application.add_handler(CommandHandler("test", test_command))  # Тестовая команда
    application.add_handler(CallbackQueryHandler(button))

    # Создаем subscription_manager для фоновых задач
    bot = application.bot
    subscription_manager = SubscriptionManager(bot, db, payment_system, PAID_CHANNEL_ID)
    
    # Запускаем фоновую задачу проверки подписок после инициализации
    async def post_init(application):
        asyncio.create_task(run_subscription_checker(subscription_manager))
    
    application.post_init = post_init
    
    logging.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main() 