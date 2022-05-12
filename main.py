import telebot
from keyfinder import *

token = 'mytoken'
botWelcomeMessage = 'Привет!\nДля декодинга аудио файла просто пришли его мне!'


bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, botWelcomeMessage)


@bot.message_handler(content_types=['audio'])
def handle_audio_file(message):
    try:
        chat_id = message.chat.id
        file_info = bot.get_file(message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        src = "C:/Users/svsergeev/PycharmProjects/musicBotTG/received/" + message.audio.file_name

        try:
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)
        except Exception as exp:
            print(exp)

        bot.reply_to(message, 'Downloaded!')
        y, sr = librosa.load(src)
        print('librosa.load')
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        print('librosa.effects')
        downloaded_audio = Tonal_Fragment(y_harmonic, sr, tend=22)
        print('Tonal Fragment')
        print(downloaded_audio.print_key())

    except Exception as e:
        bot.reply_to(message, e)


if __name__ == '__main__':
    bot.infinity_polling()



