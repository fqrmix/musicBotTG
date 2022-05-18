from __future__ import unicode_literals
from dataclasses import replace
import yt_dlp
from definitions import ROOT_DIR


ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': ROOT_DIR + '/tmp/%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
}
def get_audio_from_video(url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        mp3_path = filename.replace('.webm', '.mp3')
    return mp3_path
