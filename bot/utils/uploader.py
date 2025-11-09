import os
import aiohttp
from aiogram import Bot
from typing import Optional, Dict
import config
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def download_file(bot: Bot, file_id: str, filename: str) -> Optional[str]:
    try:
        file = await bot.get_file(file_id)
        file_path = os.path.join(config.DOCS_DIR, filename)
        
        await bot.download_file(file.file_path, file_path)
        
        return file_path
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

async def upload_document_to_backend(file_path: str) -> Dict:
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=os.path.basename(file_path))
                
                url = f"https://{config.FLASK_HOST}:{config.FLASK_PORT}/admin/upload"
                
                async with session.post(url, data=data) as response:
                    result = await response.json()
                    return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def get_backend_stats() -> Dict:
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            url = f"https://{config.FLASK_HOST}:{config.FLASK_PORT}/api/stats"
            
            async with session.get(url) as response:
                result = await response.json()
                return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def get_backend_documents() -> Dict:
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            url = f"https://{config.FLASK_HOST}:{config.FLASK_PORT}/api/documents"
            
            async with session.get(url) as response:
                result = await response.json()
                return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def delete_backend_document(filename: str) -> Dict:
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            url = f"https://{config.FLASK_HOST}:{config.FLASK_PORT}/admin/delete/{filename}"
            
            async with session.delete(url) as response:
                result = await response.json()
                return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

async def rebuild_backend_index() -> Dict:
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
            url = f"https://{config.FLASK_HOST}:{config.FLASK_PORT}/admin/rebuild"
            
            async with session.post(url) as response:
                result = await response.json()
                return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
