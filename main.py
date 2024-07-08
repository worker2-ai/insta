import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # Для хранения состояний
from aiogram.dispatcher.filters.state import StatesGroup, State  # Для работы с состояниями
from aiogram.dispatcher import FSMContext  # Для управления состояниями

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
class LoggingMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        logging.info(f"Получено сообщение: {message.text}")

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

# Функция для скачивания медиа из Instagram (без изменений)
async def download_instagram_media(url: str) -> str | None:
    # ... (тот же код, что и раньше)

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
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
