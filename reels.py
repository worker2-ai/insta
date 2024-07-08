import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

# Введите сюда свой токен бота и ключ RapidAPI
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


async def on_startup(dispatcher):
    logging.info("Бот запущен и готов к работе.")


async def on_shutdown(dispatcher):
    logging.info("Бот остановлен.")


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply(
        "Привет! Отправь мне ссылку на пост в Instagram (Reels), и я скачаю медиа для тебя."
    )


async def download_instagram_media(url: str) -> str:
    api_url = "https://instagram-downloader.p.rapidapi.com/index"
    querystring = {"url": url}
    headers = {
        "x-rapidapi-host": "instagram-downloader.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, headers=headers, params=querystring) as response:
            response_json = await response.json()

            if response.status == 200 and "result" in response_json:
                result = response_json["result"]
                media_url = result["video_url"] if result["is_video"] else result["image_url"]
                local_filename = (
                    url.split("/")[-2] + (".mp4" if result["is_video"] else ".jpg")
                )

                async with session.get(media_url) as media_response:
                    with open(local_filename, "wb") as f:
                        f.write(await media_response.read())

                return local_filename
            else:
                raise ValueError("Не удалось получить медиа URL.")


@dp.message_handler()
async def handle_message(message: types.Message):
    url = message.text

    if "instagram.com/reel/" in url or "instagram.com/p/" in url:
        try:
            file_path = await download_instagram_media(url)
            with open(file_path, "rb") as file:
                await message.reply_document(file)
            os.remove(file_path)  # Удалить файл после отправки
        except Exception as e:
            logging.error(f"Ошибка при скачивании медиа: {e}")
            await message.reply(
                f"Произошла ошибка при скачивании медиа. Попробуйте позже."
            )
    else:
        await message.reply("Пожалуйста, отправьте корректную ссылку на пост в Instagram.")


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
