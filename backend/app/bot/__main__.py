"""Run the bot with long polling: python -m app.bot

Production runs it the same way as its own service (deploy/docker-compose.yml): polling needs
no public webhook endpoint, and the same process sends the daily reminders and tidies the
market (expired handovers).
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from app.bot.handlers import router
from app.config import get_settings
from app.i18n import SUPPORTED_LANGUAGES, t
from app.market import market_loop
from app.reminders import reminder_loop


async def configure(bot: Bot) -> None:
    settings = get_settings()
    for lang in SUPPORTED_LANGUAGES:
        commands = [
            BotCommand(command="start", description=t("cmd_start", lang)),
            BotCommand(command="help", description=t("cmd_help", lang)),
        ]
        await bot.set_my_commands(commands, language_code=lang)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description=t("cmd_start", "uz")),
            BotCommand(command="help", description=t("cmd_help", "uz")),
        ]
    )
    if settings.webapp_url.startswith("https://"):
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Ekoustoz", web_app=WebAppInfo(url=settings.webapp_url)
            )
        )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not set. Put it in the .env file (see .env.example).")
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await configure(bot)
    background = [
        asyncio.create_task(reminder_loop(bot)),
        # Expired market handovers and loose photo uploads.
        asyncio.create_task(market_loop(bot)),
    ]
    try:
        await dispatcher.start_polling(bot)
    finally:
        for task in background:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
