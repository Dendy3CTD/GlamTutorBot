import os
import logging
from datetime import datetime
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
# Настройки пользователя: город, пол, псевдоним, комментарии
user_settings = {}
user_settings_state = {}  # chat_id -> 'city' | 'nickname' | 'comment' | 'feedback'

# Прошлые заказы (chat_id -> список заказов)
completed_orders = {}

# Обратная связь: список сообщений для админки (chat_id, text, date, username)
feedback_list = []

# Админ-панель: ID пользователей Telegram. Узнать свой ID: напишите боту @userinfobot в Telegram
_admin_ids = os.environ.get('ADMIN_IDS', '').strip()
ADMIN_IDS = [int(x.strip()) for x in _admin_ids.split(',') if x.strip()]
# Если переменная ADMIN_IDS не задана — укажите ID здесь:
if not ADMIN_IDS:
    ADMIN_IDS = [1290112937]  # @So_it_will_go

# Состояние админа при добавлении товара / ответе на обратную связь
admin_state = {}

# Список городов для выбора
CITIES = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 'Другой']

# Главное меню: Начать, Настройки аккаунта, Прошлые заказы, Обратная связь
menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(
    types.KeyboardButton('🟢 Начать'),
    types.KeyboardButton('⚙️ Настройки аккаунта')
)
menu.add(
    types.KeyboardButton('📦 Прошлые заказы'),
    types.KeyboardButton('💬 Обратная связь')
)

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
    """Приветствие с inline-кнопками (как в примере) и основное меню."""
    try:
        welcome_text = (
            "👋 Добро пожаловать в <b>GlamTutorBot</b>!\n\n"
            "Здесь вы можете просмотреть каталог, оформить заказ или связаться с нами.\n\n"
            "Выберите действие:"
        )
        start_keyboard = types.InlineKeyboardMarkup(row_width=2)
        start_keyboard.add(
            types.InlineKeyboardButton("🛍️ Каталог", callback_data="start_catalog"),
            types.InlineKeyboardButton("📞 Контакты", callback_data="start_contacts"),
            types.InlineKeyboardButton("⚙️ Настройки", callback_data="start_settings")
        )
        bot.send_message(
            message.chat.id,
            welcome_text,
            parse_mode='HTML',
            reply_markup=start_keyboard
        )
        bot.send_message(message.chat.id, "Или выберите пункт меню ниже:", reply_markup=menu)
    except Exception as e:
        logger.exception("Ошибка в start_message: %s", e)


def _fake_message(chat_id):
    """Вспомогательный объект с полем chat.id для вызова функций, ожидающих message."""
    m = lambda: None
    m.chat = lambda: None
    m.chat.id = chat_id
    m.text = ''
    return m


@bot.callback_query_handler(func=lambda c: c.data == "start_catalog")
def start_catalog_callback(call):
    """Старт: переход в каталог."""
    bot.answer_callback_query(call.id)
    show_catalog_feed(_fake_message(call.message.chat.id))


@bot.callback_query_handler(func=lambda c: c.data == "start_contacts")
def start_contacts_callback(call):
    """Старт: показать контакты сразу."""
    bot.answer_callback_query(call.id)
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
    try:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logger.warning("start_contacts: %s", e)


@bot.callback_query_handler(func=lambda c: c.data == "start_settings")
def start_settings_callback(call):
    """Старт: переход в настройки."""
    bot.answer_callback_query(call.id)
    show_settings(_fake_message(call.message.chat.id))


@bot.message_handler(commands=['help'])
def help_message(message):
    try:
        bot.send_message(
            message.chat.id,
            "Меню:\n"
            "🟢 Начать — каталог и приветствие\n"
            "⚙️ Настройки аккаунта — контакты, город, карты и др.\n"
            "📦 Прошлые заказы — история заказов\n"
            "💬 Обратная связь — написать или оставить отзыв",
            reply_markup=menu
        )
    except Exception as e:
        logger.exception("Ошибка в help_message: %s", e)


def is_admin(user_id):
    return user_id in ADMIN_IDS


@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Админ-панель: только для пользователей из ADMIN_IDS."""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "Доступ запрещён.")
        return
    text = "🔐 <b>Админ-панель</b>\n\nВыберите действие:"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Добавить товар", callback_data="admin_add_product"))
    keyboard.add(types.InlineKeyboardButton("💬 Обратная связь (ответы)", callback_data="admin_feedback_list"))
    keyboard.add(types.InlineKeyboardButton("❌ Выход из админки", callback_data="admin_exit"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == "admin_exit")
def admin_exit_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id)
        return
    if call.message.chat.id in admin_state:
        del admin_state[call.message.chat.id]
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выход из админ-панели.")
    except Exception:
        pass
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "admin_add_product")
def admin_add_product_start(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id)
        return
    admin_state[call.message.chat.id] = {'step': 'add_name', 'data': {}}
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="➕ <b>Добавление товара</b>\n\nШаг 1/4. Введите <b>название</b> товара:",
            parse_mode='HTML'
        )
    except Exception:
        bot.send_message(call.message.chat.id, "➕ Добавление товара\n\nШаг 1/4. Введите название товара:")
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "admin_feedback_list")
def admin_feedback_list_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id)
        return
    if not feedback_list:
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="💬 Обратная связь пуста."
            )
        except Exception:
            bot.send_message(call.message.chat.id, "💬 Обратная связь пуста.")
        bot.answer_callback_query(call.id)
        return
    text = "💬 <b>Обратная связь</b>\n\nВыберите, кому ответить:"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for i, fb in enumerate(feedback_list[-20:]):  # последние 20
        short = (fb['text'][:40] + '…') if len(fb['text']) > 40 else fb['text']
        keyboard.add(types.InlineKeyboardButton(
            f"#{i+1} {fb['date']} | @{fb['username']}: {short}",
            callback_data=f"admin_reply_{i}"
        ))
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back"))
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("admin_reply_"))
def admin_reply_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id)
        return
    try:
        idx = int(call.data.replace("admin_reply_", ""))
    except ValueError:
        bot.answer_callback_query(call.id)
        return
    recent = feedback_list[-20:]
    if idx < 0 or idx >= len(recent):
        bot.answer_callback_query(call.id, "Не найден")
        return
    fb = recent[idx]
    admin_state[call.message.chat.id] = {'step': 'reply_feedback', 'target_chat_id': fb['chat_id'], 'username': fb['username']}
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✏️ Ответ пользователю (@{fb['username']}). Напишите текст ответа в чат:"
        )
    except Exception:
        bot.send_message(call.message.chat.id, f"✏️ Ответ пользователю (@{fb['username']}). Напишите текст ответа в чат:")
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "admin_back")
def admin_back_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id)
        return
    text = "🔐 <b>Админ-панель</b>\n\nВыберите действие:"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("➕ Добавить товар", callback_data="admin_add_product"))
    keyboard.add(types.InlineKeyboardButton("💬 Обратная связь (ответы)", callback_data="admin_feedback_list"))
    keyboard.add(types.InlineKeyboardButton("❌ Выход из админки", callback_data="admin_exit"))
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


def process_admin_input(message):
    """Обработка ввода админа: добавление товара или ответ на обратную связь."""
    cid = message.chat.id
    if cid not in admin_state:
        return False
    state = admin_state[cid]
    step = state.get('step')
    data = state.get('data', {})
    text = (message.text or '').strip()

    if step == 'reply_feedback':
        target = state.get('target_chat_id')
        try:
            bot.send_message(target, f"📩 <b>Ответ от поддержки:</b>\n\n{text}", parse_mode='HTML')
            bot.send_message(cid, "✅ Ответ отправлен.")
        except Exception as e:
            bot.send_message(cid, f"Ошибка отправки: {e}")
        del admin_state[cid]
        return True

    if step == 'add_name':
        state['data']['name'] = text or 'Товар'
        state['step'] = 'add_price'
        bot.send_message(cid, "Шаг 2/4. Введите <b>цену</b> (число):", parse_mode='HTML')
        return True
    if step == 'add_price':
        try:
            price = int(text.replace(' ', ''))
        except ValueError:
            bot.send_message(cid, "Введите число для цены.")
            return True
        state['data']['price'] = price
        state['step'] = 'add_description'
        bot.send_message(cid, "Шаг 3/4. Введите <b>описание</b> товара:", parse_mode='HTML')
        return True
    if step == 'add_description':
        state['data']['description'] = text or 'Без описания'
        state['step'] = 'add_photo'
        bot.send_message(cid, "Шаг 4/4. Отправьте <b>URL фото</b> или напишите <code>пропустить</code> для заглушки.", parse_mode='HTML')
        return True
    if step == 'add_photo':
        photo = text if text and text.lower() != 'пропустить' else f"https://via.placeholder.com/400x400/FFB6C1/000000?text=Товар"
        state['data']['photo'] = photo
        # Сохраняем товар
        new_sku = f"{len(products) + 1:03d}"
        while new_sku in products:
            new_sku = f"{int(new_sku) + 1:03d}"
        products[new_sku] = {
            'name': state['data']['name'],
            'price': state['data']['price'],
            'description': state['data']['description'],
            'photo': state['data']['photo']
        }
        product_skus.append(new_sku)
        del admin_state[cid]
        bot.send_message(cid, f"✅ Товар добавлен! Артикул: <code>{new_sku}</code>", parse_mode='HTML')
        return True
    return False


@bot.message_handler(content_types=['photo'])
def admin_photo_handler(message):
    """При добавлении товара админ может отправить фото — используем file_id."""
    if not is_admin(message.from_user.id) or message.chat.id not in admin_state:
        return
    state = admin_state[message.chat.id]
    if state.get('step') != 'add_photo':
        return
    # Берём самое большое фото (последнее в списке)
    photo = message.photo[-1]
    state['data']['photo'] = photo.file_id
    data = state['data']
    new_sku = f"{len(products) + 1:03d}"
    while new_sku in products:
        new_sku = f"{int(new_sku) + 1:03d}"
    products[new_sku] = {
        'name': data['name'],
        'price': data['price'],
        'description': data['description'],
        'photo': data['photo']
    }
    product_skus.append(new_sku)
    del admin_state[message.chat.id]
    bot.send_message(message.chat.id, f"✅ Товар добавлен с фото! Артикул: <code>{new_sku}</code>", parse_mode='HTML')


@bot.message_handler(content_types=['text'])
def text_message(message):
    if not message.text:
        return
    # Ввод админа (добавление товара, ответ на обратную связь)
    if is_admin(message.from_user.id) and message.chat.id in admin_state:
        if process_admin_input(message):
            return

    if message.text == "⬅️ Назад" or message.text == "Назад":
        bot.send_message(message.chat.id, 'Главное меню:', reply_markup=menu)
    
    elif message.text == '🟢 Начать' or message.text == 'Начать':
        start_message(message)
    
    elif message.text == '⚙️ Настройки аккаунта' or message.text == 'Настройки аккаунта':
        show_settings(message)
    
    elif message.text == '📦 Прошлые заказы' or message.text == 'Прошлые заказы':
        show_past_orders(message)
    
    elif message.text == '💬 Обратная связь' or message.text == 'Обратная связь':
        show_feedback(message)
    
    else:
        # Режим ввода настроек (город, псевдоним, комментарий)
        if message.chat.id in user_settings_state:
            process_settings_input(message)
            return
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


def _ensure_user_settings(chat_id):
    if chat_id not in user_settings:
        user_settings[chat_id] = {'city': '', 'gender': '', 'nickname': '', 'comment': ''}
    return user_settings[chat_id]


def process_settings_input(message):
    """Обработка ввода города, псевдонима, комментария."""
    cid = message.chat.id
    if cid not in user_settings_state:
        return
    state = user_settings_state.pop(cid)
    _ensure_user_settings(cid)
    text = message.text.strip() if message.text else ''
    if state == 'nickname':
        user_settings[cid]['nickname'] = text or '—'
        bot.send_message(cid, f"✅ Псевдоним сохранён: <b>{user_settings[cid]['nickname']}</b>", parse_mode='HTML', reply_markup=menu)
    elif state == 'comment':
        user_settings[cid]['comment'] = text or '—'
        bot.send_message(cid, "✅ Комментарий сохранён. Спасибо за отзыв!", reply_markup=menu)
    elif state == 'feedback':
        if cid not in user_settings:
            user_settings[cid] = {}
        user_settings[cid]['last_feedback'] = text or '—'
        # Сохраняем в список для админки (чтобы можно было ответить)
        username = message.from_user.username or message.from_user.first_name or '—'
        feedback_list.append({
            'chat_id': cid,
            'text': text or '—',
            'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'username': username
        })
        bot.send_message(cid, "✅ Спасибо за обратную связь! Мы обязательно учтём ваше сообщение.", reply_markup=menu)
    elif state == 'city_input':
        user_settings[cid]['city'] = text or '—'
        bot.send_message(cid, f"✅ Город сохранён: <b>{user_settings[cid]['city']}</b>", parse_mode='HTML', reply_markup=menu)


def show_past_orders(message):
    """Показать прошлые заказы пользователя."""
    cid = message.chat.id
    orders = completed_orders.get(cid, [])
    if not orders:
        bot.send_message(
            cid,
            "📦 <b>Прошлые заказы</b>\n\nУ вас пока нет завершённых заказов.\n\nОформить заказ можно из каталога — нажмите «Начать» и выберите «Каталог».",
            parse_mode='HTML',
            reply_markup=menu
        )
        return
    lines = ["📦 <b>Прошлые заказы</b>\n"]
    for i, o in enumerate(orders[-10:], 1):  # последние 10
        lines.append(f"{i}. {o.get('product_name', '—')} | {o.get('price', '')}$ | {o.get('date', '')}")
    bot.send_message(cid, "\n".join(lines), parse_mode='HTML', reply_markup=menu)


def show_feedback(message):
    """Обратная связь: написать в поддержку или оставить сообщение."""
    text = (
        "💬 <b>Обратная связь</b>\n\n"
        "Напишите нам, задайте вопрос или оставьте отзыв. Вы можете написать напрямую продавцу или отправить сообщение через бота."
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("💬 Написать продавцу", url=f"https://t.me/{seller_contact.replace('@', '')}"))
    keyboard.add(types.InlineKeyboardButton("✏️ Оставить сообщение в боте", callback_data="feedback_write"))
    keyboard.add(types.InlineKeyboardButton("⬅️ В меню", callback_data="settings_back"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda c: c.data == "feedback_write")
def feedback_write_callback(call):
    """Запросить текст обратной связи."""
    user_settings_state[call.message.chat.id] = 'feedback'
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✏️ Напишите ваше сообщение, вопрос или отзыв в чат:"
        )
    except Exception:
        bot.send_message(call.message.chat.id, "✏️ Напишите ваше сообщение, вопрос или отзыв в чат:")
    bot.answer_callback_query(call.id)


def show_settings(message):
    """Главный экран настроек с выбором раздела и контактами в тексте."""
    try:
        text = (
            "⚙️ <b>Настройки</b>\n\n"
            f"📞 <b>Контакты:</b> {seller_phone}, {seller_contact}\n\n"
            "Выберите раздел:"
        )
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("📞 Контакты", callback_data="settings_contacts"))
        keyboard.add(types.InlineKeyboardButton("📍 Адрес", callback_data="settings_address"))
        keyboard.add(types.InlineKeyboardButton("🕐 Режим работы", callback_data="settings_hours"))
        keyboard.add(types.InlineKeyboardButton("🏙 Выбор города", callback_data="settings_city"))
        keyboard.add(types.InlineKeyboardButton("🗺 Карты", callback_data="settings_maps"))
        keyboard.add(types.InlineKeyboardButton("🧾 Онлайн чеки", callback_data="settings_receipts"))
        keyboard.add(types.InlineKeyboardButton("📊 Статистика", callback_data="settings_stats"))
        keyboard.add(types.InlineKeyboardButton("👤 Пол", callback_data="settings_gender"))
        keyboard.add(types.InlineKeyboardButton("✏️ Псевдоним", callback_data="settings_nickname"))
        keyboard.add(types.InlineKeyboardButton("💬 Комментарии", callback_data="settings_comments"))
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


@bot.callback_query_handler(func=lambda c: c.data == "settings_city")
def settings_city_callback(call):
    cid = call.message.chat.id
    _ensure_user_settings(cid)
    current = user_settings[cid].get('city') or 'не указан'
    text = f"🏙 <b>Выбор города</b>\n\nТекущий город: <b>{current}</b>\n\nВыберите или введите свой:"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for city in CITIES:
        keyboard.add(types.InlineKeyboardButton(city, callback_data=f"set_city_{city}"))
    keyboard.add(types.InlineKeyboardButton("✏️ Ввести свой город", callback_data="set_city_input"))
    keyboard.add(types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu"))
    try:
        bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        bot.send_message(cid, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("set_city_"))
def set_city_callback(call):
    if call.data == "set_city_input":
        user_settings_state[call.message.chat.id] = 'city_input'
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✏️ Введите название города:")
        except Exception:
            bot.send_message(call.message.chat.id, "✏️ Введите название города:")
        bot.answer_callback_query(call.id)
        return
    city = call.data.replace("set_city_", "", 1)
    user_settings[call.message.chat.id]['city'] = city
    text = f"✅ Город сохранён: <b>{city}</b>"
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=_settings_back_keyboard())
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=_settings_back_keyboard())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_maps")
def settings_maps_callback(call):
    text = f"🗺 <b>Карты</b>\n\nАдрес: {seller_address}\n\nОткройте в картах:"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if seller_map_link:
        keyboard.add(types.InlineKeyboardButton("🗺 Открыть в картах", url=seller_map_link))
    keyboard.add(types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu"))
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_receipts")
def settings_receipts_callback(call):
    text = "🧾 <b>Онлайн чеки</b>\n\nЧек можно получить в электронном виде после оплаты. Укажите при заказе или напишите продавцу."
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=_settings_back_keyboard())
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=_settings_back_keyboard())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_stats")
def settings_stats_callback(call):
    text = "📊 <b>Статистика</b>\n\nЗдесь будет отображаться ваша статистика заказов. Раздел в разработке."
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=_settings_back_keyboard())
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=_settings_back_keyboard())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_gender")
def settings_gender_callback(call):
    cid = call.message.chat.id
    _ensure_user_settings(cid)
    current = user_settings[cid].get('gender') or 'не указан'
    text = f"👤 <b>Пол</b>\n\nТекущее: <b>{current}</b>\n\nВыберите:"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("Мужской", callback_data="set_gender_Мужской"),
        types.InlineKeyboardButton("Женский", callback_data="set_gender_Женский")
    )
    keyboard.add(types.InlineKeyboardButton("Другое", callback_data="set_gender_Другое"))
    keyboard.add(types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu"))
    try:
        bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        bot.send_message(cid, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("set_gender_"))
def set_gender_callback(call):
    gender = call.data.replace("set_gender_", "", 1)
    _ensure_user_settings(call.message.chat.id)['gender'] = gender
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ Пол сохранён: <b>{gender}</b>", parse_mode='HTML', reply_markup=_settings_back_keyboard())
    except Exception:
        bot.send_message(call.message.chat.id, f"✅ Пол сохранён: {gender}", parse_mode='HTML', reply_markup=_settings_back_keyboard())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_nickname")
def settings_nickname_callback(call):
    cid = call.message.chat.id
    _ensure_user_settings(cid)
    current = user_settings[cid].get('nickname') or 'не указан'
    text = f"✏️ <b>Псевдоним</b>\n\nТекущий: <b>{current}</b>\n\nНажмите кнопку и введите псевдоним в чат:"
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("✏️ Ввести псевдоним", callback_data="set_nickname_input"))
    keyboard.add(types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu"))
    try:
        bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        bot.send_message(cid, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "set_nickname_input")
def set_nickname_input_callback(call):
    user_settings_state[call.message.chat.id] = 'nickname'
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✏️ Введите псевдоним в чат:")
    except Exception:
        bot.send_message(call.message.chat.id, "✏️ Введите псевдоним в чат:")
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "settings_comments")
def settings_comments_callback(call):
    text = "💬 <b>Комментарии</b>\n\nОставьте отзыв или комментарий. Нажмите кнопку и напишите в чат."
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("✏️ Оставить комментарий", callback_data="set_comment_input"))
    keyboard.add(types.InlineKeyboardButton("⬅️ В настройки", callback_data="settings_menu"))
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=keyboard)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "set_comment_input")
def set_comment_input_callback(call):
    user_settings_state[call.message.chat.id] = 'comment'
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✏️ Напишите комментарий в чат:")
    except Exception:
        bot.send_message(call.message.chat.id, "✏️ Напишите комментарий в чат:")
    bot.answer_callback_query(call.id)


def _settings_menu_keyboard():
    """Клавиатура главного меню настроек."""
    k = types.InlineKeyboardMarkup(row_width=1)
    k.add(types.InlineKeyboardButton("📞 Контакты", callback_data="settings_contacts"))
    k.add(types.InlineKeyboardButton("📍 Адрес", callback_data="settings_address"))
    k.add(types.InlineKeyboardButton("🕐 Режим работы", callback_data="settings_hours"))
    k.add(types.InlineKeyboardButton("🏙 Выбор города", callback_data="settings_city"))
    k.add(types.InlineKeyboardButton("🗺 Карты", callback_data="settings_maps"))
    k.add(types.InlineKeyboardButton("🧾 Онлайн чеки", callback_data="settings_receipts"))
    k.add(types.InlineKeyboardButton("📊 Статистика", callback_data="settings_stats"))
    k.add(types.InlineKeyboardButton("👤 Пол", callback_data="settings_gender"))
    k.add(types.InlineKeyboardButton("✏️ Псевдоним", callback_data="settings_nickname"))
    k.add(types.InlineKeyboardButton("💬 Комментарии", callback_data="settings_comments"))
    k.add(types.InlineKeyboardButton("⬅️ В главное меню", callback_data="settings_back"))
    return k


@bot.callback_query_handler(func=lambda c: c.data == "settings_menu")
def settings_menu_callback(call):
    """Возврат в меню настроек (из подраздела)."""
    text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"📞 <b>Контакты:</b> {seller_phone}, {seller_contact}\n\n"
        "Выберите раздел:"
    )
    keyboard = _settings_menu_keyboard()
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
            
            # Сохраняем в прошлые заказы
            cid = message.chat.id
            if cid not in completed_orders:
                completed_orders[cid] = []
            completed_orders[cid].append({
                'product_name': product['name'],
                'sku': order['sku'],
                'price': product['price'],
                'date': datetime.now().strftime('%d.%m.%Y'),
                'name': order['name'],
                'phone': order['phone'],
                'address': order['address']
            })
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
