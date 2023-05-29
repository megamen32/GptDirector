import os
import tempfile

import langdetect
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
        'format': 'best[ext=mp4]',
        'outtmpl': video_path,
        'quiet': True,
        'merge_output_format': 'mp4'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])


    with open(video_path, 'rb') as video_file:
        await message.reply_document(InputFile(video_file))

    return video_path

import requests
from bs4 import BeautifulSoup

def get_video_description(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    description_element = soup.find("title")
    description = description_element.text.strip() if description_element else ""
    return description

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
            audio.export(f"{video_id}.wav", format="wav")

            # Используйте SpeechRecognition для преобразования аудио в текст
            import whisper

            model = whisper.load_model("small")
            result = model.transcribe(f"{video_id}.wav")
            text = (result["text"])

            os.remove(f'{video_id}.wav')


            return text

        except Exception as e:
            print(f"Error downloading and transcribing audio: {e}")
            return None
        finally:
            os.remove(temp_file_path)
            if os.path.exists("temp.wav"):
                os.remove("temp.wav")

