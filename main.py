import telebot
from keyfinder import *
from definitions import *
from youtube import *

bot = telebot.TeleBot(TOKEN)
myTonality = Tonality()

def build_keyboard(keyboard_type):
    if keyboard_type == 'main':
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        main_menu_button_list = [
            telebot.types.InlineKeyboardButton(text='Download audio from YouTube.com', callback_data='youtube'),
            telebot.types.InlineKeyboardButton(text='Get key of .mp3 song', callback_data='keyfinder'),
            telebot.types.InlineKeyboardButton(text='Get a random chord progression', callback_data='randomchords')
        ]
        keyboard.add(*main_menu_button_list)
        return keyboard

    if keyboard_type == 'chords':
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        chords_menu_button_list = [
            telebot.types.InlineKeyboardButton(text='Random', callback_data='random'),
            telebot.types.InlineKeyboardButton(text='Specific', callback_data='specific'),
            telebot.types.InlineKeyboardButton(text='<< Get back', callback_data='back_to_main')
        ]
        keyboard.add(*chords_menu_button_list)
        return keyboard

    if keyboard_type == 'specific':
        myTonality = Tonality()
        keyboard = telebot.types.InlineKeyboardMarkup()
        specific_button_list = []
        for specific_pitch in myTonality.pitches:
            specific_button_list.append(telebot.types.InlineKeyboardButton(text=specific_pitch, callback_data='specific_keys_' + specific_pitch))
        specific_button_list.append(telebot.types.InlineKeyboardButton(text='<< Get back', callback_data='back_to_chords'))
        keyboard.add(*specific_button_list)
        return keyboard

    if keyboard_type == 'specific_scale':
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        chords_menu_button_list = [
            telebot.types.InlineKeyboardButton(text='Major', callback_data='specific_scale_major'),
            telebot.types.InlineKeyboardButton(text='Minor', callback_data='specific_scale_minor'),
            telebot.types.InlineKeyboardButton(text='<< Get back', callback_data='back_to_chords')
        ]
        keyboard.add(*chords_menu_button_list)
        return keyboard

    if keyboard_type == 'back_to_main':
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(telebot.types.InlineKeyboardButton(text='<< Get back', callback_data='back_to_main'))
        return keyboard


# YouTube -> mp3 convert

def youtube_download(message):
    chat_id = message.chat.id
    if message.text.startswith('https://www.youtube.com'):
        bot.reply_to(message, 'Got a YouTube link\nStarting download...')
        filename = get_audio_from_video(message.text)
        with open(filename, 'rb') as audio:
            bot.send_audio(chat_id, audio)
            audio.flush()
        handle_audio_file(message, from_youtube=filename)
        
    else:
        bot.send_message(chat_id, "I can't download from here!\nSend me a correct link!", reply_markup=build_keyboard('back_to_main'))
        bot.register_next_step_handler(message, youtube_download)

# Get key of song

def handle_audio_file(message, from_youtube=None):
    chat_id = message.chat.id
    if message.content_type != 'audio' and from_youtube is None:
            bot.send_message(chat_id, f"I am waiting for audio file!\nNot for {message.content_type}!", reply_markup=build_keyboard('back_to_main'))
            bot.register_next_step_handler(message, handle_audio_file)
    else:
        try:
            if from_youtube is None:
                chat_id = message.chat.id
                file_info = bot.get_file(message.audio.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                src = ROOT_DIR + "/received/"

                audio_path = src + message.audio.file_name
                with open(audio_path, 'wb') as audio_file:
                    audio_file.write(downloaded_file)
                    audio_file.flush()
                
                del downloaded_file, file_info, audio_file
            else:
                audio_path = from_youtube
            bot.reply_to(message, 'Starting analysis...')

            y, sr = librosa.load(audio_path, sr=11025)
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            downloaded_audio = Tonal_Fragment(y_harmonic, sr, tend=22)
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            likely_key, alt_key = downloaded_audio.print_key()
            del y, sr, y_harmonic, downloaded_audio

            if alt_key is not None:
                bot.reply_to(message, f'Song key: `{likely_key}`\nMaybe it can be a: `{alt_key}`\nBPM: `{round(tempo)}`', parse_mode='Markdown')
            else:
                bot.reply_to(message, f'Song key: `{likely_key}`\nBPM: `{round(tempo)}`', parse_mode='Markdown')
            del likely_key, alt_key, tempo
        except Exception as e:
            bot.reply_to(message, e)

# Start init

@bot.message_handler(commands=['start'])
def main_menu(message):
    bot.send_message(message.chat.id, text = 'Press the menu button...', reply_markup = build_keyboard('main'))

# Callback handler

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "youtube":
        link_message = bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Send me a YouTube link!',
            reply_markup=build_keyboard('back_to_main'))
        bot.register_next_step_handler(link_message, youtube_download)
    
    elif call.data == "keyfinder":
        audio_message = bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Send me a .mp3 file!',
            reply_markup=build_keyboard('back_to_main'))
        bot.register_next_step_handler(audio_message, handle_audio_file)

    elif call.data == "randomchords" or call.data == "back_to_chords":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Random/Specific?', 
            reply_markup=build_keyboard('chords'))

    elif call.data == 'random':
        progression_key, chord_progression_message = myTonality.get_random_major_chord_progression()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Scale of progression: `[{progression_key}]`',
            parse_mode='Markdown')
        bot.send_message(
            call.message.chat.id, 
            text = f'`{chord_progression_message}`', 
            parse_mode='Markdown')
        del progression_key, chord_progression_message

    elif call.data == 'specific':
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Choose the pitch:', 
            reply_markup=build_keyboard('specific'))
            
    elif call.data.startswith('specific_'):
        if call.data.startswith('specific_keys_'):
            myTonality.current_key = call.data.replace('specific_keys_', '')
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Key of progression: {myTonality.current_key}\nChoose major/minor:', 
                reply_markup=build_keyboard('specific_scale'))

        if call.data.startswith('specific_scale_'):
            myTonality.current_scale = call.data.replace('specific_scale_', '')
            myTonality.current_tonality = myTonality.current_key + ' ' + myTonality.current_scale
            progression_key, chord_progression_message = myTonality.get_random_major_chord_progression(myTonality.current_tonality)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Scale of progression: `[{myTonality.current_tonality}]`',
                parse_mode='Markdown')
            bot.send_message(
                call.message.chat.id, 
                text = f'`{chord_progression_message}`', 
                parse_mode='Markdown')
            del myTonality.current_scale, myTonality.current_tonality, myTonality.current_key, progression_key, chord_progression_message

    elif call.data == 'back_to_main':
        bot.clear_step_handler(call.message)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Press the menu button...', 
            reply_markup=build_keyboard('main'))

# Start infinity polling (loop)

if __name__ == '__main__':
    bot.infinity_polling()