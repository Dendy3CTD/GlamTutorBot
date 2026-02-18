import os
import logging
import telebot
from telebot import types

# Включить логирование для отладки
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен из переменной окружения или из кода (для разработки)
BOT_TOKEN = os.environ.get('GLAMTUTOR_BOT_TOKEN') or '8397040934:AAHA_1loP9-XQnyfobIfy7VW_TX1dRD1myM'
bot = telebot.TeleBot(BOT_TOKEN)

# База данных товаров с фото (можно использовать URL или file_id)
products = {
    '001': {
        'name': 'Тональный крем',
        'price': 100,
        'description': 'Качественный тональный крем для идеального тона кожи',
        'photo': 'https://via.placeholder.com/400x400/FFB6C1/000000?text=Тональный+крем'  # Замените на реальные фото
    },
    '002': {
        'name': 'Консилер',
        'price': 200,
        'description': 'Профессиональный консилер для маскировки недостатков',
        'photo': 'https://via.placeholder.com/400x400/FFB6C1/000000?text=Консилер'
    },
    '003': {
        'name': 'Пудра',
        'price': 500,
        'description': 'Матирующая пудра для фиксации макияжа',
        'photo': 'https://via.placeholder.com/400x400/FFB6C1/000000?text=Пудра'
    },
    '004': {
        'name': 'Румяна',
        'price': 57,
        'description': 'Натуральные румяна для здорового румянца',
        'photo': 'https://via.placeholder.com/400x400/FFB6C1/000000?text=Румяна'
    },
    '005': {
        'name': 'Хайлайтер',
        'price': 1800,
        'description': 'Премиум хайлайтер для сияния кожи',
        'photo': 'https://via.placeholder.com/400x400/FFB6C1/000000?text=Хайлайтер'
    },
    '006': {
        'name': 'Помада',
        'price': 800,
        'description': 'Стойкая помада насыщенного цвета',
        'photo': 'https://via.placeholder.com/400x400/FFB6C1/000000?text=Помада'
    }
}

# Упорядоченный список артикулов для навигации по каталогу
product_skus = list(products.keys())

# Контакты и информация продавца
seller_contact = '@R_ig_hk'
seller_phone = '+7 988-742-28-16'
seller_address = 'пр. Мира 8'
seller_work_hours = 'Пн–Вс: 10:00 – 20:00'
# Ссылка на карты (Яндекс или Google). Оставьте пустым, если не нужна кнопка
seller_map_link = 'https://yandex.ru/maps/?text=пр. Мира 8'

# Хранение данных заказа (в реальном проекте лучше использовать БД)
user_orders = {}

# Меню: только Каталог, Заказать, Настройки
menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
catalog_btn = types.KeyboardButton('🛍️ Каталог товаров')
order_btn = types.KeyboardButton('📦 Заказать')
settings_btn = types.KeyboardButton('⚙️ Настройки')
menu.add(catalog_btn, order_btn, settings_btn)

back = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_button = types.KeyboardButton('⬅️ Назад')
back.add(back_button)


def check_bot_token():
    """Проверка токена при запуске."""
    try:
        me = bot.get_me()
        logger.info(f"Бот запущен: @{me.username} (id={me.id})")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к Telegram: {e}")
        logger.error("Проверьте токен бота в @BotFather и что бот не заблокирован.")
        return False


@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        welcome_text = (
            "Добро пожаловать в GlamTutorBot! 🎨\n\n"
            "Здесь вы можете:\n"
            "• Просмотреть каталог товаров\n"
            "• Оформить заказ\n"
            "• Настроить параметры\n\n"
            "Выберите интересующий раздел:"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=menu)
    except Exception as e:
        logger.exception("Ошибка в start_message: %s", e)


@bot.message_handler(commands=['help'])
def help_message(message):
    try:
        bot.send_message(
            message.chat.id,
            "Используйте кнопки меню:\n"
            "🛍️ Каталог товаров - просмотр товаров с фото\n"
            "📦 Заказать - оформление заказа\n"
            "⚙️ Настройки - контакты и адрес",
            reply_markup=menu
        )
    except Exception as e:
        logger.exception("Ошибка в help_message: %s", e)


@bot.message_handler(content_types=['text'])
def text_message(message):
    if not message.text:
        return
    
    if message.text == "⬅️ Назад" or message.text == "Назад":
        bot.send_message(message.chat.id, 'Главное меню:', reply_markup=menu)
    
    elif message.text == '🛍️ Каталог товаров' or message.text == 'Каталог товаров':
        show_catalog_feed(message)
    
    elif message.text == '📦 Заказать' or message.text == 'Заказать':
        start_order_process(message)
    
    elif message.text == '⚙️ Настройки' or message.text == 'Настройки':
        show_settings(message)
    
    else:
        # Если пользователь в процессе заказа, обрабатываем как данные
        if message.chat.id in user_orders:
            process_order_data(message)
        else:
            try:
                bot.send_message(
                    message.chat.id,
                    "Используйте кнопки меню ниже или нажмите /start для главного меню.",
                    reply_markup=menu
                )
            except Exception as e:
                logger.exception("Ошибка отправки сообщения: %s", e)


def _catalog_caption_and_keyboard(index):
    """Формирует подпись и клавиатуру для товара по индексу в каталоге."""
    sku = product_skus[index]
    product = products[sku]
    total = len(product_skus)
    caption = (
        f"🛍️ Каталог — {index + 1}/{total}\n\n"
        f"📦 <b>{product['name']}</b>\n\n"
        f"💰 Цена: <b>{product['price']}$</b>\n"
        f"🔢 Артикул: <code>{sku}</code>\n\n"
        f"📝 {product['description']}"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    # Навигация: ⬅️ Назад | N/M | Вперёд ➡️
    row1 = []
    if index > 0:
        row1.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"catalog_{index - 1}"))
    row1.append(types.InlineKeyboardButton(text=f"{index + 1}/{total}", callback_data="catalog_noop"))
    if index < total - 1:
        row1.append(types.InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"catalog_{index + 1}"))
    keyboard.add(*row1)
    keyboard.add(
        types.InlineKeyboardButton(text="📦 Заказать", callback_data=f"order_from_catalog_{sku}"),
        types.InlineKeyboardButton(text="💬 Написать продавцу", url=f"https://t.me/{seller_contact.replace('@', '')}")
    )
    return caption, keyboard


def show_catalog_feed(message):
    """Показать каталог: один товар с кнопками переключения."""
    try:
        index = 0
        sku = product_skus[index]
        product = products[sku]
        caption, keyboard = _catalog_caption_and_keyboard(index)
        bot.send_message(message.chat.id, "🛍️ Каталог товаров. Переключайте товары кнопками:", reply_markup=back)
        try:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=product['photo'],
                caption=caption,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.warning("Ошибка отправки фото каталога: %s", e)
            bot.send_message(message.chat.id, caption, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logger.exception("Ошибка в show_catalog_feed: %s", e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('catalog_'))
def catalog_nav_callback(call):
    """Переключение по товарам в каталоге (Назад / Вперёд)."""
    if call.data == "catalog_noop":
        bot.answer_callback_query(call.id)
        return
    try:
        idx = int(call.data.split('_')[1])
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id)
        return
    if idx < 0 or idx >= len(product_skus):
        bot.answer_callback_query(call.id)
        return
    sku = product_skus[idx]
    product = products[sku]
    caption, keyboard = _catalog_caption_and_keyboard(idx)
    try:
        media = types.InputMediaPhoto(product['photo'], caption=caption, parse_mode='HTML')
        bot.edit_message_media(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            media=media,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.warning("edit_message_media (catalog): %s", e)
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e2:
            logger.warning("edit_message_caption: %s", e2)
            bot.send_message(call.message.chat.id, caption, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


def show_settings(message):
    """Главный экран настроек с выбором раздела."""
    try:
        text = (
            "⚙️ <b>Настройки</b>\n\n"
            "Выберите раздел:"
        )
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("📞 Контакты", callback_data="settings_contacts"))
        keyboard.add(types.InlineKeyboardButton("📍 Адрес", callback_data="settings_address"))
        keyboard.add(types.InlineKeyboardButton("🕐 Режим работы", callback_data="settings_hours"))
        keyboard.add(types.InlineKeyboardButton("⬅️ В главное меню", callback_data="settings_back"))
        bot.send_message(
            message.chat.id,
            text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.exception("Ошибка в show_settings: %s", e)


def _settings_back_keyboard():
    """Кнопка «В настройки» для подразделов."""
    return types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu")
    )


@bot.callback_query_handler(func=lambda c: c.data == "settings_contacts")
def settings_contacts_callback(call):
    """Раздел Контакты: телефон, Telegram, кнопки связи."""
    text = (
        "📞 <b>Контакты</b>\n\n"
        f"Телефон: <code>{seller_phone}</code>\n"
        f"Telegram: {seller_contact}"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(
        "💬 Написать продавцу",
        url=f"https://t.me/{seller_contact.replace('@', '')}"
    ))
    keyboard.add(types.InlineKeyboardButton(
        "📞 Позвонить",
        url=f"tel:{seller_phone.replace(' ', '').replace('-', '')}"
    ))
    keyboard.add(types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu"))
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.warning("edit_settings_contacts: %s", e)
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_address")
def settings_address_callback(call):
    """Раздел Адрес: адрес и кнопка карты."""
    text = f"📍 <b>Адрес</b>\n\n{seller_address}"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if seller_map_link:
        keyboard.add(types.InlineKeyboardButton("🗺 Открыть в картах", url=seller_map_link))
    keyboard.add(types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu"))
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.warning("edit_settings_address: %s", e)
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_hours")
def settings_hours_callback(call):
    """Раздел Режим работы."""
    text = f"🕐 <b>Режим работы</b>\n\n{seller_work_hours}"
    keyboard = _settings_back_keyboard()
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.warning("edit_settings_hours: %s", e)
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_menu")
def settings_menu_callback(call):
    """Возврат в меню настроек (из подраздела)."""
    text = "⚙️ <b>Настройки</b>\n\nВыберите раздел:"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("📞 Контакты", callback_data="settings_contacts"))
    keyboard.add(types.InlineKeyboardButton("📍 Адрес", callback_data="settings_address"))
    keyboard.add(types.InlineKeyboardButton("🕐 Режим работы", callback_data="settings_hours"))
    keyboard.add(types.InlineKeyboardButton("⬅️ В главное меню", callback_data="settings_back"))
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.warning("edit_settings_menu: %s", e)
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_back")
def settings_back_callback(call):
    """Возврат в главное меню из настроек."""
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    bot.send_message(
        call.message.chat.id,
        "Главное меню:",
        reply_markup=menu
    )
    bot.answer_callback_query(call.id)


def start_order_process(message):
    """Начало процесса заказа"""
    try:
        # Показываем каталог для выбора товара
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for sku, product in products.items():
            button_text = f"{product['name']} - {product['price']}$"
            buttons.append(types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_product_{sku}"
            ))
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                keyboard.add(buttons[i], buttons[i + 1])
            else:
                keyboard.add(buttons[i])
        
        bot.send_message(
            message.chat.id,
            "📦 <b>Оформление заказа</b>\n\nВыберите товар из каталога:",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.exception("Ошибка в start_order_process: %s", e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_product_'))
def select_product_callback(call):
    """Выбор товара для заказа"""
    try:
        sku = call.data.split('_')[2]
        if sku in products:
            product = products[sku]
            user_orders[call.message.chat.id] = {'sku': sku, 'step': 'name'}
            
            bot.send_message(
                call.message.chat.id,
                f"✅ Выбран товар: <b>{product['name']}</b>\n💰 Цена: <b>{product['price']}$</b>\n\n"
                "Для оформления заказа мне нужна следующая информация:\n\n"
                "📝 <b>Шаг 1/3:</b> Введите ваше имя:",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            bot.answer_callback_query(call.id, f"Выбран: {product['name']}")
        else:
            bot.answer_callback_query(call.id, "Товар не найден")
    except Exception as e:
        logger.exception("Ошибка в select_product_callback: %s", e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('order_from_catalog_'))
def order_from_catalog_callback(call):
    """Заказ напрямую из каталога"""
    try:
        sku = call.data.split('_')[3]
        if sku in products:
            product = products[sku]
            user_orders[call.message.chat.id] = {'sku': sku, 'step': 'name'}
            
            bot.send_message(
                call.message.chat.id,
                f"✅ Выбран товар: <b>{product['name']}</b>\n💰 Цена: <b>{product['price']}$</b>\n\n"
                "Для оформления заказа мне нужна следующая информация:\n\n"
                "📝 <b>Шаг 1/3:</b> Введите ваше имя:",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            bot.answer_callback_query(call.id, f"Выбран: {product['name']}")
        else:
            bot.answer_callback_query(call.id, "Товар не найден")
    except Exception as e:
        logger.exception("Ошибка в order_from_catalog_callback: %s", e)


def process_order_data(message):
    """Обработка данных заказа пошагово"""
    try:
        if message.chat.id not in user_orders:
            return
        
        order = user_orders[message.chat.id]
        step = order.get('step')
        
        if step == 'name':
            order['name'] = message.text
            order['step'] = 'phone'
            bot.send_message(
                message.chat.id,
                f"✅ Имя: <b>{message.text}</b>\n\n"
                "📞 <b>Шаг 2/3:</b> Введите ваш номер телефона:",
                parse_mode='HTML'
            )
        
        elif step == 'phone':
            order['phone'] = message.text
            order['step'] = 'address'
            bot.send_message(
                message.chat.id,
                f"✅ Телефон: <b>{message.text}</b>\n\n"
                "📍 <b>Шаг 3/3:</b> Введите адрес доставки:",
                parse_mode='HTML'
            )
        
        elif step == 'address':
            order['address'] = message.text
            order['step'] = 'complete'
            
            # Формируем итоговый заказ
            product = products[order['sku']]
            order_text = (
                f"✅ <b>Заказ оформлен!</b>\n\n"
                f"📦 <b>Товар:</b> {product['name']}\n"
                f"🔢 <b>Артикул:</b> <code>{order['sku']}</code>\n"
                f"💰 <b>Цена:</b> {product['price']}$\n\n"
                f"👤 <b>Имя:</b> {order['name']}\n"
                f"📞 <b>Телефон:</b> {order['phone']}\n"
                f"📍 <b>Адрес:</b> {order['address']}\n\n"
                f"Нажмите кнопку ниже, чтобы написать продавцу и подтвердить заказ:"
            )
            
            keyboard = types.InlineKeyboardMarkup()
            contact_btn = types.InlineKeyboardButton(
                text="💬 Написать продавцу",
                url=f"https://t.me/{seller_contact.replace('@', '')}"
            )
            keyboard.add(contact_btn)
            
            bot.send_message(
                message.chat.id,
                order_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            # Отправляем заказ продавцу (если есть канал/чат)
            try:
                order_for_seller = (
                    f"🆕 <b>Новый заказ!</b>\n\n"
                    f"📦 Товар: {product['name']} (Артикул: {order['sku']})\n"
                    f"💰 Цена: {product['price']}$\n\n"
                    f"👤 Имя: {order['name']}\n"
                    f"📞 Телефон: {order['phone']}\n"
                    f"📍 Адрес: {order['address']}\n\n"
                    f"ID пользователя: {message.chat.id}"
                )
                # Раскомментируйте, если есть канал для заказов:
                # bot.send_message(chat_id='@So_it_will_go', text=order_for_seller, parse_mode='HTML')
            except Exception as e:
                logger.warning(f"Не удалось отправить заказ продавцу: {e}")
            
            # Очищаем данные заказа
            del user_orders[message.chat.id]
            
            # Возвращаем меню
            bot.send_message(
                message.chat.id,
                "Спасибо за заказ! Меню:",
                reply_markup=menu
            )
    
    except Exception as e:
        logger.exception("Ошибка в process_order_data: %s", e)
        if message.chat.id in user_orders:
            del user_orders[message.chat.id]
        bot.send_message(
            message.chat.id,
            "Произошла ошибка. Попробуйте оформить заказ заново.",
            reply_markup=menu
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith('order_'))
def order_callback(call):
    """Обработка заказа товара (старая функция для совместимости)"""
    try:
        sku = call.data.split('_')[1]
        if sku in products:
            product = products[sku]
            user_orders[call.message.chat.id] = {'sku': sku, 'step': 'name'}
            
            bot.send_message(
                call.message.chat.id,
                f"✅ Выбран товар: <b>{product['name']}</b>\n💰 Цена: <b>{product['price']}$</b>\n\n"
                "Для оформления заказа мне нужна следующая информация:\n\n"
                "📝 <b>Шаг 1/3:</b> Введите ваше имя:",
                parse_mode='HTML',
                reply_markup=types.ReplyKeyboardRemove()
            )
            bot.answer_callback_query(call.id, f"Выбран: {product['name']}")
        else:
            bot.answer_callback_query(call.id, "Товар не найден")
    except Exception as e:
        logger.exception("Ошибка в order_callback: %s", e)


if __name__ == '__main__':
    if not check_bot_token():
        print("Не удалось подключиться к Telegram. Проверьте токен и интернет.")
        exit(1)
    try:
        # skip_pending=True — не обрабатывать старые сообщения после перезапуска
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.exception("Бот остановился с ошибкой: %s", e)
        exit(1)
