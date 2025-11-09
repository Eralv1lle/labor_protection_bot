from datetime import datetime
from typing import Dict, List

def format_statistics(stats: Dict) -> str:
    if not stats.get('success'):
        return "❌ Ошибка получения статистики"
    
    db_stats = stats.get('database', {})
    emb_stats = stats.get('embeddings', {})
    
    message = "📊 <b>Статистика системы</b>\n\n"
    
    message += "📁 <b>Документы:</b>\n"
    message += f"├ Загружено: {db_stats.get('total_documents', 0)}\n"
    message += f"├ Уникальных в индексе: {emb_stats.get('unique_documents', 0)}\n"
    message += f"└ Всего чанков: {emb_stats.get('total_chunks', 0)}\n\n"
    
    message += "👥 <b>Пользователи:</b>\n"
    message += f"├ Всего: {db_stats.get('total_users', 0)}\n"
    message += f"└ Всего запросов: {db_stats.get('total_queries', 0)}\n\n"
    
    top_users = db_stats.get('top_users', [])
    if top_users:
        message += "🏆 <b>Топ пользователей:</b>\n"
        for i, user in enumerate(top_users[:5], 1):
            message += f"{i}. {user['username']}: {user['queries']} запросов\n"
        message += "\n"
    
    recent_users = db_stats.get('recent_users', [])
    if recent_users:
        message += "🕐 <b>Последняя активность:</b>\n"
        for user in recent_users[:3]:
            message += f"├ {user['username']}\n"
            message += f"└ {user['last_active']}\n"
    
    return message

def format_documents_list(documents: List[Dict]) -> str:
    if not documents:
        return "📁 Документы не загружены"
    
    message = f"📁 <b>Загруженные документы ({len(documents)}):</b>\n\n"
    
    for i, doc in enumerate(documents, 1):
        message += f"{i}. <b>{doc['filename']}</b>\n"
        message += f"├ Страниц: {doc.get('pages_count', 'N/A')}\n"
        message += f"├ Размер текста: {doc.get('content_length', 0):,} символов\n"
        message += f"└ Загружен: {doc['upload_date']}\n\n"
    
    return message

def format_document_info(doc: Dict) -> str:
    message = f"📄 <b>{doc['filename']}</b>\n\n"
    message += f"🆔 ID: {doc['id']}\n"
    message += f"📄 Страниц: {doc.get('pages_count', 'N/A')}\n"
    message += f"📏 Символов: {doc.get('content_length', 0):,}\n"
    message += f"📅 Загружен: {doc['upload_date']}\n"
    
    return message

def format_user_stats(stats: Dict, username: str) -> str:
    message = f"📊 <b>Статистика пользователя {username}</b>\n\n"
    message += f"💬 Всего запросов: {stats.get('queries_count', 0)}\n"
    message += f"🕐 Последний запрос: {stats.get('last_request_at', 'Нет данных')}\n"
    
    return message

def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
