from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        if event.message:
            user = event.message.from_user
            text = event.message.text or "[media]"
            logger.info(
                f"Message from {user.id} (@{user.username}): {text[:50]}..."
            )
        elif event.callback_query:
            user = event.callback_query.from_user
            callback_data = event.callback_query.data
            logger.info(
                f"Callback from {user.id} (@{user.username}): {callback_data}"
            )

        return await handler(event, data)
