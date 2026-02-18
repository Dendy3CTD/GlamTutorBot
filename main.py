import telebot
from telebot import types

bot = telebot.TeleBot('8397040934:AAHA_1loP9-XQnyfobIfy7VW_TX1dRD1myM')

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
    bot.send_message(message.chat.id, "Hello world", reply_markup=menu)

@bot.message_handler(content_types=['text'])
def text_message(message):
    if message.text == "Назад":
        bot.send_message(message.chat.id, 'Что вас интересует?', reply_markup = menu)
    elif message.text == 'Цена':
        bot.send_message(message.chat.id, 'тональные кремы = 100$ \n консилеры = 200$ \n пудры = 500$ \n румяна = 57$ \n хайлайтеры 1800$ \n крч вот девушки для вас бля буду = 800$', reply_markup= back)
    elif message.text == 'Контакты':
        bot.send_message(message.chat.id, '+7 988-742-28-16, @R_ig_hk', reply_markup= back)
    elif message.text == 'Адрес':
        bot.send_message(message.chat.id, 'пр. Мира 8', reply_markup= back)
    elif message.text == 'Заказать':
        bot.send_message(message.chat.id, 'Введите артикул товара',  reply_markup= types.ReplyKeyboardRemove())

def forward(message):
    bot.forward_message(chat_id='@So_it_will_go', from_chat_id = message.chat.id, message_id= message.id)
    bot.send_message(message.chat.id, "Спасибо, что выбрали нас", reply_markup=menu)
    bot.register_next_step_handler(message, forward)

bot.infinity_polling()