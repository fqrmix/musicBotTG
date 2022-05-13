import telebot
from keyfinder import *
from definitions import *

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
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)
        except Exception as exp:
            print(exp)

        bot.reply_to(message, 'Downloaded!')

        if audio_path.endswith('.mp3'):
            mp3_audiopath = src
            wav_audiopath = src.replace('.mp3', '.wav')
            try:
                ffmpeg -i mp3_audiopath wav_audiopath
                print(f'File {mp3_audiopath} was converted to {wav_audiopath}')
            except Exception as e:
                print(e)
            audio_path = wav_audiopath

        y, sr = librosa.load(audio_path)
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        downloaded_audio = Tonal_Fragment(y_harmonic, sr, tend=22)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        print(tempo)
        print(downloaded_audio.print_key())

    except Exception as e:
        bot.reply_to(message, e)


if __name__ == '__main__':
    bot.infinity_polling()



