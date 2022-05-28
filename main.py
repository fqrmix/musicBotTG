import telebot
from keyfinder import *
from definitions import *
from youtube import *

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def process_start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row('/youtube || Download audio from YouTube.com')
    keyboard.row('/keyfinder || Get key of .mp3 song')
    bot.send_message(message.chat.id, text = 'Press the menu button...', reply_markup = keyboard)

@bot.message_handler(commands=['youtube'])
def get_link(message):
    link_message = bot.send_message(message.chat.id, 'Send me a YouTube link!')
    bot.register_next_step_handler(link_message, youtube_download)

def youtube_download(message):
    chat_id = message.chat.id
    if message.text.startswith('https://www.youtube.com'):
        bot.reply_to(message, 'Got a YouTube link\nStarting download...')
        try: 
            filename = get_audio_from_video(message.text)
        finally:
            bot.send_audio(chat_id, audio=open(filename, 'rb'))
    else: 
        bot.reply_to(message, "I can't download from here!")

@bot.message_handler(commands=['keyfinder'])
def get_audio_file(message):
    audio_message = bot.send_message(message.chat.id, 'Send me a .mp3 file!')
    bot.register_next_step_handler(audio_message, handle_audio_file)

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


if __name__ == '__main__':
    bot.infinity_polling()