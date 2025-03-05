import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from Private_chat.admin import admin_router
from Private_chat.group import group_router
from Private_chat.worker import worker_router

from DataBase.engine import session_maker, drop_db, create_db
from DataBase.middleware import DataBaseSessionMaker
from Private_chat.client import client_router
from DataBase.orm_query import orm_get_admins, orm_get_workers

bot = Bot(token=os.getenv('TOKEN'),
          default=DefaultBotProperties(parse_mode=ParseMode.HTML)
          )

dp = Dispatcher()
dp.include_router(admin_router)
dp.include_router(worker_router)
dp.include_router(client_router)
dp.include_router(group_router)


param = False
if param:
    asyncio.run(drop_db())
asyncio.run(create_db())


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    bot.admins = [admin.id for admin in await orm_get_admins(session_maker())]
    bot.workers = [worker.id_contact_information for worker in await orm_get_workers(session_maker())]
    # bot.admins = [1263803424]
    dp.update.middleware(DataBaseSessionMaker(session_pool=session_maker))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())
