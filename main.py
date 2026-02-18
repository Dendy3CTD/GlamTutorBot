import telebot
from telebot import types

bot = telebot.TeleBot('8397040934:AAHA_1loP9-XQnyfobIfy7VW_TX1dRD1myM')

# База данных товаров
products = {
    '001': {'name': 'Тональный крем', 'price': 100, 'description': 'Качественный тональный крем для идеального тона кожи'},
    '002': {'name': 'Консилер', 'price': 200, 'description': 'Профессиональный консилер для маскировки недостатков'},
    '003': {'name': 'Пудра', 'price': 500, 'description': 'Матирующая пудра для фиксации макияжа'},
    '004': {'name': 'Румяна', 'price': 57, 'description': 'Натуральные румяна для здорового румянца'},
    '005': {'name': 'Хайлайтер', 'price': 1800, 'description': 'Премиум хайлайтер для сияния кожи'},
    '006': {'name': 'Помада', 'price': 800, 'description': 'Стойкая помада насыщенного цвета'}
}

# Контакты продавца
seller_contact = '@R_ig_hk'
seller_phone = '+7 988-742-28-16'

menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
address = types.KeyboardButton('Адрес')
prices = types.KeyboardButton('Цена')
contacts = types.KeyboardButton('Контакты')
services = types.KeyboardButton("Каталог товаров")
sign_up = types.KeyboardButton('Заказать')
menu.add(services, prices, contacts, address, sign_up)

back = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_button = types.KeyboardButton('Назад')
back.add(back_button)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Добро пожаловать в GlamTutorBot! 🎨\n\nВыберите интересующий вас раздел:", reply_markup=menu)


@bot.message_handler(content_types=['text'])
def text_message(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, 'Что вас интересует?', reply_markup=menu)
    elif message.text == 'Цена':
        price_list = "💰 Прайс-лист товаров:\n\n"
        for sku, product in products.items():
            price_list += f"{product['name']} - {product['price']}$ (Артикул: {sku})\n"
        bot.send_message(message.chat.id, price_list, reply_markup=back)
    elif message.text == 'Контакты':
        bot.send_message(message.chat.id, f'📞 Контакты продавца:\n\nТелефон: {seller_phone}\nTelegram: {seller_contact}', reply_markup=back)
    elif message.text == 'Адрес':
        bot.send_message(message.chat.id, '📍 Адрес: пр. Мира 8', reply_markup=back)
    elif message.text == 'Заказать':
        show_catalog(message)
    elif message.text == 'Каталог товаров':
        show_catalog(message)


def show_catalog(message):
    """Отображение каталога товаров с inline-кнопками"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    # Создаем кнопки для каждого товара
    buttons = []
    for sku, product in products.items():
        button_text = f"{product['name']} - {product['price']}$"
        buttons.append(types.InlineKeyboardButton(text=button_text, callback_data=f"product_{sku}"))
    
    # Добавляем кнопки в клавиатуру по 2 в ряд
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.add(buttons[i], buttons[i + 1])
        else:
            keyboard.add(buttons[i])
    
    bot.send_message(
        message.chat.id,
        "🛍️ Каталог товаров:\n\nВыберите товар для просмотра деталей и заказа:",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def product_callback(call):
    """Обработка выбора товара"""
    sku = call.data.split('_')[1]
    
    if sku in products:
        product = products[sku]
        
        # Создаем клавиатуру с действиями
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(
            text="💬 Написать продавцу",
            url=f"https://t.me/{seller_contact.replace('@', '')}"
        )
        order_button = types.InlineKeyboardButton(
            text="📦 Заказать",
            callback_data=f"order_{sku}"
        )
        back_button = types.InlineKeyboardButton(
            text="⬅️ Назад к каталогу",
            callback_data="back_to_catalog"
        )
        keyboard.add(contact_button)
        keyboard.add(order_button)
        keyboard.add(back_button)
        
        product_info = (
            f"📦 {product['name']}\n\n"
            f"💰 Цена: {product['price']}$\n"
            f"🔢 Артикул: {sku}\n\n"
            f"📝 Описание: {product['description']}\n\n"
            f"Вы можете написать продавцу или оформить заказ прямо здесь!"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=product_info,
            reply_markup=keyboard
        )
    else:
        bot.answer_callback_query(call.id, "Товар не найден")


@bot.callback_query_handler(func=lambda call: call.data.startswith('order_'))
def order_callback(call):
    """Обработка заказа товара"""
    sku = call.data.split('_')[1]
    
    if sku in products:
        product = products[sku]
        
        # Создаем клавиатуру для связи с продавцом
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(
            text="💬 Написать продавцу",
            url=f"https://t.me/{seller_contact.replace('@', '')}"
        )
        keyboard.add(contact_button)
        
        order_message = (
            f"✅ Заказ оформлен!\n\n"
            f"📦 Товар: {product['name']}\n"
            f"💰 Цена: {product['price']}$\n"
            f"🔢 Артикул: {sku}\n\n"
            f"Нажмите кнопку ниже, чтобы написать продавцу и подтвердить заказ:"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=order_message,
            reply_markup=keyboard
        )
        
        bot.answer_callback_query(call.id, "Заказ оформлен! Напишите продавцу для подтверждения.")
    else:
        bot.answer_callback_query(call.id, "Ошибка при оформлении заказа")


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_catalog')
def back_to_catalog_callback(call):
    """Возврат к каталогу"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = []
    for sku, product in products.items():
        button_text = f"{product['name']} - {product['price']}$"
        buttons.append(types.InlineKeyboardButton(text=button_text, callback_data=f"product_{sku}"))
    
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.add(buttons[i], buttons[i + 1])
        else:
            keyboard.add(buttons[i])
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🛍️ Каталог товаров:\n\nВыберите товар для просмотра деталей и заказа:",
        reply_markup=keyboard
    )


def forward(message):
    """Пересылка сообщения продавцу"""
    bot.forward_message(chat_id='@So_it_will_go', from_chat_id=message.chat.id, message_id=message.id)
    bot.send_message(message.chat.id, "Спасибо, что выбрали нас! Ваш заказ отправлен продавцу.", reply_markup=menu)
    bot.register_next_step_handler(message, forward)


bot.infinity_polling()
