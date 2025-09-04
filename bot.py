import os
import re
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
user_mark = {}
user_count = {}
user_lang = {}
user_progress = {}
user_photos = {}

keys = [str(i) for i in range(1, 11)]

@bot.message_handler(commands=['start']) 
def start(message: types.Message): 
    name = message.chat.first_name if message.chat.first_name else 'No_name' 
    user_count[message.chat.id] = 0 
    user_progress[message.chat.id] = 0
    user_photos[message.chat.id] = ['photo1', 'photo2', 'photo3', 'photo4']
    logger.info(f'Chat {name} (ID: {message.chat.id}) started bot') 
    input_field = {'ru': 'Воспользуйтесь меню:', 'en': 'Use the menu:'}
    key_yes = {'ru': 'Да', 'en': 'Yes'}
    key_no = {'ru': 'Нет', 'en': 'No'}
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                         one_time_keyboard=True, 
                                         input_field_placeholder=input_field[get_lang(message)]) 
    keyboard.add(key_yes[get_lang(message)], key_no[get_lang(message)]) 
    welcome_mess = {'ru': 'Привет! Хочешь представиться? (опционально)', 
                    'en': 'Hy! Would you like to introduce yourself? (optionaly)'} 
    bot.send_message(message.chat.id, welcome_mess[get_lang(message)], reply_markup=keyboard) 

@bot.message_handler(func=lambda message: message.text in ["Да", "Yes"])
def handle_yes(message: types.Message):
    new_message = {'ru': "Так как тебя зовут?", 
                   'en': "So what's your name?"}
    bot.send_message( message.chat.id, 
                     new_message[get_lang(message)], 
                     reply_markup=types.ReplyKeyboardRemove() )
    user_states[message.chat.id] = "waiting_name"

@bot.message_handler(func=lambda message: message.text in ["Нет", 'No'])
def handle_no(message: types.Message):
    new_message = {'ru': "Тогда отправляй голосовое, я расшифрую!", 
                   'en': "Then send a voice message, I will decipher!"}
    bot.send_message( message.chat.id, 
                     new_message[get_lang(message)], 
                     reply_markup=types.ReplyKeyboardRemove() )
    user_states[message.chat.id] = message.chat.first_name if message.chat.first_name else 'No_name'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_name")
def handle_name(message: types.Message):
    name = message.text.strip()
    user_states[message.chat.id] = name
    new_message = {'ru': f"Приятно познакомиться, {name}! Отправляй голосовое, я расшифрую!", 
                   'en': f"Nice to meet you, {name}! Send a voice message, I will decipher!"}
    bot.send_message(message.chat.id, 
                     new_message[get_lang(message)])

@bot.message_handler(commands=['help'])
def help(message: types.Message):
    help_mess = {'ru': 'Рекомендую начать диалог с команды /start (сбрасывает прогресс). Затем пиши и отправляй голосовые или видеосообщения, я расшифрую! \nДоступные команды: \n/start \n/help \n/heart \n/progress \n/ru \n/en',
                 'en': "It is recommended to start a dialogue with the /start command (resets progress). Then write and send voice or video messages, I will decipher! \nAvailable commands: \n/start \n/help \n/heart \n/progress \n/ru \n/en"}
    bot.send_message(message.chat.id, help_mess[get_lang(message)])

@bot.message_handler(commands=['heart'])
def help(message: types.Message):
    bot.send_photo(message.chat.id, open('photo1.jpg', 'rb'))
    if make_progress('photo1', message.chat.id):
            new_message = {'ru': f'Ты открыл {get_prog(message)}-ю карточку.\nТвой прогресс: {draw_a_progress(get_prog(message), message)}', 
                           'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_a_progress(get_prog(message), message)}'}
            bot.send_message(message.chat.id, new_message[get_lang(message)])
            if get_prog(message) == 4:
                new_message = {'ru': 'А ты не промах. Ты открыл все карточки!', 
                               'en': "You're no slouch. You've opened all the cards!"}
                bot.send_message(message.chat.id, new_message[get_lang(message)])

@bot.message_handler(commands=['progress'])
def help(message: types.Message):
    if get_prog(message) == 0:
        mess = {'ru': 'Ты еще не нашел ни одной карточки', 
                'en': "You haven't found any cards yet"}
        bot.send_message(message.chat.id, mess[get_lang(message)])
    elif get_prog(message) == 1:
        mess = {'ru': f'Ты нашел только {get_prog(message)} карточу\nТвой прогресс: {draw_a_progress(get_prog(message), message)}', 
                'en': f"You found only {get_prog(message)} card\nYou're progress: {draw_a_progress(get_prog(message), message)}"}
        bot.send_message(message.chat.id, mess[get_lang(message)])
    elif get_prog(message) in (2, 3):
        mess = {'ru': f'Ты нашел {get_prog(message)} карточи\nТвой прогресс: {draw_a_progress(get_prog(message), message)}', 
                'en': f"You found {get_prog(message)} cards\nYou're progress: {draw_a_progress(get_prog(message), message)}"}
        bot.send_message(message.chat.id, mess[get_lang(message)])
    elif get_prog(message) >= 4:
        mess = {'ru': 'Ты нашел все карточки!', 
                'en': "You found all cards!"}
        bot.send_message(message.chat.id, mess[get_lang(message)])

def get_prog(message: types.Message) -> int:
    return user_progress.get(message.chat.id, 0)

def get_lang(message: types.Message) -> str:
    return user_lang.get(message.chat.id, 'ru')

@bot.message_handler(commands=['ru'])
def set_ru(message: types.Message):
    user_lang[message.chat.id] = 'ru'
    bot.send_message(message.chat.id, "Теперь говорим по-русски")

@bot.message_handler(commands=['en'])
def set_en(message: types.Message):
    user_lang[message.chat.id] = 'en'
    bot.send_message(message.chat.id, "Let's speak English")

@bot.message_handler(content_types=['voice'])
def get_audio_messages(message: types.Message):
    process_audio(message, file_ext=".ogg")

@bot.message_handler(content_types=['video_note'])
def get_video_messages(message: types.Message):
    process_audio(message, file_ext=".mp4")

def process_audio(message: types.Message, file_ext):
    file_id = message.voice.file_id if message.content_type == "voice" else message.video_note.file_id
    duration = message.voice.duration if message.content_type == "voice" else message.video_note.duration
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = str(message.message_id) + file_ext

    if duration > 200:
        mess = {'ru': 'Такое большое, придется подождать', 
                'en': "So big, we'll have to wait"}
        bot.send_photo(message.chat.id, open('photo4.jpg', 'rb'), mess[get_lang(message)])
        if make_progress('photo4', message.chat.id):
            mess = {'ru': f'Ты открыл {get_prog(message)}-ю карточку.\nТвой прогресс: {draw_a_progress(get_prog(message), message)}', 
                   'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_a_progress(get_prog(message), message)}'}
            bot.send_message(message.chat.id, mess[get_lang(message)])
            if get_prog(message) == 4:
                mess = {'ru': 'А ты не промах. Ты открыл все карточки!', 
                        'en': "You're no slouch. You've opened all the cards!"}
                bot.send_message(message.chat.id, mess[get_lang(message)])

    elif duration > 50:
        mess = {'ru': 'Сообщение большое, придется подождать', 
                'en': "Message's bis, we'll have to wait"}
        bot.send_message(message.chat.id, mess[get_lang(message)])

    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    converter = Converter(file_name)
    os.remove(file_name)
    try:
        user_count[message.chat.id] += 1
        if user_count[message.chat.id] == 5:
            mess = {'ru': 'Автоматическое продление подписки на 1 месяц🗓️ С вашей карты списано $3.99💳 Спасибо, что остаетесь с нами!',
                    'en': "Automatic renewal of subscription for 1 month🗓️ $3.99 is written from your card💳 Thank you for staying with us!"}
            bot.send_message(message.chat.id, mess[get_lang(message)])
        elif user_count[message.chat.id] == 10:
            mess = {'ru': 'Тебе не надоело?', 'en': "Aren't you tired of this?"}
            bot.send_photo(message.chat.id, open('photo3.jpg', 'rb'), mess[get_lang(message)])
            if make_progress('photo3', message.chat.id):
                mess = {'ru': f'Ты открыл {get_prog(message)}-ю карточку.\nТвой прогресс: {draw_a_progress(get_prog(message), message)}', 
                        'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_a_progress(get_prog(message), message)}'}
                bot.send_message(message.chat.id, mess[get_lang(message)])
                if get_prog(message) == 4:
                    mess = {'ru': 'А ты не промах. Ты открыл все карточки!', 
                            'en': "You're no slouch. You've opened all the cards!"}
                    bot.send_message(message.chat.id, mess[get_lang(message)])
    except KeyError:
        user_count[message.chat.id] = 1

    message_text = converter.audio_to_text()
    user_voice_texts[message.chat.id] = message_text

    if not message_text:
        mess = {'ru': 'Ничего не слышу, попробуй снова', 
                'en': "I can't hear anything, try again"}
        bot.send_message(message.chat.id, mess[get_lang(message)])
        return
    if has_english(message_text):
        mess = {'ru': 'О, Вы из Англии?', 
                'en': "Oh, aren't You from England?"}
        bot.send_message(message.chat.id, mess[get_lang(message)])
    
    if duration > 5:
        input_field = {'ru': 'Воспользуйтесь меню:', 'en': 'Use the menu:'}
        key_1 = {'ru': 'Полный рассказ', 'en': 'Full story'}
        key_2 = {'ru': 'Краткий пересказ', 'en': 'Brief summary'}
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                             one_time_keyboard=True, 
                                             input_field_placeholder=input_field[get_lang(message)]) 
        keyboard.add(key_1[get_lang(message)], key_2[get_lang(message)]) 
        try:
            mess = {'ru': f"Готово! {user_states[message.chat.id]}, тебе полный рассказ или краткий пересказ?", 
                    'en': f'Ready! {user_states[message.chat.id]}, you want the full story or a brief summary?'}
            bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)
        except KeyError:
            mess = {'ru': f"Готово! Тебе полный рассказ или краткий пересказ?", 
                    'en': f'Ready! You want the full story or a brief summary?'}
            bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, message_text, reply_markup=types.ReplyKeyboardRemove())

        if user_count[message.chat.id] >= 3:
            try:
                user_mark[message.chat.id]
            except KeyError:
                input_field = {'ru': 'Выберите оценку:', 'en': 'Select rating:'}
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                                     one_time_keyboard=True,
                                                     input_field_placeholder=input_field[get_lang(message)])
                keyboard.add('1','2','3','4','5','6','7','8','9','10', row_width=5)
                mess = {'ru': "Вот что там говорилось, теперь оцени, насколько я тебе помог 😊", 
                        'en': "That's what it said, now rate how much I helped you 😊"}
                bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)

        if user_count[message.chat.id] % 8 == 0 and user_mark[message.chat.id] > 0:
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

        if user_count[message.chat.id] == 4:
            mess = {'ru': 'К сожалению, бесплатный пробный период подошел к концу 😞',
                    'en': "Unfortunately, the free trial period has ended 😞"}
            bot.send_message(message.chat.id, mess[get_lang(message)])

@bot.message_handler(func=lambda msg: msg.text in ["Полный рассказ", "Краткий пересказ", "Full story", "Brief summary"])
def handle_choice(message: types.Message):
    text = user_voice_texts.get(message.chat.id)

    if text:
        if message.text in ["Полный рассказ", "Full story"]:
            bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
        elif message.text in ["Краткий пересказ", "Brief summary"]:
            short_text = summarize(text)
            if len(short_text) > int(len(text) * 1.2):
                mess = {'ru': 'Что-то пошло не так... Лучше отправлю тебе полную версию',
                        'en': "Something went wrong... I'd better send you the full version"}
                bot.send_message(message.chat.id, mess[get_lang(message)])
                bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, short_text, reply_markup=types.ReplyKeyboardRemove())

        try:
            if user_count[message.chat.id] >= 3:
                try:
                    user_mark[message.chat.id]
                except KeyError:
                    input_field = {'ru': 'Выберите оценку:', 'en': 'Select rating:'}
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                                         one_time_keyboard=True,
                                                         input_field_placeholder=input_field[get_lang(message)])
                    keyboard.add('1','2','3','4','5','6','7','8','9','10', row_width=5)
                    mess = {'ru': "Вот что там говорилось, теперь оцени, насколько я тебе помог 😊", 
                            'en': "That's what it said, now rate how much I helped you 😊"}
                    bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)
                    
            if user_count[message.chat.id] % 8 == 0 and user_mark[message.chat.id] > 0:
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
        except:
            pass

    try:
        if user_count[message.chat.id] == 4:
            mess = {'ru': 'К сожалению, бесплатный пробный период подошел к концу 😞',
                    'en': "Unfortunately, the free trial period has ended 😞"}
            bot.send_message(message.chat.id, mess[get_lang(message)])
    except KeyError:
        pass

    user_voice_texts.pop(message.chat.id, None)

@bot.message_handler(func=lambda msg: msg.text in ['Хочу', "Let's change"])
def suggest_to_evaluate(message: types.Message):
    try:
        input_field = {'ru': 'Выберите оценку:', 'en': 'Select rating:'}
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, 
                                             one_time_keyboard=True,
                                             input_field_placeholder=input_field[get_lang(message)])
        keyboard.add('1','2','3','4','5','6','7','8','9','10', row_width=5)
        mess = {'ru': "Вот что там говорилось, теперь оцени, насколько я тебе помог 😊", 
                'en': "That's what it said, now rate how much I helped you 😊"}
        bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=keyboard)
    except:
        pass

@bot.message_handler(func=lambda msg: msg.text in ['Не хочу', "I wouldn't"])
def suggest_to_evaluate(message: types.Message):
    pass
    
@bot.message_handler(func=lambda msg: msg.text in keys)
def get_mark(message: types.Message):
    if message.text == '10':
        mess = {'ru': 'Спасибо за максимальную оценку!', 
                'en': "Thank you for the maximum rating!"}
        bot.send_photo(message.chat.id, open('photo2.jpg', 'rb'), mess[get_lang(message)])
        if make_progress('photo2', message.chat.id):
            mess = {'ru': f'Ты открыл {get_prog(message)}-ю карточку.\nТвой прогресс: {draw_a_progress(get_prog(message), message)}', 
                   'en': f'You have opened the {get_prog(message)}-th card\nYour progress: {draw_a_progress(get_prog(message), message)}'}
            bot.send_message(message.chat.id, mess[get_lang(message)])
            if get_prog(message) == 4:
                mess = {'ru': 'А ты не промах. Ты открыл все карточки!', 
                        'en': "You're no slouch. You've opened all the cards!"}
                bot.send_message(message.chat.id, mess[get_lang(message)])
    else:
        mess = {'ru': 'Спасибо за оценку! Отправляй еще голосовые, если надо', 
                'en': "Thanks for the rating! Send more voicemails if needed"}
        bot.send_message(message.chat.id, mess[get_lang(message)], reply_markup=types.ReplyKeyboardRemove())
    user_mark[message.chat.id] = int(message.text)

@bot.message_handler(content_types=["text", "document", "photo",
    "sticker","video", "location", "contact",
    "new_chat_members", "left_chat_member", "new_chat_title",
    "new_chat_photo", "delete_chat_photo", "group_chat_created",
    "supergroup_chat_created", "channel_chat_created",
    "migrate_to_chat_id", "migrate_from_chat_id", "pinned_message"])
def get_text_message(message: types.Message):
    mess = {'ru': 'Я расшифровываю только голосовые и видеосообщения', 
            'en': "I only transcribe voice and video messages"}
    bot.send_message(message.chat.id, mess[get_lang(message)])

def has_english(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))

def get_photos(chat_id: int) -> set:
    return user_photos.get(chat_id, None)

def make_progress(photo_name: str, chat_id: int) -> bool:
    if get_photos(chat_id) == None:
        return True
    elif photo_name in get_photos(chat_id):
        user_progress[chat_id] += 1
        get_photos(chat_id)[int(photo_name[5])-1] = ''
        return True
    return False

def draw_a_progress(progress: int, message: types.Message) -> str:
    paint = []
    paint.append('[')
    if progress == 0:
        mess = {'ru': 'Авторизуйся с помощью /start для отображения прогресса', 
                'en': "Login with /start to display progress"}
        paint.append(mess[get_lang(message)])
    elif progress in [1, 2, 3]:
        for _ in range(progress * 3 - 1):
            paint.append('—')
        paint.append('●')
        for _ in range(11 - progress * 3):
            paint.append('. . ')
    elif progress == 4:
        for _ in range(12):
            paint.append('—')
    paint.append(']')
    return ''.join(paint)


if __name__ == '__main__':
    logger.info('Starting bot')
    bot.polling(none_stop=True, timeout=111)
