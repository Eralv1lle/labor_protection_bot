from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text)
async def handle_text(message: Message):
    response = "🤖 Для взаимодействия со мной используйте Mini App.\n\n"
    response += "Нажмите кнопку '🚀 Открыть Mini App' ниже."

    await message.answer(response)