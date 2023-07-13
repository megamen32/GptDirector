import asyncio
import os
import tempfile
import traceback

import langdetect
import openai
import youtube_dl
import speech_recognition as sr
from aiogram.types import InputFile
from pydub import AudioSegment

import yt_dlp
from langdetect import detect
from yt_dlp import YoutubeDL


def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        print(f"Error detecting language: {e}")
        return None





async def download_video(url, message):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            video_path = temp_file.name
            ydl_opts = {
                  "format": "bestvideo+bestaudio/best",
                "outtmpl": video_path + ".%(ext)s",
                "postprocessors": [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                "quiet": True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                audio_extension = info_dict.get("ext", "mp4")
                temp_file_path_with_extension = video_path + "." + 'mp4'
                if os.path.exists(temp_file_path_with_extension):
                    pass
                else:
                    temp_file_path_with_extension = video_path + "." + audio_extension
            try:
                await message.reply_document(InputFile(temp_file_path_with_extension))
            except:
                traceback.print_exc()
            return temp_file_path_with_extension
    except:
        traceback.print_exc()
        return None





import requests
from bs4 import BeautifulSoup

def get_video_description(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    description_element = soup.find("title")
    description = description_element.text.strip() if description_element else ""
    return description

def download_audio_and_transcribe(url):
    global model
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        temp_file_path = temp_file.name

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": temp_file_path + ".%(ext)s",
            "quiet": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                audio_extension = info_dict.get("ext", "webm")
                temp_file_path_with_extension = temp_file_path + "." + audio_extension
            audio = AudioSegment.from_file(temp_file_path_with_extension)
            # Создаем временный файл для конвертированного в wav аудио
            with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_wav_file:
                audio.export(temp_wav_file.name, format="wav")

                # Используем SpeechRecognition для преобразования аудио в текст
                result = openai.Audio.transcribe('whisper-1', open(temp_wav_file.name, 'rb'))
                text = result["text"]

                return text

        except Exception as e:
            print(f"Error downloading and transcribing audio: {e}")
            return None




