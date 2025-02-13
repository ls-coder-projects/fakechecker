import asyncio

import aiojobs
import orjson
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from app import utils
from app.handlers.messages import router as messages_router
from app.web_handlers.tg_updates import tg_updates_app


# Настройка главного меню команды
async def setup_bot_main_menu(bot: Bot) -> None:
    main_menu_commands = [
        BotCommand(command="/info", description="Что я умею?"),
    ]

    await bot.set_my_commands(main_menu_commands)


# Настройка обработчиков
def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(messages_router)


# Настройка aiogram
async def setup_aiogram(dp: Dispatcher) -> None:
    setup_handlers(dp)


async def aiohttp_on_startup(app: web.Application) -> None:
    dp: Dispatcher = app["dp"]
    workflow_data = {"app": app, "dispatcher": dp}
    if "bot" in app:
        workflow_data["bot"] = app["bot"]
    await dp.emit_startup(**workflow_data)


async def aiohttp_on_shutdown(app: web.Application) -> None:
    dp: Dispatcher = app["dp"]
    for i in [app, *app._subapps]:  # dirty
        if "scheduler" in i:
            scheduler: aiojobs.Scheduler = i["scheduler"]
            scheduler._closed = True
    workflow_data = {"app": app, "dispatcher": dp}
    if "bot" in app:
        workflow_data["bot"] = app["bot"]
    await dp.emit_shutdown(**workflow_data)


# Настройка polling
async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await setup_aiogram(dispatcher)
    await setup_bot_main_menu(bot)


# Закрытие сессии polling
async def aiogram_on_shutdown_polling(bot: Bot) -> None:
    await bot.session.close()


# Настройка aiohttp
async def setup_aiohttp_app(bot: Bot, dp: Dispatcher) -> web.Application:
    scheduler = aiojobs.Scheduler()
    app = web.Application()

    subapps: list[tuple[str, web.Application]] = [
        ("/tg/webhooks/", tg_updates_app),
    ]

    for prefix, subapp in subapps:
        subapp["bot"] = bot
        subapp["dp"] = dp
        subapp["scheduler"] = scheduler
        app.add_subapp(prefix, subapp)
    app["bot"] = bot
    app["dp"] = dp
    app["scheduler"] = scheduler
    app.on_startup.append(aiohttp_on_startup)
    app.on_shutdown.append(aiohttp_on_shutdown)
    return app


# Закрытие сессии
async def close_sessions(session: AsyncSession):
    await session.close()


def main() -> None:
    # nnew
    logger = structlog.get_logger()  # Создайте логгер
    session = utils.smart_session.SmartAiogramAiohttpSession(
        logger=logger,  # Передайте логгер
        json_loads=orjson.loads,  # Если это все еще нужно
    )

    # Создание бота
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    dp = Dispatcher()
    dp.startup.register(aiogram_on_startup_polling)
    dp.shutdown.register(aiogram_on_shutdown_polling)
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
