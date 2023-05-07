import os
import tempfile
import youtube_dl
import speech_recognition as sr
from pydub import AudioSegment

import yt_dlp
from langdetect import detect

def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        print(f"Error detecting language: {e}")
        return None

from aiogram.types import InputFile

async def download_video(video_id,message):
    video_path = f"{video_id}.mp4"

    ydl_opts = {
        'format': 'best[ext=mp4][height<=1080][fps<=30]+bestaudio/best[ext=m4a]',
        'outtmpl': video_path,
        'quiet': True,
        'merge_output_format': 'mp4'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])


    with open(video_path, 'rb') as video_file:
        await message.reply_video(video=InputFile(video_file))

    return video_path

def download_audio_and_transcribe(video_id):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
        temp_file_path = 'out.webm'

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": temp_file_path,
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

            audio = AudioSegment.from_file(temp_file_path)
            audio.export("temp.wav", format="wav")

            recognizer = sr.Recognizer()

            with sr.AudioFile("temp.wav") as source:
                audio_data = recognizer.record(source)

            # First, try to recognize speech in English
            try:
                text = recognizer.recognize_google(audio_data, language='en-US', show_all=False)
            except:
                text = recognizer.recognize_google(audio_data, language='ru-RU', show_all=False)

            return text

        except Exception as e:
            print(f"Error downloading and transcribing audio: {e}")
            return None
        finally:
            os.remove(temp_file_path)
            if os.path.exists("temp.wav"):
                os.remove("temp.wav")

