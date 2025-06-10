# Простой Telegram-бот на Python
# Устанавливай библиотеку один раз:
# pip install pyTelegramBotAPI

import telebot

# Вставь сюда свой токен от BotFather
token = '7796793440:AAGpjEwv4_jrCqVq1_74WWjDUUOEFvMtSgs'

# Создаём объект бота
bot = telebot.TeleBot(token)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def say_hi(message):
    bot.send_message(message.chat.id, 'Привет, ' + message.chat.first_name)

# Запуск бота
bot.polling()
