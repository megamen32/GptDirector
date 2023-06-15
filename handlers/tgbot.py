import asyncio
import os
import re
import traceback

from aiogram import types
from aiogram.types import InputFile
from openai.error import RateLimitError

from loader import CHATGPT_API_KEY, dp,openai
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
my_session_tokens = ['eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJoZGhmYTEyNEByYW1ibGVyLnJ1IiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXIta3ZrNzRJWGxzWkZxRVZzR3FhMnFwR0hYIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJhdXRoMHw2M2Y1MmYyOWY4M2JkODE2ZTg4NzQ2OGIiLCJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSIsImh0dHBzOi8vb3BlbmFpLm9wZW5haS5hdXRoMGFwcC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNjg2MzEyODQ2LCJleHAiOjE2ODc1MjI0NDYsImF6cCI6IlRkSkljYmUxNldvVEh0Tjk1bnl5d2g1RTR5T282SXRHIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBtb2RlbC5yZWFkIG1vZGVsLnJlcXVlc3Qgb3JnYW5pemF0aW9uLnJlYWQgb3JnYW5pemF0aW9uLndyaXRlIn0.Rmwv55D2gNG--Kmm433y7mbJuVm2V2LNz0nU9bgs_6_JmBNvzZk_PBh7bCPBBrDQIGhlaxf1nqr_PhTKsCYqe7w2CJaSaFdK7_HEpLGIKSetrn4Bpl2BAholzd2dXtLq9B1vacgEwGoTjVyYOZyqLcV3poCXVq5wt8Pii9awDILRnJM3yEdeGys9r7vGOxQEFTlMGOBkpMwwC6hL7l5FQMLimK2ZMDadyyCNeFAOrhIM9Jk99toO_GaDoRPbkRkfEJeacDQ9mt3_ldYsr7VopkIDOjB_aLMdr-bpJzqSVu9cbRRmywr4lbk1YB-rvN3jZzTcQD97npc-088ROE98Aw']
my_session_tokens = reversed(my_session_tokens)

llm = None
cur_token_index = 0
async def chatgpt_request(prompt,gpt3=True):
    if gpt3:
        while True:
            try:
                async with rate_limiter:
                    response = await openai.ChatCompletion.create(
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
            prompt=f'Ты помощник, который переписывает сценарии, упрощая сложные термины и сокращая лишний текст. Помни, что твоя аудитория - дети, которые понимают только русский язык. Твоя задача - сделать сценарий доступным и понятным, не включая лишнюю информацию. Сформулируй ответ так, чтобы он мог быть произнесён за одну минуту. Video transkript:\n"{prompt}"'
        response = llm[cur_token_index](prompt)
        return response



@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Отправьте мне ссылку на видео YouTube Shorts, и я сделаю транскрипцию аудио и переведу сценарий на русский язык, а затем перескажу его молодежно и стильно от лица блогера!")


video_cache={}


@dp.message_handler(content_types=types.ContentType.TEXT, regexp='^(https://youtube\.com/)')
async def process_youtube_shorts(message: types.Message):
    text = message.text.strip()
    msg = await message.reply(text)

    if not text.startswith('https://youtube.com/') and not text.startswith('https://youtu.be/'):
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
            await message.reply_document(InputFile(video_file), caption=gpt_response)
        # Remove the downloaded video file
        os.remove(video_path)
    else:
        await message.reply("Не удалось распознать речь в данном видео.")
