import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import os

# Введите сюда свой токен бота и ключ RapidAPI
TOKEN = '7414905635:AAHBlef17Zjo0x13nrTCV0X410fiyY1TOKQ'
RAPIDAPI_KEY = '96ca1f6a06mshc27c0509ae6b900p12f032jsn0b08682cf81b'
# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

async def on_startup(dispatcher):
    logging.info("Бот запущен и готов к работе.")

async def on_shutdown(dispatcher):
    logging.info("Бот остановлен.")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на пост в Instagram (Reels), и я скачаю медиа для тебя.")

def download_instagram_media(url: str) -> str:
    api_url = "https://instagram-downloader.p.rapidapi.com/index"
    querystring = {"url": url}

    headers = {
        "x-rapidapi-host": "instagram-downloader.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    response = requests.get(api_url, headers=headers, params=querystring)
    response_json = response.json()
    
    if response.status_code == 200 and 'result' in response_json:
        result = response_json['result']
        if result['is_video']:
            media_url = result['video_url']
        else:
            media_url = result['image_url']
        local_filename = url.split("/")[-2] + (".mp4" if result['is_video'] else ".jpg")
        
        media_response = requests.get(media_url)
        with open(local_filename, 'wb') as f:
            f.write(media_response.content)
        return local_filename
    else:
        raise ValueError("Не удалось получить медиа URL.")

@dp.message_handler()
async def handle_message(message: types.Message):
    url = message.text
    if 'instagram.com/reel/' in url or 'instagram.com/p/' in url:
        try:
            file_path = download_instagram_media(url)
            with open(file_path, 'rb') as file:
                await message.reply_document(file)
            os.remove(file_path)  # Удалить файл после отправки
        except Exception as e:
            await message.reply(f'Произошла ошибка при скачивании медиа: {e}')
    else:
        await message.reply('Пожалуйста, отправьте корректную ссылку на пост в Instagram.')

if name == 'main':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)