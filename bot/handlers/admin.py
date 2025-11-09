from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards import get_admin_menu, get_document_actions, get_confirm_delete
from bot.utils.uploader import (
    download_file, 
    upload_document_to_backend,
    get_backend_stats,
    get_backend_documents,
    delete_backend_document,
    rebuild_backend_index
)
from bot.utils.formatter import format_statistics, format_documents_list
import config

router = Router()

class UploadStates(StatesGroup):
    waiting_for_file = State()

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_TELEGRAM_IDS

@router.message(Command("upload"))
async def cmd_upload(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await message.answer(
        "📁 <b>Загрузка документа</b>\n\n"
        "Отправьте PDF-файл для добавления в базу знаний.\n\n"
        "Отправьте /cancel для отмены.",
        parse_mode="HTML"
    )
    await state.set_state(UploadStates.waiting_for_file)

@router.message(F.text == "📁 Загрузить документ")
async def btn_upload(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await cmd_upload(message, state)

@router.message(UploadStates.waiting_for_file, F.document)
async def process_document(message: Message, state: FSMContext):
    document = message.document

    if not document.file_name.lower().endswith('.pdf'):
        await message.answer("Пожалуйста, отправьте PDF-файл.\nОтправьте /cancel для отмены.")
        return

    if document.file_size > 50 * 1024 * 1024:
        await message.answer("Файл слишком большой (максимум 50 МБ).\nОтправьте /cancel для отмены.")
        return

    import urllib.parse
    filename = urllib.parse.unquote(document.file_name)

    processing_msg = await message.answer("Загружаю и обрабатываю документ...")

    try:
        file_path = await download_file(message.bot, document.file_id, filename)

        if not file_path:
            await processing_msg.edit_text("Ошибка загрузки файла")
            return

        result = await upload_document_to_backend(file_path)

        if result.get('success'):
            success_text = f"Документ успешно загружен!\n\nФайл: {filename}\n"

            doc_info = result.get('document', {})
            if doc_info:
                success_text += f"Страниц: {doc_info.get('pages_count', 'N/A')}\n"
                success_text += f"Символов: {doc_info.get('content_length', 0):,}\n"

            await processing_msg.edit_text(success_text)
        else:
            error_msg = result.get('error', 'Unknown error')
            await processing_msg.edit_text(f"Ошибка: {error_msg}")

    except Exception as e:
        await processing_msg.edit_text(f"Ошибка: {str(e)}")

    finally:
        await state.clear()

@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять")
        return
    
    await state.clear()
    await message.answer("✅ Операция отменена", reply_markup=get_admin_menu())


@router.message(Command("list"))
async def cmd_list(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return

    try:
        result = await get_backend_documents()

        if not result.get('success'):
            await message.answer("Ошибка получения списка документов")
            return

        documents = result.get('documents', [])

        if not documents:
            await message.answer("Документы не загружены")
            return

        text = f"Загруженные документы ({len(documents)}):\n\n"

        for i, doc in enumerate(documents, 1):
            text += f"{i}. {doc['filename']}\n"
            text += f"Страниц: {doc.get('pages_count', 'N/A')}\n"
            text += f"Символов: {doc.get('content_length', 0):,}\n\n"

        await message.answer(text)

        for doc in documents:
            from bot.keyboards import get_document_actions
            await message.answer(
                f"📄 {doc['filename']}",
                reply_markup=get_document_actions(doc['id'], doc['filename'])
            )

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


@router.message(F.text == "📋 Список документов")
async def btn_list(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора")
        return

    await cmd_list(message)

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    try:
        stats = await get_backend_stats()
        text = format_statistics(stats)
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@router.message(F.text == "📊 Статистика")
async def btn_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await cmd_stats(message)

@router.message(Command("rebuild"))
async def cmd_rebuild(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    processing_msg = await message.answer("⏳ Обновляю индекс...")
    
    try:
        result = await rebuild_backend_index()
        
        if result.get('success'):
            stats = result.get('stats', {})
            text = f"✅ <b>Индекс успешно обновлен!</b>\n\n"
            text += f"📊 Статистика:\n"
            text += f"├ Всего чанков: {stats.get('total_chunks', 0)}\n"
            text += f"├ Векторов: {stats.get('total_vectors', 0)}\n"
            text += f"└ Документов: {stats.get('unique_documents', 0)}\n"
            
            await processing_msg.edit_text(text, parse_mode="HTML")
        else:
            error_msg = result.get('error', 'Unknown error')
            await processing_msg.edit_text(f"❌ Ошибка: {error_msg}")
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Ошибка: {str(e)}")

@router.message(F.text == "🔄 Обновить индекс")
async def btn_rebuild(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await cmd_rebuild(message)


@router.callback_query(F.data.startswith("del:"))
async def callback_delete_doc(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    doc_id = int(callback.data.split(":")[1])

    try:
        result = await get_backend_documents()
        documents = result.get('documents', [])
        doc = next((d for d in documents if d['id'] == doc_id), None)

        if not doc:
            await callback.message.edit_text("Документ не найден")
            await callback.answer()
            return

        from bot.keyboards import get_confirm_delete
        await callback.message.edit_text(
            f"Удалить документ?\n\n{doc['filename']}\n\nЭто действие нельзя отменить",
            reply_markup=get_confirm_delete(doc_id)
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("confirm:"))
async def callback_confirm_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return

    doc_id = int(callback.data.split(":")[1])

    await callback.message.edit_text("Удаляю документ...")

    try:
        result = await get_backend_documents()
        documents = result.get('documents', [])
        doc = next((d for d in documents if d['id'] == doc_id), None)

        if not doc:
            await callback.message.edit_text("Документ не найден")
            await callback.answer()
            return

        filename = doc['filename']
        delete_result = await delete_backend_document(filename)

        if delete_result.get('success'):
            await callback.message.edit_text(f"Документ {filename} успешно удален")
        else:
            error_msg = delete_result.get('error', 'Unknown error')
            await callback.message.edit_text(f"Ошибка: {error_msg}")

    except Exception as e:
        await callback.message.edit_text(f"Ошибка: {str(e)}")

    await callback.answer()


@router.callback_query(F.data == "cancel")
async def callback_cancel_delete(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Отменено")