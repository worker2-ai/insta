import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor

# Замените на ваши реальные токены
TOKEN = '7414905635:AAHBlef17Zjo0x13nrTCV0X410fiyY1TOKQ'
RAPIDAPI_KEY = '96ca1f6a06mshc27c0509ae6b900p12f032jsn0b08682cf81b'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота, хранилища состояний и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Middleware для логирования сообщений
dp.middleware.setup(LoggingMiddleware())

# Состояния бота
class DownloadState(StatesGroup):
    waiting_for_url = State()  # Ожидание ссылки от пользователя

# Обработчики событий запуска и остановки бота
async def on_startup(dispatcher):
    logging.info("Бот запущен и готов к работе.")

async def on_shutdown(dispatcher):
    logging.info("Бот остановлен.")

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Пришли мне ссылку на пост в Instagram (Reels), и я скачаю медиа для тебя.")
    await DownloadState.waiting_for_url.set()  # Устанавливаем состояние ожидания ссылки

# Функция для скачивания медиа из Instagram
async def download_instagram_media(url: str) -> str | None:
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
                local_filename = url.split("/")[-2] + (".mp4" if result["is_video"] else ".jpg")

                async with session.get(media_url) as media_response:
                    with open(local_filename, "wb") as f:
                        f.write(await media_response.read())

                return local_filename
            else:
                raise ValueError("Не удалось получить медиа URL.")

# Обработчик сообщений с ссылками (в состоянии ожидания ссылки)
@dp.message_handler(state=DownloadState.waiting_for_url)
async def handle_message(message: types.Message, state: FSMContext):
    url = message.text

    if "instagram.com/reel/" in url or "instagram.com/p/" in url:
        try:
            file_path = await download_instagram_media(url)
            if file_path:
                with open(file_path, "rb") as file:
                    await message.reply_document(file)
                os.remove(file_path)  # Удаляем файл после отправки
        except Exception as e:
            logging.error(f"Ошибка при скачивании медиа: {e}")
            await message.reply("Произошла ошибка при скачивании. Попробуйте позже.")
    else:
        await message.reply("Пожалуйста, пришлите корректную ссылку на пост в Instagram.")

    await state.finish()  # Завершаем состояние ожидания ссылки

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
