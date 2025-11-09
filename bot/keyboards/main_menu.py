from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import config

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Открыть Mini App", web_app=WebAppInfo(url=config.MINI_APP_URL))],
            [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="📊 Моя статистика")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Открыть Mini App", web_app=WebAppInfo(url=config.MINI_APP_URL))],
            [KeyboardButton(text="📁 Загрузить документ"), KeyboardButton(text="📋 Список документов")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🔄 Обновить индекс")],
            [KeyboardButton(text="ℹ️ О боте")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_document_actions(doc_id: int, filename: str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🗑 Удалить {filename[:20]}", callback_data=f"del:{doc_id}")],
        ]
    )
    return keyboard

def get_confirm_delete(doc_id: int):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{doc_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
            ]
        ]
    )
    return keyboard