# Простой Telegram-бот на Python
# Устанавливай библиотеку один раз:
# pip install pyTelegramBotAPI

import telebot

# Загружаем токен из файла
with open("token.txt", "r") as file:
    token = file.read().strip()

# Создаём объект бота
bot = telebot.TeleBot(token)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def say_hi(message):
    bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name)

# Запуск бота
bot.polling()
