import asyncio
import os
import re


from aiogram import types
from aiogram.types import InputFile

from loader import CHATGPT_API_KEY, dp,openai
from transkript import download_video, download_audio_and_transcribe


def check_language(text):
    cyrillic_letters = re.findall('[а-яА-Я]', text)
    if len(cyrillic_letters) > 0:
        return "ru"
    else:
        return "en"


async def chatgpt_request(prompt):
    response=await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are popular blogger that explain scenario in russian language, as it was for children."},
            {"role": "assistant", "content": f'транскрипция видео:"{prompt}"'}],
        temperature=0.8,
        max_tokens=400,
        n=1,
    )
    res = response['choices'][0]['message']['content']

    return res


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Отправьте мне ссылку на видео YouTube Shorts, и я сделаю транскрипцию аудио и переведу сценарий на русский язык, а затем перескажу его молодежно и стильно от лица блогера!")


video_cache={}


@dp.message_handler(content_types=types.ContentType.TEXT, regexp='^(https://youtube\.com/shorts/)')
async def process_youtube_shorts(message: types.Message):
    text = message.text.strip()
    msg = await message.reply(text)

    if not text.startswith('https://youtube.com/shorts/') and not text.startswith('https://youtu.be/'):
        await message.reply("Пожалуйста, отправьте действительную ссылку на видео YouTube Shorts.")
        return

    video_id = text.split('/')[-1].split('?')[0]
    # Check if the video text is already cached
    video_path_task = asyncio.create_task(download_video(video_id,message))

    if text in video_cache:
        transcript_text = video_cache[text]
    else:
        transcript_text =await asyncio.get_running_loop().run_in_executor(None, download_audio_and_transcribe,(video_id))
        if transcript_text:
            video_cache[text] = transcript_text  # Cache the video text
        else:
            await message.reply("Не удалось распознать речь в данном видео.")
            return
    await msg.edit_text(transcript_text)


    if transcript_text:

        prompt = f"Вот транскрипция видео: {transcript_text}. " \
                  "Теперь переведи на русский и перескажи его для детей от лица блогера:"
        gpt_response = await chatgpt_request(transcript_text)
        await msg.edit_text(transcript_text+'\n____\n'+gpt_response)

        video_path= await video_path_task
        # Send video with the generated script
        with open(video_path, 'rb') as video_file:
            await message.reply_video(video=InputFile(video_file), caption=gpt_response)
        # Remove the downloaded video file
        os.remove(video_path)
    else:
        await message.reply("Не удалось распознать речь в данном видео.")
