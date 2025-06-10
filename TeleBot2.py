# pip install pyTelegramBotAPI vosk pydub

import os
import json
import urllib.request
import telebot
import vosk
import wave
from pydub import AudioSegment

# Загрузка изображения
url = "https://drive.google.com/uc?export=view&id=1WDN5RXcYQHiUT4JVujQ2VSwr7p0XLlYX"
filename = "skillbox_sticker.webp"
try:
    urllib.request.urlretrieve(url, filename)
except:
    print("Не удалось загрузить стикер")

# Загружаем токен из файла
with open("token.txt", "r") as file:
    token = file.read().strip()

# Создаём бота
bot = telebot.TeleBot(token)

# Поиск модели Vosk в папке проекта
def find_vosk_model():
    """Ищет папку с моделью Vosk в текущей директории"""
    current_dir = os.getcwd()
    for item in os.listdir(current_dir):
        if os.path.isdir(item) and 'vosk-model' in item.lower():
            return item
    return None

# Инициализация модели Vosk
MODEL_PATH = find_vosk_model()

def init_vosk_model():
    """Инициализирует модель Vosk"""
    if MODEL_PATH is None:
        print("❌ Модель Vosk не найдена в текущей папке")
        print("📁 Убедитесь, что папка с моделью содержит 'vosk-model' в названии")
        return None
    
    try:
        print(f"📦 Загружаем модель из: {MODEL_PATH}")
        model = vosk.Model(MODEL_PATH)
        print("✅ Модель Vosk загружена успешно")
        return model
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return None

# Инициализируем модель при запуске
vosk_model = init_vosk_model()

def oga2wav(filename):
    """Конвертирует .ога файл в .wav с правильными параметрами для Vosk"""
    new_filename = filename.replace('.oga', '.wav')
    try:
        # Загружаем аудио файл
        audio = AudioSegment.from_ogg(filename)
        
        # Vosk требует моно аудио с частотой дискретизации 16kHz
        audio = audio.set_channels(1)  # моно
        audio = audio.set_frame_rate(16000)  # 16kHz
        audio = audio.set_sample_width(2)  # 16-bit
        
        # Экспортируем в wav
        audio.export(new_filename, format='wav')
        return new_filename
    except Exception as e:
        print(f"Ошибка конвертации аудио: {e}")
        return None

def recognize_speech_vosk(oga_filename):
    """Распознает речь с помощью Vosk (офлайн)"""
    if vosk_model is None:
        return "❌ Модель Vosk не загружена"
    
    try:
        # Конвертируем в wav
        wav_filename = oga2wav(oga_filename)
        if wav_filename is None:
            return "❌ Ошибка конвертации аудио"
        
        # Открываем wav файл
        wf = wave.open(wav_filename, 'rb')
        
        # Проверяем параметры аудио
        if wf.getnchannels() != 1:
            wf.close()
            return "❌ Аудио должно быть моно"
        
        if wf.getsampwidth() != 2:
            wf.close()
            return "❌ Неподдерживаемая битность аудио"
        
        if wf.getframerate() not in [8000, 16000, 22050, 44100, 48000]:
            wf.close()
            return "❌ Неподдерживаемая частота дискретизации"
        
        # Создаем распознаватель
        rec = vosk.KaldiRecognizer(vosk_model, wf.getframerate())
        rec.SetWords(True)  # Включаем распознавание отдельных слов
        
        results = []
        
        # Читаем аудио порциями и распознаем
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
                
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get('text', '').strip()
                if text:
                    results.append(text)
        
        # Получаем финальный результат
        final_result = json.loads(rec.FinalResult())
        final_text = final_result.get('text', '').strip()
        if final_text:
            results.append(final_text)
        
        wf.close()
        
        # Очищаем временные файлы
        try:
            if os.path.exists(oga_filename):
                os.remove(oga_filename)
            if os.path.exists(wav_filename):
                os.remove(wav_filename)
        except:
            pass
        
        # Объединяем все результаты
        full_text = ' '.join(results).strip()
        
        if full_text:
            return full_text
        else:
            return "🔇 Речь не распознана или тишина"
            
    except Exception as e:
        print(f"Ошибка распознавания: {e}")
        return f"❌ Ошибка распознавания: {str(e)}"

def download_file(bot, file_id):
    """Скачивает голосовое сообщение от Telegram"""
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Создаем уникальное имя файла
        filename = f"voice_{file_id}.oga"
        
        with open(filename, 'wb') as f:
            f.write(downloaded_file)
        return filename
    except Exception as e:
        print(f"Ошибка скачивания файла: {e}")
        return None

@bot.message_handler(commands=['start'])
def say_hi(message):
    """Обработчик команды /start"""
    if vosk_model is None:
        response = """🤖 Привет! 

⚠️ Модель для распознавания речи не найдена!

📥 Для работы нужно:
1. Скачать модель с https://alphacephei.com/vosk/models/
2. Распаковать в папку с ботом
3. Перезапустить бота

🔍 Бот ищет папки с названием содержащим 'vosk-model'"""
    else:
        response = """🤖 Привет! 

✅ Бот готов к работе!
🎤 Отправьте голосовое сообщение для распознавания речи
🔧 Используется офлайн распознавание Vosk

💡 Говорите четко и не слишком быстро для лучших результатов"""
    
    bot.send_message(message.chat.id, response)
    
    # Отправляем стикер если есть
    try:
        with open('skillbox_sticker.webp', 'rb') as sticker:
            bot.send_sticker(message.chat.id, sticker)
    except FileNotFoundError:
        pass

@bot.message_handler(commands=['status'])
def check_status(message):
    """Проверка статуса модели"""
    if vosk_model is None:
        bot.send_message(message.chat.id, 
                        f"❌ Модель не загружена\n"
                        f"📁 Проверьте наличие папки с моделью Vosk")
    else:
        bot.send_message(message.chat.id, 
                        f"✅ Модель загружена из: {MODEL_PATH}\n"
                        f"🎤 Готов к распознаванию речи")

@bot.message_handler(commands=['help'])
def show_help(message):
    """Показать справку"""
    help_text = """🤖 Бот для распознавания речи

📋 Команды:
/start - Начать работу
/status - Проверить статус модели  
/help - Показать справку

🎤 Использование:
• Отправьте голосовое сообщение
• Бот переведет его в текст
• Работает полностью офлайн

💡 Советы:
• Говорите четко и разборчиво
• Избегайте фонового шума
• Оптимальная длина: 5-30 секунд

🔧 Технические детали:
• Движок: Vosk (офлайн)
• Поддержка: русский и английский
• Формат: моно, 16kHz"""
    
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(content_types=['voice'])
def transcript(message):
    """Обработчик голосовых сообщений"""
    if vosk_model is None:
        bot.send_message(message.chat.id, 
                        "❌ Модель не загружена. Используйте /help для инструкций.")
        return
    
    try:
        # Уведомляем о начале обработки
        processing_msg = bot.send_message(message.chat.id, "🔄 Обрабатываю голосовое сообщение...")
        
        # Скачиваем файл
        filename = download_file(bot, message.voice.file_id)
        if not filename:
            bot.edit_message_text("❌ Ошибка при скачивании файла", 
                                message.chat.id, processing_msg.message_id)
            return
        
        # Распознаем речь
        text = recognize_speech_vosk(filename)
        
        # Отправляем результат
        if text.startswith('❌') or text.startswith('🔇'):
            bot.edit_message_text(text, message.chat.id, processing_msg.message_id)
        else:
            result_text = f"✅ Распознано:\n\n📝 {text}"
            bot.edit_message_text(result_text, message.chat.id, processing_msg.message_id)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Произошла ошибка: {str(e)}")
        print(f"Ошибка в обработчике голоса: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик текстовых сообщений"""
    bot.send_message(message.chat.id, 
                    "🎤 Отправьте голосовое сообщение для распознавания.\n"
                    "📋 Используйте /help для получения справки.")

# Запуск бота
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 TELEGRAM BOT - VOICE TO TEXT (VOSK)")
    print("=" * 60)
    
    if MODEL_PATH:
        print(f"📦 Найдена модель: {MODEL_PATH}")
    else:
        print("⚠️  Модель Vosk не найдена!")
        print("📥 Скачайте модель с https://alphacephei.com/vosk/models/")
        print("📁 Рекомендуется: vosk-model-small-ru-0.22.zip")
    
    if vosk_model:
        print("✅ Модель успешно загружена")
    else:
        print("❌ Модель не инициализирована")
    
    print("=" * 60)
    print("🚀 Запуск бота...")
    
    try:
        bot.polling(none_stop=True, interval=0, timeout=60)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
    finally:
        print("👋 До свидания!")