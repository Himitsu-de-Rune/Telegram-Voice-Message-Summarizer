import os
import re
import time
import random
import logging
import telebot
import config
import db
from telebot import types
from convert import Converter
from summarize import summarize


bot = telebot.TeleBot(config.BOT_TOKEN)
db.init_db()

logging.basicConfig(level=logging.INFO,
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

keys = [str(i) for i in range(1, 11)]


def get_user(chat_id: int) -> dict:
    user = db.get_user(chat_id)
    if not user:
        db.save_user(chat_id, count=0, progress=0, start_time=time.time())
        user = db.get_user(chat_id)
    return user

def get_lang(message: types.Message) -> str:
    user = get_user(message.chat.id)
    return user.get("lang", "ru")

def get_prog(message: types.Message) -> int:
    user = get_user(message.chat.id)
    return user.get("progress", 0)

def get_photos(chat_id: int):
    user = get_user(chat_id)
    return user.get("photos").split(",") if user.get("photos") else []

def save_photos(chat_id: int, photos: list, progress: int):
    db.save_user(chat_id, photos=",".join(photos), progress=progress)

def make_progress(photo_name: str, chat_id: int) -> bool:
    photos = get_photos(chat_id)
    progress = get_user(chat_id).get("progress", 0)
    if not photos:
        return True
    elif photo_name in photos:
        progress += 1
        photos[int(photo_name[5]) - 1] = ''
        save_photos(chat_id, photos, progress)
        return True
    return False

def has_english(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))

def draw_progress(progress: int, message: types.Message) -> str:
    paint = []
    paint.append('[')
    if progress == 0:
        mess = {'ru': 'Авторизуйся с помощью /start для отображения прогресса',
                'en': "Login with /start to display progress"}
        return ''.join(mess[get_lang(message)])
    elif progress in [1, 2, 3]:
        for _ in range(progress * 3 - 1):
            paint.append('—')
        paint.append('●')
        for _ in range(11 - progress * 3):
            paint.append('. . ')
    elif progress == 4:
        for _ in range(12):
            paint.append('—')
    paint.append(f'] {progress*25}%')
    return ''.join(paint)


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    chat_id = message.chat.id
    db.save_user(chat_id, count=0, progress=0, start_time=time.time(), photos="photo1,photo2,photo3,photo4")
    name = message.chat.first_name if message.chat.first_name else 'No_name'
    logger.info(f'Chat {name} (ID: {chat_id}) started bot')
    input_field = {'ru': 'Воспользуйтесь меню:', 'en': 'Use the menu:'}
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
    input_field_placeholder=input_field[get_lang(message)])
    keyboard.add({'ru': 'Да', 'en': 'Yes'}[get_lang(message)],
    {'ru': 'Нет', 'en': 'No'}[get_lang(message)])
    welcome_mess = {'ru': 'Привет! Хочешь представиться? (опционально)',
    'en': 'Hy! Would you like to introduce yourself? (optionaly)'}
    bot.send_message(chat_id, welcome_mess[get_lang(message)], reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in ["Да", "Yes"])
def handle_yes(message: types.Message):
    db.save_user(message.chat.id, state="waiting_name")
    new_message = {'ru': "Так как тебя зовут?",
    'en': "So what's your name?"}
    bot.send_message(message.chat.id, new_message[get_lang(message)], reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: message.text in ["Нет", 'No'])
def handle_no(message: types.Message):
    name = message.chat.first_name if message.chat.first_name else 'No_name'
    db.save_user(message.chat.id, state=name)
    new_message = {'ru': "Тогда отправляй голосовое, я расшифрую!",
    'en': "Then send a voice message, I will decipher!"}
    bot.send_message(message.chat.id, new_message[get_lang(message)], reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: get_user(message.chat.id).get("state") == "waiting_name")
def handle_name(message: types.Message):
    name = message.text.strip()
    db.save_user(message.chat.id, state=name)
    new_message = {'ru': f"Приятно познакомиться, {name}! Отправляй голосовое, я расшифрую!",
    'en': f"Nice to meet you, {name}! Send a voice message, I will decipher!"}
    bot.send_message(message.chat.id, new_message[get_lang(message)])

@bot.message_handler(commands=['help'])
def help(message: types.Message):
    help_mess = {'ru': 'Рекомендую начать диалог с команды /start (сбрасывает прогресс). Затем пиши и отправляй голосовые или видеосообщения, я расшифрую! \nДоступные команды: \n/start \n/help \n/heart \n/progress \n/hint \n/ru \n/en',
    'en': "It is recommended to start a dialogue with the /start command (resets progress). Then write and send voice or video messages, I will decipher! \nAvailable commands: \n/start \n/help \n/heart \n/progress \n/hint \n/ru \n/en"}
    bot.send_message(message.chat.id, help_mess[get_lang(message)])

@bot.message_handler(commands=['heart'])
def heart(message: types.Message):
    bot.send_photo(message.chat.id, open('photo1.jpg', 'rb'), message_effect_id="5159385139981059251")
    if make_progress('photo1', message.chat.id):
            new_message = {'ru': f'Ты открыл {get_prog(message)}-ю карточку\nТвой прогресс: {draw_progress(get_prog(message), message)}', 
                           'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_progress(get_prog(message), message)}'}
            bot.send_message(message.chat.id, new_message[get_lang(message)])
            if get_prog(message) == 4:
                user = get_user(message.chat.id)
                new_message = {'ru': f'А ты не промах. Ты открыл все карточки!\nУ тебя ушло на это {round(time.time() - user["start_time"])//60} минут', 
                               'en': f"You're no slouch. You've opened all the cards!\nIt took you {round(time.time() - user['start_time'])//60} minutes to do this"}
                bot.send_message(message.chat.id, new_message[get_lang(message)], message_effect_id="5046509860389126442")

@bot.message_handler(commands=['progress'])
def progress(message: types.Message):
    prog = get_prog(message)
    if prog == 0:
        mess = {'ru': 'Ты еще не нашел ни одной карточки',
                'en': "You haven't found any cards yet"}
    elif prog == 1:
        mess = {'ru': f'Ты нашел только {prog} карточу\nТвой прогресс: {draw_progress(prog, message)}',
                'en': f"You found only {prog} card\nYour progress: {draw_progress(prog, message)}"}
    elif prog in (2, 3):
        mess = {'ru': f'Ты нашел {prog} карточи\nТвой прогресс: {draw_progress(prog, message)}',
                'en': f"You found {prog} cards\nYour progress: {draw_progress(prog, message)}"}
    else:
        mess = {'ru': 'Ты нашел все карточки!',
                'en': "You found all cards!"}
    bot.send_message(message.chat.id, mess[get_lang(message)])

@bot.message_handler(commands=['hint'])
def progress(message: types.Message):
    user_photos = get_photos(message.chat.id)
    while '' in user_photos:
        user_photos.remove('')
    if user_photos:
        random_photo = random.choice(user_photos)
        num = int(random_photo[5])
        if num == 1:
            mess = {'ru': 'Возможно, стоит попробовать остальные команды. Загляни в /help',
                    'en': "Perhaps, it's worth trying the other commands. Check /help"}
            bot.send_message(message.chat.id, mess[get_lang(message)])
        elif num == 2:
            mess = {'ru': 'Стоит проявить больше уважения',
                    'en': "Should show more respect"}
            bot.send_message(message.chat.id, mess[get_lang(message)])
        elif num == 3:
            mess = {'ru': 'А ты недостаточно терпеливый',
                    'en': "You are not patient enough"}
            bot.send_message(message.chat.id, mess[get_lang(message)])
        elif num == 4:
            mess = {'ru': 'Размер имеет значение',
                    'en': "Size matters"}
            bot.send_message(message.chat.id, mess[get_lang(message)])
    else:
        mess = {'ru': 'Они тебе больше не нужны 😎',
                'en': "You don't need them anymore 😎"}
        bot.send_message(message.chat.id, mess[get_lang(message)])

@bot.message_handler(commands=['ru'])
def set_ru(message: types.Message):
    if get_lang(message) != 'ru':
        db.save_user(message.chat.id, lang='ru')
        bot.send_message(message.chat.id, "Let's speak some Russian")

@bot.message_handler(commands=['en'])
def set_en(message: types.Message):
    if get_lang(message) != 'en':
        db.save_user(message.chat.id, lang='en')
        bot.send_message(message.chat.id, "Давай поговорим по-английски")

@bot.message_handler(content_types=['voice'])
def get_audio_messages(message: types.Message):
    process_audio(message, file_ext=".ogg")

@bot.message_handler(content_types=['video_note'])
def get_video_messages(message: types.Message):
    process_audio(message, file_ext=".mp4")

def process_audio(message: types.Message, file_ext):
    chat_id = message.chat.id
    file_id = message.voice.file_id if message.content_type == "voice" else message.video_note.file_id
    duration = message.voice.duration if message.content_type == "voice" else message.video_note.duration
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = str(message.message_id) + file_ext

    if duration > 200:
        mess = {'ru': 'Такое большое🥵 придется подождать', 
                'en': "So big🥵 we'll have to wait"}
        bot.send_photo(chat_id, open('photo4.jpg', 'rb'), mess[get_lang(message)], has_spoiler=True)
        if make_progress('photo4', chat_id):
            mess = {'ru': f'Ты открыл {get_prog(message)}-ю карточку\nТвой прогресс: {draw_progress(get_prog(message), message)}', 
                   'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_progress(get_prog(message), message)}'}
            bot.send_message(chat_id, mess[get_lang(message)])
            if get_prog(message) == 4:
                user = get_user(chat_id)
                mess = {'ru': f'А ты не промах. Ты открыл все карточки!\nУ тебя ушло на это {round(time.time() - user['start_time'])//60} минут', 
                        'en': f"You're no slouch. You've opened all the cards!\nIt took you {round(time.time() - user['start_time'])//60} minutes to do this"}
                bot.send_message(chat_id, mess[get_lang(message)], message_effect_id="5046509860389126442")

    elif duration > 50:
        mess = {'ru': 'Сообщение большое, придется подождать', 
                'en': "Message's bis, we'll have to wait"}
        bot.send_message(chat_id, mess[get_lang(message)])

    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    converter = Converter(file_name)
    os.remove(file_name)

    user = get_user(chat_id)
    mark = (user.get("mark") or 0)
    count = (user.get("count") or 0)
    count += 1
    db.save_user(chat_id, count=count)

    if count == 5:
        mess = {'ru': 'Автоматическое продление подписки на 1 месяц🗓️ С вашей карты списано $3.99💳 Спасибо, что остаетесь с нами!',
                'en': "Automatic renewal of subscription for 1 month🗓️ $3.99 is written from your card💳 Thank you for staying with us!"}
        bot.send_message(chat_id, mess[get_lang(message)])
    elif count == 10:
        mess = {'ru': 'Тебе не надоело?', 'en': "Aren't you tired of this?"}
        bot.send_photo(chat_id, open('photo3.jpg', 'rb'), mess[get_lang(message)])
        if make_progress('photo3', chat_id):
            mess = {'ru': f'Ты открыл {get_prog(message)}-ю карточку\nТвой прогресс: {draw_progress(get_prog(message), message)}', 
                    'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_progress(get_prog(message), message)}'}
            bot.send_message(chat_id, mess[get_lang(message)])
            if get_prog(message) == 4:
                mess = {'ru': f'А ты не промах. Ты открыл все карточки!\nУ тебя ушло на это {round(time.time() - user['start_time'])//60} минут', 
                        'en': f"You're no slouch. You've opened all the cards!\nIt took you {round(time.time() - user['start_time'])//60} minutes to do this"}
                bot.send_message(chat_id, mess[get_lang(message)], message_effect_id="5046509860389126442")

    message_text = converter.audio_to_text()
    db.save_user(chat_id, voice_text=message_text)

    if not message_text:
        mess = {'ru': 'Ничего не слышу, попробуй снова', 
                'en': "I can't hear anything, try again"}
        bot.send_message(chat_id, mess[get_lang(message)])

        if count == 4:
            mess = {'ru': 'К сожалению, бесплатный пробный период подошел к концу 😞',
                    'en': "Unfortunately, the free trial period has ended 😞"}
            bot.send_message(message.chat.id, mess[get_lang(message)])
        return
    
    if has_english(message_text):
        mess = {'ru': 'О, Вы из Англии?', 
                'en': "Oh, aren't you from England?"}
        bot.send_message(chat_id, mess[get_lang(message)])
    
    if duration > 5:
        input_field = {'ru': 'Воспользуйтесь меню:', 'en': 'Use the menu:'}
        key_1 = {'ru': 'Полный рассказ', 'en': 'Full story'}
        key_2 = {'ru': 'Краткий пересказ', 'en': 'Brief summary'}
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                             one_time_keyboard=True, 
                                             input_field_placeholder=input_field[get_lang(message)])
        keyboard.add(key_1[get_lang(message)], key_2[get_lang(message)])
        name = user.get("state") or ''
        mess = {'ru': f"Готово! {name}, тебе полный рассказ или краткий пересказ?",
                'en': f'Ready! {name}, you want the full story or a brief summary?'}
        bot.send_message(chat_id, mess[get_lang(message)], reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, message_text, reply_markup=types.ReplyKeyboardRemove())

        if count >= 3 and mark == 0:
            input_field = {'ru': 'Выберите оценку:', 'en': 'Select rating:'}
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                                 one_time_keyboard=True,
                                                 input_field_placeholder=input_field[get_lang(message)])
            keyboard.add('1','2','3','4','5','6','7','8','9','10', row_width=5)
            mess = {'ru': "Вот что там говорилось, теперь оцени, насколько я тебе помог 😊", 
                    'en': "That's what it said, now rate how much I helped you 😊"}
            bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)

        if count % 8 == 0 and mark > 0:
                input_field = {'ru': 'Воспользуйтесь меню:', 'en': 'Use the menu:'}
                key_1 = {'ru': 'Хочу', 'en': "Let's change"}
                key_2 = {'ru': 'Не хочу', 'en': "I wouldn't"}
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                                     one_time_keyboard=True, 
                                                     input_field_placeholder=input_field[get_lang(message)]) 
                keyboard.add(key_1[get_lang(message)], key_2[get_lang(message)])
                mess = {'ru': 'Не хочешь поменять оценку?', 
                        'en': "Would you want to change your rating?"}
                bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)

        if count == 4:
            mess = {'ru': 'К сожалению, бесплатный пробный период подошел к концу 😞',
                    'en': "Unfortunately, the free trial period has ended 😞"}
            bot.send_message(message.chat.id, mess[get_lang(message)])

@bot.message_handler(func=lambda msg: msg.text in ["Полный рассказ", "Краткий пересказ", "Full story", "Brief summary"])
def handle_choice(message: types.Message):
    user = get_user(message.chat.id)
    text = user.get("voice_text")
    mark = (user.get("mark") or 0)
    count = (user.get("count") or 0)

    if text:
        if message.text in ["Полный рассказ", "Full story"]:
            bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
        elif message.text in ["Краткий пересказ", "Brief summary"]:
            short_text = summarize(text)
            if len(short_text) > int(len(text) * 1.2) or len(short_text.split()) > len(set(short_text.split())) * 3:
                mess = {'ru': 'Что-то пошло не так... Лучше отправлю тебе полную версию',
                        'en': "Something went wrong... I'd better send you the full version"}
                bot.send_message(message.chat.id, mess[get_lang(message)])
                bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, short_text, reply_markup=types.ReplyKeyboardRemove())

        if count >= 3 and mark == 0:
            input_field = {'ru': 'Выберите оценку:', 'en': 'Select rating:'}
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                                 one_time_keyboard=True,
                                                 input_field_placeholder=input_field[get_lang(message)])
            keyboard.add('1','2','3','4','5','6','7','8','9','10', row_width=5)
            mess = {'ru': "Вот что там говорилось, теперь оцени, насколько я тебе помог 😊", 
                    'en': "That's what it said, now rate how much I helped you 😊"}
            bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)
                
        if count % 8 == 0 and mark > 0:
            input_field = {'ru': 'Воспользуйтесь меню:', 'en': 'Use the menu:'}
            key_1 = {'ru': 'Хочу', 'en': "Let's change"}
            key_2 = {'ru': 'Не хочу', 'en': "I wouldn't"}
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                                 one_time_keyboard=True, 
                                                 input_field_placeholder=input_field[get_lang(message)]) 
            keyboard.add(key_1[get_lang(message)], key_2[get_lang(message)])
            mess = {'ru': 'Не хочешь поменять оценку?', 
                    'en': "Would you want to change your rating?"}
            bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)

    if count == 4:
        mess = {'ru': 'К сожалению, бесплатный пробный период подошел к концу 😞',
                'en': "Unfortunately, the free trial period has ended 😞"}
        bot.send_message(message.chat.id, mess[get_lang(message)])

    db.save_user(message.chat.id, voice_text=None)

@bot.message_handler(func=lambda msg: msg.text in ['Хочу', "Let's change"])
def suggest_to_evaluate(message: types.Message):
        input_field = {'ru': 'Выберите оценку:', 'en': 'Select rating:'}
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                             one_time_keyboard=True,
                                             input_field_placeholder=input_field[get_lang(message)])
        keyboard.add('1','2','3','4','5','6','7','8','9','10', row_width=5)
        mess = {'ru': "Вот что там говорилось, теперь оцени, насколько я тебе помог 😊", 
                'en': "That's what it said, now rate how much I helped you 😊"}
        bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)

@bot.message_handler(func=lambda msg: msg.text in ['Не хочу', "I wouldn't"])
def suggest_to_evaluate(message: types.Message):
    pass
    
@bot.message_handler(func=lambda msg: msg.text in keys)
def get_mark(message: types.Message):
    mark = int(message.text)
    db.save_user(message.chat.id, mark=mark)
    if mark == 10:
        mess = {'ru': 'Спасибо за максимальную оценку!', 
                'en': "Thank you for the maximum rating!"}
        bot.send_photo(message.chat.id, open('photo2.jpg', 'rb'), mess[get_lang(message)], message_effect_id="5104841245755180586")
        if make_progress('photo2', message.chat.id):
            mess = {'ru': f'Ты открыл {get_prog(message)}-ю карточку\nТвой прогресс: {draw_progress(get_prog(message), message)}', 
                   'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_progress(get_prog(message), message)}'}
            bot.send_message(message.chat.id, mess[get_lang(message)])
            if get_prog(message) == 4:
                user = get_user(message.chat.id)
                mess = {'ru': f'А ты не промах. Ты открыл все карточки!\nУ тебя ушло на это {round(time.time() - user['start_time'])//60} минут', 
                        'en': f"You're no slouch. You've opened all the cards!\nIt took you {round(time.time() - user['start_time'])//60} minutes to do this"}
                bot.send_message(message.chat.id, mess[get_lang(message)], message_effect_id="5046509860389126442")
    else:
        mess = {'ru': 'Спасибо за оценку! Отправляй еще голосовые, если надо', 
                'en': "Thanks for the rating! Send more voicemails if needed"}
        bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=["text", "document", "photo",
    "sticker","video", "location", "contact",
    "new_chat_members", "left_chat_member", "new_chat_title",
    "new_chat_photo", "delete_chat_photo", "group_chat_created",
    "supergroup_chat_created", "channel_chat_created",
    "migrate_to_chat_id", "migrate_from_chat_id", "pinned_message"])
def get_wrong_message(message: types.Message):
    mess = {'ru': 'Я расшифровываю только голосовые и видеосообщения', 
            'en': "I only transcribe voice and video messages"}
    bot.send_message(message.chat.id, mess[get_lang(message)])


if __name__ == '__main__':
    logger.info('Starting bot')
    bot.polling(none_stop=True, timeout=111)
