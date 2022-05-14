import telebot
from keyfinder import *
from definitions import *
import subprocess

print(ROOT_DIR)

botWelcomeMessage = 'Привет!\nДля декодинга аудио файла просто пришли его мне!'


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, botWelcomeMessage)


@bot.message_handler(content_types=['audio'])
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
        except Exception as exp:
            print(exp)

        bot.reply_to(message, 'Downloaded!')

        y, sr = librosa.load(audio_path, sr=11025)
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        downloaded_audio = Tonal_Fragment(y_harmonic, sr, tend=22)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        print(tempo)
        likely_key, alt_key = downloaded_audio.print_key()

        if alt_key is not None:
            bot.reply_to(message, f'Song key: {likely_key}\n Maybe it can be a: {alt_key}')
        else:
            bot.reply_to(message, f'Song key:{likely_key}')
    except Exception as e:
        bot.reply_to(message, e)


if __name__ == '__main__':
    bot.infinity_polling()