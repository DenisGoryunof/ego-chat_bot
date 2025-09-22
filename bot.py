
import os
import logging
import json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest
from telegram.error import BadRequest
from dotenv import load_dotenv
from dateutil import parser

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ID администраторов из .env
ADMIN_MANICURE = int(os.getenv('ADMIN_MANICURE', 1373071419))
ADMIN_OTHER = int(os.getenv('ADMIN_OTHER', 1094720117))
ADMIN_ALL = int(os.getenv('ADMIN_ALL', 130208292))

# Контакты студии из .env
STUDIO_CONTACTS = {
    'phone': os.getenv('STUDIO_PHONE', '+7 (978) 859-03-84'),
    'instagram': os.getenv('STUDIO_INSTAGRAM', '@ego_sevastopol'),
    'address': os.getenv('STUDIO_ADDRESS', 'г.Севатополь, ул 6-я Бастионная, д.40 2й этаж'),
    'hours': os.getenv('STUDIO_HOURS', 'Ежедневно с 9:00 до 19:00')
}

# Группы услуг для разных администраторов
MANICURE_SERVICES = ['💅 Маникюр', '👣 Педикюр']
OTHER_SERVICES = ['🧖 Лазерная эпиляция', '☀️ Моментальный загар', '💄 Визажист', '👁️ Ресницы']

# Состояния диалога
SERVICE, DATE, TIME, CONTACTS, CONFIRM = range(5)

# Длительность процедур в минутах
SERVICE_DURATIONS = {
    '🧖 Лазерная эпиляция': 30,
    '☀️ Моментальный загар': 30,
    '💅 Маникюр': 90,
    '👣 Педикюр': 90,
    '💄 Визажист': 60,
    '👁️ Ресницы': 60
}

# Время работы студии
WORKING_HOURS = {
    'start': 9,  # 9:00
    'end': 19    # 19:00
}

class BeautySalonBot:
    def __init__(self, token):
        self.token = token
        # Используем HTTPXRequest для лучшей производительности
        self.application = Application.builder().token(token).request(HTTPXRequest()).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        # ConversationHandler для записи
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                SERVICE: [CallbackQueryHandler(self.get_service)],
                DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_date)],
                TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_time)],
                CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_contacts)],
                CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_booking)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # Основные обработчики
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("zapis", self.start))
        self.application.add_handler(CommandHandler("admin", self.admin_stats))
        self.application.add_handler(CommandHandler("menu", self.main_menu))
        self.application.add_handler(CommandHandler("contacts", self.show_contacts))
        self.application.add_handler(CommandHandler("mybookings", self.show_my_bookings))
        self.application.add_handler(CommandHandler("newbooking", self.new_booking))
        
        # Обработчики для кнопок главного меню
        self.application.add_handler(MessageHandler(filters.Regex("^📊 Мои записи$"), self.show_my_bookings))
        self.application.add_handler(MessageHandler(filters.Regex("^ℹ️ О студии$"), self.about_studio))
        self.application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), self.show_contacts))
        self.application.add_handler(MessageHandler(filters.Regex("^🔄 Главное меню$"), self.main_menu))
        self.application.add_handler(MessageHandler(filters.Regex("^💅 Новая запись$"), self.new_booking))
        self.application.add_handler(MessageHandler(filters.Regex("^💅 Записаться на процедуру$"), self.start))
        
        # Обработчик для callback query
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработчик для контактов
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех callback запросов"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Callback received: {query.data}")
        
        if query.data == 'back':
            await self.main_menu_from_query(query)
            return ConversationHandler.END
        
        # Если это callback из ConversationHandler (выбор услуги)
        if context.user_data.get('conversation'):
            await self.get_service(update, context)

    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка контакта из Telegram"""
        if context.user_data.get('conversation') and context.user_data.get('state') == CONTACTS:
            contact = update.message.contact
            if contact:
                phone_number = contact.phone_number
                name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                if name:
                    context.user_data['contacts'] = f"👤 {name} 📱 {phone_number}"
                else:
                    context.user_data['contacts'] = f"📱 {phone_number}"
                
                # Переходим к подтверждению после получения контакта
                confirm_keyboard = [["✅ Да, подтверждаю", "❌ Нет, отменить"]]
                reply_markup = ReplyKeyboardMarkup(confirm_keyboard, resize_keyboard=True)
                
                confirm_text = (
                    f"✅ *ПРОВЕРЬТЕ ДАННЫЕ ЗАПИСИ:*\n\n"
                    f"💅 *Услуга:* {context.user_data['service']}\n"
                    f"📅 *Дата и время:* {context.user_data['date']}\n"
                    f"⏰ *Продолжительность:* {context.user_data['duration']} мин.\n"
                    f"📞 *Контакты:* {context.user_data['contacts']}\n\n"
                    f"Всё верно? Подтверждаете запись?"
                )
                
                await update.message.reply_text(confirm_text, reply_markup=reply_markup, parse_mode='Markdown')
                context.user_data['state'] = CONFIRM
                return CONFIRM

    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню с кнопками"""
        # Выходим из состояния conversation
        context.user_data.clear()
        
        keyboard = [
            ["💅 Записаться на процедуру"],
            ["📊 Мои записи", "ℹ️ О студии"],
            ["📞 Контакты", "🔄 Главное меню"]
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        if update.message:
            await update.message.reply_text(
                "💖 Добро пожаловать в студию красоты!\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.message.reply_text(
                "💖 Добро пожаловать в студию красоты!\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )

    async def send_admin_notification(self, context, booking_data, chat_id, username, contacts):
        """Отправляет уведомления администраторам"""
        service = booking_data['service']
        user_id = booking_data['user_id']
        
        if booking_data.get('username'):
            telegram_link = f"[@{booking_data['username']}](https://t.me/{booking_data['username']})"
        else:
            telegram_link = "Не указан"
        
        notification_text = (
            "🎉 *НОВАЯ ПРЕДВАРИТЕЛЬНАЯ ЗАПИСЬ*\n\n"
            f"👤 *Клиент:* {username or 'Не указано'}\n"
            f"📞 *Контакты:* {contacts or 'Не указаны'}\n"
            f"💅 *Услуга:* {service}\n"
            f"📅 *Дата и время:* {booking_data['date']}\n"
            f"⏰ *Продолжительность:* {booking_data['duration']} мин.\n"
            f"🔢 *Номер записи:* #{booking_data['id']}\n\n"
            f"🔗 *Telegram:* {telegram_link}\n"
            f"🆔 *User ID:* `{user_id}`\n"
            f"💬 *Чат ID:* `{chat_id}`\n\n"
            "⚠️ *Необходимо связаться с клиентом для подтверждения!*"
        )
        
        admin_ids = set()
        
        # Добавляем администраторов в зависимости от услуг
        if service in MANICURE_SERVICES:
            admin_ids.add(ADMIN_MANICURE)
        if service in OTHER_SERVICES:
            admin_ids.add(ADMIN_OTHER)
        
        # Всегда отправляем главному администратору
        admin_ids.add(ADMIN_ALL)
        
        # Отправляем уведомления всем соответствующим администраторам
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"Уведомление отправлено администратору {admin_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления администратору {admin_id}: {e}")

    def get_next_booking_number(self):
        """Генерирует номер записи"""
        try:
            with open('bookings.json', 'r', encoding='utf-8') as f:
                bookings = [json.loads(line) for line in f.readlines()]
            return len(bookings) + 1
        except:
            return 1

    def save_booking(self, booking_data):
        """Сохраняет запись в файл"""
        try:
            with open('bookings.json', 'a', encoding='utf-8') as f:
                json.dump(booking_data, f, ensure_ascii=False)
                f.write('\n')
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения записи: {e}")
            return False

    def get_user_bookings(self, user_id):
        """Возвращает записи пользователя (только актуальные)"""
        try:
            with open('bookings.json', 'r', encoding='utf-8') as f:
                bookings = [json.loads(line) for line in f.readlines()]
            
            # Фильтруем только актуальные записи (не прошедшие)
            current_time = datetime.now()
            user_bookings = []
            
            for booking in bookings:
                if booking.get('user_id') == user_id:
                    # Проверяем, не прошла ли запись
                    try:
                        booking_datetime = datetime.strptime(booking['date'], "%d.%m.%Y %H:%M")
                        if booking_datetime >= current_time:
                            user_bookings.append(booking)
                    except:
                        user_bookings.append(booking)  # Если ошибка формата, все равно показываем
            
            return user_bookings
        except:
            return []

    def is_time_available(self, selected_datetime, duration_minutes):
        """Проверяет доступно ли время для записи"""
        try:
            with open('bookings.json', 'r', encoding='utf-8') as f:
                bookings = [json.loads(line) for line in f.readlines()]
            
            end_datetime = selected_datetime + timedelta(minutes=duration_minutes)
            
            for booking in bookings:
                try:
                    booking_datetime = datetime.strptime(booking['date'], "%d.%m.%Y %H:%M")
                    booking_end = booking_datetime + timedelta(minutes=booking.get('duration', 60))
                    
                    # Проверяем пересечение временных интервалов
                    if (selected_datetime < booking_end and end_datetime > booking_datetime):
                        return False
                except:
                    continue
            
            return True
        except:
            return True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало записи - выбор услуги"""
        context.user_data.clear()
        context.user_data['conversation'] = True
        
        keyboard = [
            [InlineKeyboardButton("🧖 Лазерная эпиляция", callback_data='epilation')],
            [InlineKeyboardButton("☀️ Моментальный загар", callback_data='tanning')],
            [InlineKeyboardButton("💅 Маникюр", callback_data='manicure')],
            [InlineKeyboardButton("👣 Педикюр", callback_data='pedicure')],
            [InlineKeyboardButton("💄 Визажист", callback_data='makeup')],
            [InlineKeyboardButton("👁️ Ресницы", callback_data='lashes')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💅 Выберите услугу для записи:",
            reply_markup=reply_markup
        )
        return SERVICE

    async def get_service(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора услуги"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Обработка услуги: {query.data}")
        
        if query.data == 'back':
            await self.main_menu_from_query(query)
            return ConversationHandler.END
        
        service_map = {
            'epilation': '🧖 Лазерная эпиляция',
            'tanning': '☀️ Моментальный загар',
            'manicure': '💅 Маникюр',
            'pedicure': '👣 Педикюр',
            'makeup': '💄 Визажист',
            'lashes': '👁️ Ресницы'
        }
        
        service_name = service_map.get(query.data)
        if not service_name:
            await query.message.reply_text("Ошибка выбора услуги. Попробуйте снова /start")
            return ConversationHandler.END
        
        context.user_data['service'] = service_name
        context.user_data['duration'] = SERVICE_DURATIONS.get(service_name, 60)
        
        # Получаем текущую дату для кнопок
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        after_tomorrow = today + timedelta(days=2)
        
        date_keyboard = [
            [f"📅 Сегодня ({today.strftime('%d.%m')})", f"📅 Завтра ({tomorrow.strftime('%d.%m')})"],
            [f"📅 Послезавтра ({after_tomorrow.strftime('%d.%m')})", "📅 Другая дата"],
            ["🔙 Назад к услугам"]
        ]
        
        reply_markup = ReplyKeyboardMarkup(date_keyboard, resize_keyboard=True)
        
        await query.message.reply_text(
            f"💅 Вы выбрали: {service_name}\n"
            f"⏰ Продолжительность: {context.user_data['duration']} мин.\n\n"
            "Выберите дату:",
            reply_markup=reply_markup
        )
        return DATE

    async def get_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора даты"""
        try:
            user_input = update.message.text
            
            # Обработка кнопок с датами
            if user_input == "🔙 Назад к услугам":
                await update.message.reply_text("Возвращаемся к выбору услуги...", reply_markup=ReplyKeyboardRemove())
                await self.start(update, context)
                return SERVICE
            
            # Определяем выбранную дату
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            after_tomorrow = today + timedelta(days=2)
            
            selected_date = None
            
            if "Сегодня" in user_input:
                selected_date = today.date()
            elif "Завтра" in user_input:
                selected_date = tomorrow.date()
            elif "Послезавтра" in user_input:
                selected_date = after_tomorrow.date()
            elif "Другая дата" in user_input:
                await update.message.reply_text(
                    "📅 Введите дату в формате ДД.ММ.ГГГГ\n\n"
                    "Пример: 25.12.2024",
                    reply_markup=ReplyKeyboardRemove()
                )
                return DATE
            else:
                # Парсим введенную пользователем дату
                selected_date = parser.parse(user_input, dayfirst=True).date()
            
            # Проверяем что дата не в прошлом
            if selected_date < datetime.now().date():
                await update.message.reply_text(
                    "❌ Нельзя записаться на прошедшую дату.\n"
                    "Пожалуйста, выберите будущую дату:"
                )
                return DATE
            
            context.user_data['selected_date'] = selected_date.isoformat()
            
            # Предлагаем выбрать время
            time_keyboard = [
                ["🕘 09:00", "🕙 10:00", "🕚 11:00"],
                ["🕛 12:00", "🕐 13:00", "🕑 14:00"],
                ["🕒 15:00", "🕓 16:00", "🕔 17:00"],
                ["🕕 18:00", "🕖 19:00", "🕗 Другое время"],
                ["🔙 Назад к выбору дата"]
            ]
            
            reply_markup = ReplyKeyboardMarkup(time_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"📅 Выбрана дата: {selected_date.strftime('%d.%m.%Y')}\n\n"
                "🕐 Выберите удобное время:",
                reply_markup=reply_markup
            )
            return TIME
            
        except Exception as e:
            logger.error(f"Ошибка обработки даты: {e}")
            
            # Восстанавливаем клавиатуру выбора даты
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            after_tomorrow = today + timedelta(days=2)
            
            date_keyboard = [
                [f"📅 Сегодня ({today.strftime('%d.%m')})", f"📅 Завтра ({tomorrow.strftime('%d.%m')})"],
                [f"📅 Послезавтра ({after_tomorrow.strftime('%d.%m')})", "📅 Другая дата"],
                ["🔙 Назад к услугам"]
            ]
            
            reply_markup = ReplyKeyboardMarkup(date_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "❌ Неверный формат даты.\n\n"
                "Пожалуйста, выберите дату из кнопок или введите в формате ДД.ММ.ГГГГ\n\n"
                "Пример: 25.12.2024",
                reply_markup=reply_markup
            )
            return DATE

    async def get_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора времени"""
        try:
            user_input = update.message.text
            
            # Обработка кнопок
            if user_input == "🔙 Назад к выбору даты":
                # Восстанавливаем клавиатуру выбора даты
                today = datetime.now()
                tomorrow = today + timedelta(days=1)
                after_tomorrow = today + timedelta(days=2)
                
                date_keyboard = [
                    [f"📅 Сегодня ({today.strftime('%d.%m')})", f"📅 Завтра ({tomorrow.strftime('%d.%m')})"],
                    [f"📅 Послезавтра ({after_tomorrow.strftime('%d.%m')})", "📅 Другая дата"],
                    ["🔙 Назад к услугам"]
                ]
                
                reply_markup = ReplyKeyboardMarkup(date_keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    "Выберите дату:",
                    reply_markup=reply_markup
                )
                return DATE
            
            selected_date = datetime.fromisoformat(context.user_data['selected_date']).date()
            selected_time = None
            
            if "Другое время" in user_input:
                await update.message.reply_text(
                    "🕐 Введите время в формате ЧЧ:MM\n\n"
                    "Пример: 15:30",
                    reply_markup=ReplyKeyboardRemove()
                )
                return TIME
            
            # Извлекаем время из текста (формат "🕘 09:00")
            if ":" in user_input:
                time_part = user_input.split()[-1]  # Берем последнюю часть с временем
                selected_time = datetime.strptime(time_part, "%H:%M").time()
            else:
                # Парсим введенное пользователем время
                selected_time = datetime.strptime(user_input, "%H:%M").time()
            
            # Проверяем рабочее время
            if selected_time.hour < WORKING_HOURS['start'] or selected_time.hour >= WORKING_HOURS['end']:
                await update.message.reply_text(
                    f"❌ Студия работает с {WORKING_HOURS['start']:02d}:00 до {WORKING_HOURS['end']:02d}:00.\n"
                    "Пожалуйста, выберите время в рабочее время:"
                )
                return TIME
            
            # Сохраняем полную дату и время
            full_datetime = datetime.combine(selected_date, selected_time)
            
            # Проверяем доступность времени
            if not self.is_time_available(full_datetime, context.user_data['duration']):
                await update.message.reply_text(
                    "❌ Это время уже занято. Пожалуйста, выберите другое время:"
                )
                return TIME
            
            context.user_data['date'] = full_datetime.strftime("%d.%m.%Y %H:%M")
            
            # Запрашиваем контакты
            contacts_keyboard = [
                ["📞 Поделиться контактом"],
                ["🔙 Назад к выбору времени"]
            ]
            reply_markup = ReplyKeyboardMarkup(contacts_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "📞 *Как с вами связаться для подтверждения записи?*\n\n"
                "Укажите ваш телефон или другие контакты:\n"
                "• 📱 Номер телефона\n"
                "• 💬 WhatsApp\n"
                "• ✈️ Telegram (@username)\n"
                "• 📧 Email\n\n"
                "Или нажмите '📞 Поделиться контактом'",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            context.user_data['state'] = CONTACTS
            return CONTACTS
            
        except Exception as e:
            logger.error(f"Ошибка обработки времени: {e}")
            
            # Восстанавливаем клавиатуру выбора времени
            time_keyboard = [
                ["🕘 09:00", "🕙 10:00", "🕚 11:00"],
                ["🕛 12:00", "🕐 13:00", "🕑 14:00"],
                ["🕒 15:00", "🕓 16:00", "🕔 17:00"],
                ["🕕 18:00", "🕖 19:00", "🕗 Другое время"],
                ["🔙 Назад к выбору даты"]
            ]
            
            reply_markup = ReplyKeyboardMarkup(time_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "❌ Неверный формат времени.\n\n"
                "Пожалуйста, выберите время из кнопок или введите в формате ЧЧ:MM\n\n"
                "Пример: 15:30",
                reply_markup=reply_markup
            )
            return TIME

    async def get_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода контактов"""
        user_input = update.message.text
        
        if user_input == "🔙 Назад к выбору времени":
            # Восстанавливаем клавиатуру выбора времени
            time_keyboard = [
                ["🕘 09:00", "🕙 10:00", "🕚 11:00"],
                ["🕛 12:00", "🕐 13:00", "🕑 14:00"],
                ["🕒 15:00", "🕓 16:00", "🕔 17:00"],
                ["🕕 18:00", "🕖 19:00", "🕗 Другое время"],
                ["🔙 Назад к выбору даты"]
            ]
            
            reply_markup = ReplyKeyboardMarkup(time_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "🕐 Выберите удобное время:",
                reply_markup=reply_markup
            )
            return TIME
        
        if user_input == "📞 Поделиться контактом":
            # Запрашиваем контакт с специальной кнопкой
            contact_keyboard = [[KeyboardButton("📞 Поделиться контактом", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                "📞 Пожалуйста, нажмите на кнопку ниже, чтобы поделиться контактом:",
                reply_markup=reply_markup
            )
            return CONTACTS
        
        context.user_data['contacts'] = user_input
        
        # Кнопки подтверждения
        confirm_keyboard = [["✅ Да, подтверждаю", "❌ Нет, отменить"]]
        reply_markup = ReplyKeyboardMarkup(confirm_keyboard, resize_keyboard=True)
        
        confirm_text = (
            f"✅ *ПРОВЕРЬТЕ ДАННЫЕ ЗАПИСИ:*\n\n"
            f"💅 *Услуга:* {context.user_data['service']}\n"
            f"📅 *Дата и время:* {context.user_data['date']}\n"
            f"⏰ *Продолжительность:* {context.user_data['duration']} мин.\n"
            f"📞 *Контакты:* {user_input}\n\n"
            f"Всё верно? Подтверждаете запись?"
        )
        
        await update.message.reply_text(confirm_text, reply_markup=reply_markup, parse_mode='Markdown')
        return CONFIRM

    async def confirm_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтверждение записи"""
        user_input = update.message.text
        
        if user_input in ["✅ Да, подтверждаю", "да", "yes", "y", "ок", "подтверждаю"]:
            try:
                user = update.effective_user
                booking_number = self.get_next_booking_number()
                
                booking_data = {
                    'id': booking_number,
                    'service': context.user_data['service'],
                    'date': context.user_data['date'],
                    'duration': context.user_data['duration'],
                    'contacts': context.user_data['contacts'],
                    'timestamp': datetime.now().isoformat(),
                    'chat_id': update.message.chat_id,
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'status': 'pending'
                }
                
                if self.save_booking(booking_data):
                    await self.send_admin_notification(
                        context, booking_data, update.message.chat_id,
                        f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or 'Не указано',
                        context.user_data['contacts']
                    )
                    
                    # Кнопки после успешной записи
                    success_keyboard = [
                        ["💅 Новая запись", "📊 Мои записи"],
                        ["📞 Контакты", "🔄 Главное меню"]
                    ]
                    
                    reply_markup = ReplyKeyboardMarkup(success_keyboard, resize_keyboard=True)
                    
                    await update.message.reply_text(
                        f"🎉 *ПРЕДВАРИТЕЛЬНАЯ ЗАПИСЬ #{booking_number} СОЗДАНА!*\n\n"
                        f"💅 *Услуга:* {context.user_data['service']}\n"
                        f"📅 *Дата:* {context.user_data['date']}\n"
                        f"⏰ *Продолжительность:* {context.user_data['duration']} мин.\n"
                        f"📞 *Контакты:* {context.user_data['contacts']}\n\n"
                        "⚠️ *Это предварительная запись!*\n"
                        "Администратор свяжется с вами в ближайшее время для подтверждения.\n\n"
                        "Спасибо за доверие! 💖",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    
                    logger.info(f"Создана новая запись #{booking_number}")
                else:
                    await update.message.reply_text("❌ Произошла ошибка при сохранении записи. Попробуйте позже.")
                
            except Exception as e:
                logger.error(f"Ошибка при создании записи: {e}")
                await update.message.reply_text("❌ Произошла ошибка при создании записи. Попробуйте позже.")
        else:
            # Отмена записи
            await self.main_menu(update, context)
        
        return ConversationHandler.END

    async def show_my_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает записи пользователя (только актуальные)"""
        user_id = update.effective_user.id
        bookings = self.get_user_bookings(user_id)
        
        if not bookings:
            await update.message.reply_text(
                "📋 У вас пока нет актуальных записей.\n\n"
                "Хотите записаться на процедуру?",
                reply_markup=ReplyKeyboardMarkup([["💅 Записаться на процедуру"], ["🔄 Главное меню"]], resize_keyboard=True)
            )
            return
        
        bookings_text = "📋 *ВАШИ АКТУАЛЬНЫЕ ЗАПИСИ:*\n\n"
        for i, booking in enumerate(bookings, 1):
            status_emoji = "✅" if booking.get('status') == 'confirmed' else "⏳"
            status_text = "Подтверждена" if booking.get('status') == 'confirmed' else "Ожидает подтверждения"
            bookings_text += (
                f"{i}. {status_emoji} *{booking['service']}*\n"
                f"   📅 {booking['date']}\n"
                f"   🔢 №{booking['id']}\n"
                f"   📞 {booking.get('contacts', 'Контакты не указаны')}\n"
                f"   🏷️ Статус: {status_text}\n\n"
            )
        
        await update.message.reply_text(bookings_text, parse_mode='Markdown')

    async def show_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает контакты студии"""
        # Экранируем специальные символы Markdown
        phone = STUDIO_CONTACTS['phone'].replace('(', '\\(').replace(')', '\\)').replace('+', '\\+')
        instagram = STUDIO_CONTACTS['instagram'].replace('@', '\\@')
        address = STUDIO_CONTACTS['address'].replace('.', '\\.').replace('-', '\\-')
        hours = STUDIO_CONTACTS['hours'].replace(':', '\\:')
        
        contacts_text = (
            "📞 *КОНТАКТЫ СТУДИИ КРАСОТЫ*\n\n"
            f"📱 *Телефон:* {phone}\n"
            f"📸 *Instagram:* {instagram}\n"
            f"🏠 *Адрес:* {address}\n"
            f"🕐 *Часы работы:* {hours}\n\n"
            "📍 *Мы ждем вас в гости!*"
        )
        
        try:
            await update.message.reply_text(contacts_text, parse_mode='Markdown')
        except BadRequest as e:
            # Если все равно возникает ошибка, отправляем без Markdown
            logger.warning(f"Markdown parsing error, sending without formatting: {e}")
            contacts_text_plain = (
                "📞 КОНТАКТЫ СТУДИИ КРАСОТЫ\n\n"
                f"📱 Телефон: {STUDIO_CONTACTS['phone']}\n"
                f"📸 Instagram: {STUDIO_CONTACTS['instagram']}\n"
                f"🏠 Адрес: {STUDIO_CONTACTS['address']}\n"
                f"🕐 Часы работы: {STUDIO_CONTACTS['hours']}\n\n"
                "📍 Мы ждем вас в гости!"
            )
            await update.message.reply_text(contacts_text_plain)

    async def about_studio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о студии"""
        about_text = (
            "💖 *О НАШЕЙ СТУДИИ*\n\n"
            "Мы - современная студия красоты, где работают настоящие профессионалы!\n\n"
            "✨ *Наши услуги:*\n"
            "• 🧖 Лазерная эпиляция\n"
            "• ☀️ Моментальный загар\n"
            "• 💅 Маникюр и педикюр\n"
            "• 💄 Визажист\n"
            "• 👁️ Наращивание ресниц\n\n"
            "🏆 *Наши преимущества:*\n"
            "• Профессиональное оборудование\n"
            "• Качественные материалы\n"
            "• Индивидуальный подход\n"
            "• Уютная атмосфера\n\n"
            "*Ждем вас в нашей студии!* 💫"
        )
        await update.message.reply_text(about_text, parse_mode='Markdown')

    async def new_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Новая запись"""
        await self.start(update, context)

    async def main_menu_from_query(self, query):
        """Главное меню из callback query"""
        keyboard = [
            ["💅 Записаться на процедуру"],
            ["📊 Мои записи", "ℹ️ О студии"],
            ["📞 Контакты", "🔄 Главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await query.message.reply_text("💖 Главное меню:", reply_markup=reply_markup)

    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика для администраторов"""
        if update.effective_user.id not in [ADMIN_ALL, ADMIN_MANICURE, ADMIN_OTHER]:
            await update.message.reply_text("❌ Доступ запрещен")
            return
        
        try:
            with open('bookings.json', 'r', encoding='utf-8') as f:
                bookings = [json.loads(line) for line in f.readlines()]
            total = len(bookings)
            
            # Подсчет актуальных записей
            current_time = datetime.now()
            active_bookings = 0
            for booking in bookings:
                try:
                    booking_datetime = datetime.strptime(booking['date'], "%d.%m.%Y %H:%M")
                    if booking_datetime >= current_time:
                        active_bookings += 1
                except:
                    continue
            
            stats_text = (
                f"📊 *СТАТИСТИКА СИСТЕМЫ:*\n\n"
                f"• Всего записей: {total}\n"
                f"• Актуальных записей: {active_bookings}\n"
                f"• Прошедших записей: {total - active_bookings}"
            )
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
        except:
            await update.message.reply_text("📊 Записей пока нет")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена записи"""
        await self.main_menu(update, context)
        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи"""
        help_text = (
            "🤖 *КОМАНДЫ БОТА:*\n\n"
            "💅 /start - начать запись\n"
            "📊 /mybookings - мои записи\n"
            "📞 /contacts - контакты студии\n"
            "🏠 /menu - главное меню\n"
            "ℹ️ /help - справка\n\n"
            "Используйте кнопки меню для навигации! 🚀"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус записей"""
        try:
            with open('bookings.json', 'r', encoding='utf-8') as f:
                bookings = [json.loads(line) for line in f.readlines()]
            
            current_time = datetime.now()
            active_bookings = 0
            for booking in bookings:
                try:
                    booking_datetime = datetime.strptime(booking['date'], "%d.%m.%Y %H:%M")
                    if booking_datetime >= current_time:
                        active_bookings += 1
                except:
                    continue
            
            status_text = (
                f"📊 *СТАТУС СИСТЕМЫ:*\n\n"
                f"• Всего записей: {len(bookings)}\n"
                f"• Актуальных записей: {active_bookings}\n"
                f"• Система работает нормально ✅"
            )
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
        except:
            await update.message.reply_text("📊 Записей пока нет\n✅ Система работает нормально")

    def run(self):
        logger.info("Бот запущен!")
        self.application.run_polling()

if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("Не установлен BOT_TOKEN!")
        print("ERROR: Не установлен BOT_TOKEN!")
        print("Установите переменную: export BOT_TOKEN='ваш_токен'")
        exit(1)
    
    # Создаем файл для записей если его нет
    if not os.path.exists('bookings.json'):
        with open('bookings.json', 'w', encoding='utf-8') as f:
            f.write('')
    
    bot = BeautySalonBot(token)
    bot.run()

