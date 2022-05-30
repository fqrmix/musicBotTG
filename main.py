from sre_parse import State
from subprocess import call
import telebot
from keyfinder import *
from definitions import *
from youtube import *

bot = telebot.TeleBot(TOKEN)

# YouTube -> mp3 convert

def youtube_download(message,):
    chat_id = message.chat.id
    if message.text.startswith('https://www.youtube.com'):
        bot.reply_to(message, 'Got a YouTube link\nStarting download...')
        try: 
            filename = get_audio_from_video(message.text)
        finally:
            bot.send_audio(chat_id, audio=open(filename, 'rb'))
    else:
        bot.reply_to(message, "I can't download from here!")

# Get key of song

def handle_audio_file(message):
    try:
        chat_id = message.chat.id
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        src = ROOT_DIR + "/received/"

        audio_path = src + message.audio.file_name

        try:
            with open(audio_path, 'wb') as new_file:
                new_file.write(downloaded_file)
        except Exception as e:
            print(e)

        bot.reply_to(message, 'Downloaded! Starting analysis...')

        y, sr = librosa.load(audio_path, sr=11025)
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        downloaded_audio = Tonal_Fragment(y_harmonic, sr, tend=22)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        print(tempo)
        likely_key, alt_key = downloaded_audio.print_key()

        if alt_key is not None:
            bot.reply_to(message, f'Song key: {likely_key}\nMaybe it can be a: {alt_key}')
        else:
            bot.reply_to(message, f'Song key:{likely_key}')
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(commands=['start'])
def main_menu(message):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)

    main_menu_button_list = [
        telebot.types.InlineKeyboardButton(text='Download audio from YouTube.com', callback_data='youtube'),
        telebot.types.InlineKeyboardButton(text='Get key of .mp3 song', callback_data='keyfinder'),
        telebot.types.InlineKeyboardButton(text='Get a random chord progression', callback_data='randomchords')
    ]

    keyboard.add(*main_menu_button_list)

    bot.send_message(message.chat.id, text = 'Press the menu button...', reply_markup = keyboard)

# Random Chord Progression Menu

def random_chords_menu(message):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)

    chords_menu_button_list = [
        telebot.types.InlineKeyboardButton(text='Random', callback_data='random'),
        telebot.types.InlineKeyboardButton(text='Specific', callback_data='specific'),
        telebot.types.InlineKeyboardButton(text='<< Get back', callback_data='back')
    ]
    keyboard.add(*chords_menu_button_list)

    bot.send_message(
        chat_id=message.chat.id, 
        text = 'Press the menu button...', 
        reply_markup = keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    if call.data == "youtube":
        link_message = bot.send_message(call.message.chat.id, 'Send me a YouTube link!')
        bot.register_next_step_handler(link_message, youtube_download)

    elif call.data == "keyfinder":
        audio_message = bot.send_message(call.message.chat.id, 'Send me a .mp3 file!')
        bot.register_next_step_handler(audio_message, handle_audio_file)

    elif call.data == "randomchords":
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)

        chords_menu_button_list = [
            telebot.types.InlineKeyboardButton(text='Random', callback_data='random'),
            telebot.types.InlineKeyboardButton(text='Specific', callback_data='specific'),
            telebot.types.InlineKeyboardButton(text='<< Get back', callback_data='back')
        ]
        keyboard.add(*chords_menu_button_list)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Random/Specific?', 
            reply_markup=keyboard)

    elif call.data == 'random':
        myTonality = Tonality()
        progression_key, chord_progression_message = myTonality.get_random_major_chord_progression()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Key of progression: `[{progression_key}]`',
            parse_mode='Markdown')
        bot.send_message(
            call.message.chat.id, 
            text = f'`{chord_progression_message}`', 
            parse_mode='Markdown')

    elif call.data == 'specific':
        myTonality = Tonality()
        specific_keyboard = telebot.types.InlineKeyboardMarkup(row_width=3)
        
        specific_button_list = []
        for specific_pitch in myTonality.pitches:
            specific_button_list.append(telebot.types.InlineKeyboardButton(text=specific_pitch, callback_data=specific_pitch))
        specific_button_list.append(telebot.types.InlineKeyboardButton(text='<< Get back', callback_data='back_to_chords'))
        specific_keyboard.add(*specific_button_list)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Choose the pitch:', 
            reply_markup=specific_keyboard)
            
# Start

if __name__ == '__main__':
    bot.infinity_polling()