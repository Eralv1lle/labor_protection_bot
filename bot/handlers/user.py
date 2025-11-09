from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.keyboards import get_main_menu, get_admin_menu
from bot.utils.formatter import format_user_stats
from bot.utils.uploader import get_backend_stats
import config

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_TELEGRAM_IDS

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    user_id = user.id
    
    welcome_text = f"👋 Добро пожаловать, {user.first_name}!\n\n"
    welcome_text += "Я виртуальный преподаватель по охране труда и промышленной безопасности.\n\n"
    welcome_text += "🚀 <b>Нажмите на кнопку ниже, чтобы открыть Mini App</b> и начать задавать вопросы.\n\n"
    
    if is_admin(user_id):
        welcome_text += "⚡️ <i>У вас есть права администратора</i>"
        keyboard = get_admin_menu()
    else:
        welcome_text += "💡 Задавайте вопросы о требованиях охраны труда, и я предоставлю актуальную информацию из нормативных документов."
        keyboard = get_main_menu()
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = "ℹ️ <b>Помощь</b>\n\n"
    help_text += "<b>Основные команды:</b>\n"
    help_text += "/start - Главное меню\n"
    help_text += "/help - Справка\n\n"
    help_text += "<b>Как пользоваться:</b>\n"
    help_text += "1. Нажмите кнопку '🚀 Открыть Mini App'\n"
    help_text += "2. Введите свой вопрос в чат\n"
    help_text += "3. Получите ответ на основе нормативных документов\n\n"
    
    if is_admin(message.from_user.id):
        help_text += "<b>Команды администратора:</b>\n"
        help_text += "/upload - Загрузить документ\n"
        help_text += "/list - Список документов\n"
        help_text += "/stats - Статистика системы\n"
        help_text += "/rebuild - Обновить индекс\n"
    
    await message.answer(help_text, parse_mode="HTML")

@router.message(F.text == "ℹ️ О боте")
async def about_bot(message: Message):
    about_text = "🤖 <b>О боте</b>\n\n"
    about_text += "Виртуальный преподаватель по охране труда - это интеллектуальный помощник, "
    about_text += "который использует нейросеть GigaChat для консультирования по вопросам охраны труда.\n\n"
    about_text += "<b>Возможности:</b>\n"
    about_text += "✅ Ответы на вопросы по охране труда\n"
    about_text += "✅ Ссылки на нормативные документы\n"
    about_text += "✅ Практические рекомендации\n"
    about_text += "✅ Актуальная информация\n\n"
    about_text += "💡 Используйте Mini App для удобного общения!"
    
    await message.answer(about_text, parse_mode="HTML")

@router.message(F.text == "📊 Моя статистика")
async def my_stats(message: Message):
    try:
        stats_data = await get_backend_stats()
        
        if not stats_data.get('success'):
            await message.answer("❌ Ошибка получения статистики")
            return
        
        db_stats = stats_data.get('database', {})
        top_users = db_stats.get('top_users', [])
        
        user_username = message.from_user.username or f"User {message.from_user.id}"
        user_stats = next((u for u in top_users if u['username'] == user_username), None)
        
        if user_stats:
            stats_text = f"📊 <b>Ваша статистика</b>\n\n"
            stats_text += f"💬 Всего запросов: {user_stats['queries']}\n"
            stats_text += f"📁 Доступно документов: {db_stats.get('total_documents', 0)}\n"
        else:
            stats_text = "📊 У вас пока нет статистики.\n\n"
            stats_text += "Используйте Mini App, чтобы начать задавать вопросы!"
        
        await message.answer(stats_text, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
