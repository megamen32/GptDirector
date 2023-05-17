import asyncio
import functools
import os
import tempfile

from gtts import gTTS
import openai
#import pyttsx3

from loader import dp,bot,openai
from aiogram import types


async def generate_song():
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a creative songwriter."},
            {"role": "assistant", "content": "Напишите песню на русском языке."}],
        temperature=0.8,
        max_tokens=200,
    )
    res = response['choices'][0]['message']['content']

    return res.strip()



async def text_to_speech(text):
    # Преобразование текста в речь и сохранение во временный файл
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        filename = fp.name + ".mp3"
    tts = await asyncio.get_running_loop().run_in_executor(None, functools.partial(gTTS,lang='ru'),text)  # Указать язык текста
    await asyncio.get_running_loop().run_in_executor(None,
                                                     tts.save,(filename))
    return filename


@dp.message_handler(commands=['song'])
async def send_song(message:types.Message):
    msg=await message.reply('Начинаю генерацию песни')
    song_text = await generate_song()
    asyncio.create_task(msg.edit_text(song_text))
    audio_file = await text_to_speech(song_text)
    with open(audio_file, 'rb') as audio:
        await bot.send_audio(message.chat.id, audio,caption=song_text)
        asyncio.create_task( msg.delete())
    os.remove(audio_file)
