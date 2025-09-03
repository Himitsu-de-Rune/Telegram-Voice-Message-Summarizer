import os
import logging
import telebot
import config
from telebot import types
from convert import Converter
from summarize import summarize

bot = telebot.TeleBot(config.BOT_TOKEN)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

user_states = {}
user_voice_texts = {}
mark = {}
count = {}

@bot.message_handler(commands=['start'])
def start(message: types.Message):
    name = message.chat.first_name if message.chat.first_name else 'No_name'
    count[message.chat.id] = 0
    logger.info(f'Chat {name} (ID: {message.chat.id}) started bot')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Да", "Нет")
    welcome_mess = 'Привет! Хочешь представиться?'
    bot.send_message(message.chat.id, welcome_mess, reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "Да")
def handle_yes(message: types.Message):
    bot.send_message(
        message.chat.id,
        "Так как тебя зовут?",
        reply_markup=types.ReplyKeyboardRemove()
    )
    user_states[message.chat.id] = "waiting_name"

@bot.message_handler(func=lambda message: message.text == "Нет")
def handle_no(message: types.Message):
    bot.send_message(
        message.chat.id,
        "Тогда отправляй голосовое, я расшифрую!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    user_states[message.chat.id] = message.chat.first_name if message.chat.first_name else 'No_name'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_name")
def handle_name(message: types.Message):
    name = message.text.strip()
    user_states[message.chat.id] = name
    bot.send_message(message.chat.id, f"Приятно познакомиться, {name}! Отправляй голосовое, я расшифрую!")

@bot.message_handler(commands=['help'])
def help(message: types.Message):
    help_mess = 'Запиши и отправь голосовое или видео сообщение, я расшифрую!'
    bot.send_message(message.chat.id, help_mess)

@bot.message_handler(content_types=['voice'])
def get_audio_messages(message: types.Message):
    process_audio(message, file_ext=".ogg")

@bot.message_handler(content_types=['video_note'])
def get_video_messages(message: types.Message):
    process_audio(message, file_ext=".mp4")

def process_audio(message: types.Message, file_ext):
    file_id = message.voice.file_id if message.content_type == "voice" else message.video_note.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = str(message.message_id) + file_ext

    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    converter = Converter(file_name)
    os.remove(file_name)
    try:
        count[message.chat.id] += 1
        if count[message.chat.id] == 5:
            bot.send_message(message.chat.id, 'Автоматическое продление подписки на 1 месяц🗓️ С вашего кошелька списано $3.99💳 Спасибо, что остаетесь с нами!')
    except KeyError:
        pass

    message_text = converter.audio_to_text()
    if not message_text:
        bot.send_message(message.chat.id, "Ничего не слышу, попробуй снова")
        return
    user_voice_texts[message.chat.id] = message_text

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Полный рассказ", "Краткий пересказ")
    try:
        bot.send_message(message.chat.id, f"Готово! {user_states[message.chat.id]}, тебе полный рассказ или краткий пересказ?", reply_markup=keyboard)
    except KeyError:
        bot.send_message(message.chat.id, f"Готово! Тебе полный рассказ или краткий пересказ?", reply_markup=keyboard)

@bot.message_handler(func=lambda msg: msg.text in ["Полный рассказ", "Краткий пересказ"])
def handle_choice(message: types.Message):
    text = user_voice_texts.get(message.chat.id)

    if message.text == "Полный рассказ":
        bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
    elif message.text == "Краткий пересказ":
        short_text = summarize(text)
        bot.send_message(message.chat.id, short_text, reply_markup=types.ReplyKeyboardRemove())

    try:
        if count[message.chat.id] == 4:
            bot.send_message(message.chat.id, 'К сожалению, бесплатный пробный период подошел к концу 😞')
    except KeyError:
        pass

    try:
        mark[message.chat.id]
    except KeyError:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add('1', '2', '3', '4', '5', '6', '7', '8', '9', '10')
        bot.send_message(message.chat.id, "Вот что там говорилось, теперь оцени, насколько я тебе помог 😊", reply_markup=keyboard)

    user_voice_texts.pop(message.chat.id, None)

@bot.message_handler(func=lambda msg: msg.text in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
def get_mark(message: types.Message):
    bot.send_message(message.chat.id, 'Спасибо за оценку! Отправляй еще голосовые, если надо', reply_markup=types.ReplyKeyboardRemove())
    mark[message.chat.id] = message

@bot.message_handler(content_types=["text", "document", "photo",
    "sticker","video", "location", "contact",
    "new_chat_members", "left_chat_member", "new_chat_title",
    "new_chat_photo", "delete_chat_photo", "group_chat_created",
    "supergroup_chat_created", "channel_chat_created",
    "migrate_to_chat_id", "migrate_from_chat_id", "pinned_message"])
def get_text_message(message: types.Message):
    bot.send_message(message.chat.id, 'Я расшифровываю только голосовые сообщения')


if __name__ == '__main__':
    logger.info('Starting bot')
    bot.polling(none_stop=True, timeout=111)