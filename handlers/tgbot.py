import asyncio
import os
import re
import traceback

import aiogram.utils.markdown
import requests
import yt_dlp
from aiogram import types
from aiogram.types import InputFile
from bs4 import BeautifulSoup
from openai.error import RateLimitError

from loader import CHATGPT_API_KEY, dp, openai
from transkript import download_video, download_audio_and_transcribe


def check_language(text):
    cyrillic_letters = re.findall('[а-яА-Я]', text)
    if len(cyrillic_letters) > 0:
        return "ru"
    else:
        return "en"


from aiolimiter import AsyncLimiter

# Create a rate limiter that allows 3 operations per minute
rate_limiter = AsyncLimiter(3, 60)
# Token is the __Secure-next-auth.session-token from chat.openai.com
my_session_tokens = [
    'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJoZGhmYTEyNEByYW1ibGVyLnJ1IiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXIta3ZrNzRJWGxzWkZxRVZzR3FhMnFwR0hYIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJhdXRoMHw2M2Y1MmYyOWY4M2JkODE2ZTg4NzQ2OGIiLCJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSIsImh0dHBzOi8vb3BlbmFpLm9wZW5haS5hdXRoMGFwcC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNjg2MzEyODQ2LCJleHAiOjE2ODc1MjI0NDYsImF6cCI6IlRkSkljYmUxNldvVEh0Tjk1bnl5d2g1RTR5T282SXRHIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBtb2RlbC5yZWFkIG1vZGVsLnJlcXVlc3Qgb3JnYW5pemF0aW9uLnJlYWQgb3JnYW5pemF0aW9uLndyaXRlIn0.Rmwv55D2gNG--Kmm433y7mbJuVm2V2LNz0nU9bgs_6_JmBNvzZk_PBh7bCPBBrDQIGhlaxf1nqr_PhTKsCYqe7w2CJaSaFdK7_HEpLGIKSetrn4Bpl2BAholzd2dXtLq9B1vacgEwGoTjVyYOZyqLcV3poCXVq5wt8Pii9awDILRnJM3yEdeGys9r7vGOxQEFTlMGOBkpMwwC6hL7l5FQMLimK2ZMDadyyCNeFAOrhIM9Jk99toO_GaDoRPbkRkfEJeacDQ9mt3_ldYsr7VopkIDOjB_aLMdr-bpJzqSVu9cbRRmywr4lbk1YB-rvN3jZzTcQD97npc-088ROE98Aw']
my_session_tokens = reversed(my_session_tokens)

llm = None
cur_token_index = 0


async def chatgpt_request(prompt, gpt3=True):
    if gpt3:
        while True:
            try:
                async with rate_limiter:
                    response = await openai.ChatCompletion.acreate(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": "Ты помощник, который переписывает сценарии, упрощая сложные термины и сокращая лишний текст. Помни, что твоя аудитория - дети, которые понимают только русский язык. Твоя задача - сделать сценарий доступным и понятным, не включая лишнюю информацию. Сформулируй ответ так, чтобы он мог быть произнесён за одну минуту."
                            },
                            {
                                "role": "user",
                                "content": f'транскрипция видео:"{prompt}"'
                            }
                        ],
                        max_tokens=400,  # Уменьшение max_tokens, чтобы соответствовать длине одной минуты речи.
                    )

                    res = response['choices'][0]['message']['content']

                    return res
            except RateLimitError as error:
                traceback.print_exc()
                await asyncio.sleep(20)
                continue
    else:
        from gpt4_openai import GPT4OpenAI
        global llm, cur_token_index
        if llm is None:
            llm = [GPT4OpenAI(token=token, headless=True, model='gpt-4') for token in my_session_tokens]
            # GPT3.5 will answer 8, while GPT4 should be smart enough to answer 10
            prompt = f'Ты помощник, который переписывает сценарии, упрощая сложные термины и сокращая лишний текст. Помни, что твоя аудитория - дети, которые понимают только русский язык. Твоя задача - сделать сценарий доступным и понятным, не включая лишнюю информацию. Сформулируй ответ так, чтобы он мог быть произнесён за одну минуту. Video transkript:\n"{prompt}"'
        response = llm[cur_token_index](prompt)
        return response


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(
        "Привет! Отправьте мне ссылку на видео YouTube Shorts, и я сделаю транскрипцию аудио и переведу сценарий на русский язык, а затем перескажу его молодежно и стильно от лица блогера!")


video_cache = {}

from aiogram.types import InputFile


def find_interesting_word(transcript_text):
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform([transcript_text])

    # получаем отсортированный по важности список ключевых слов
    feature_names = vectorizer.get_feature_names_out()
    keywords = [feature_names[index] for index in X.toarray().argsort()[0][::-1]]

    # выбираем самое длинное и важное ключевое слово для вставки ссылки
    long_keywords = list(filter(lambda x: len(x) > 4, keywords))

    if not long_keywords:
        return keywords[0] if keywords else None  # fallback to the most important word, or None if no words

    return long_keywords[0]  # the most important among long keywords


async def download_and_process_video(url, message,news=False):
    # Проверка поддержки URL
    msg=await message.reply(f'start downloading from {url}')
    ie_list = yt_dlp.extractor.gen_extractor_classes()
    for ie in ie_list:
        if ie.suitable(url):
            break
    else:
        await msg.edit_text("Не могу загрузить это видео. Пожалуйста, отправьте действительную ссылку на видео.")
        return

    video_path_task = asyncio.create_task(download_video(url, message))
    transcript_text = await asyncio.get_running_loop().run_in_executor(None,download_audio_and_transcribe,(url))

    if not transcript_text:
        await msg.edit_text("Не удалось распознать речь в данном видео.")
        return

    msg = await msg.edit_text(transcript_text)
    prompt = f"Вот транскрипция видео: {transcript_text}. " \
             "Теперь переведи на русский и перескажи его для детей от лица блогера:"
    if news:


        interesting_word = find_interesting_word(transcript_text)
        vid_url = extract_video_url(url)
        linked_word = aiogram.utils.markdown.hlink(interesting_word , vid_url)

        # Replace the interesting word in the original transcript.
        gpt_response = transcript_text.replace(interesting_word, linked_word)
        await msg.edit_text(gpt_response,parse_mode='HTML')
    else:

        gpt_response = await chatgpt_request(transcript_text)
        await msg.edit_text(transcript_text + '\n____\n' + gpt_response)

        video_path = await video_path_task
        with open(video_path, 'rb') as video_file:
            await message.reply_document(InputFile(video_file),caption=gpt_response)
        os.remove(video_path)
    return gpt_response
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

def extract_video_url(yappy_url):
    #return yappy_url
    r = requests.get(yappy_url, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    video_tag = soup.find('video')
    return video_tag['src']

@dp.message_handler(regexp=r'^https://yappy\.media/s/.*$')
async def process_yappy_link(message: types.Message):
    yappy_url = message.text.strip()
    await download_and_process_video(yappy_url, message,news=True)


@dp.message_handler(content_types=types.ContentType.TEXT)
async def process_youtube_shorts(message: types.Message):
    text = message.text.strip()
    await download_and_process_video(text, message)