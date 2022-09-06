import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from tgbot.config import load_config, Config
from tgbot.handlers.superuser import superuser_router
from tgbot.handlers.admin import admin_router
from tgbot.handlers.echo import echo_router
from tgbot.handlers.new_user import new_user_router
from tgbot.middlewares.config import ConfigMiddleware
from tgbot.middlewares.database import DbSessionMiddleware
from tgbot.misc.default_commands import setup_default_commands
from tgbot.services import broadcaster
from tgbot.database.models.base import Base
from tgbot.database.functions.setup import create_session_pool

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, config: Config):
    admin_ids = config.tg_bot.admin_ids
    await setup_default_commands(bot)
    await broadcaster.broadcast(bot, admin_ids, "Bot Started!")


async def on_shutdown(db: Base):
    logger.info("Dropping tables!")
    Base.metadata.drop_all()
    logger.info("TABLES DROPPED!")


def register_global_middlewares(dp: Dispatcher, config, session_pool):
    dp.message.outer_middleware(ConfigMiddleware(config))
    dp.callback_query.outer_middleware(ConfigMiddleware(config))
    dp.message.middleware(DbSessionMiddleware(session_pool=session_pool))
    dp.callback_query.middleware(DbSessionMiddleware(session_pool=session_pool))


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot!")
    config = load_config(".env")

    storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)
    session_pool = await create_session_pool(db=config.db)

    for router in [
        superuser_router,
        admin_router,
        new_user_router,
        echo_router
    ]:
        dp.include_router(router)

    register_global_middlewares(dp, config, session_pool)

    try:
        await on_startup(bot, config)
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("The bot has been disabled!")

