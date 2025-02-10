from aiogram import Router, types, Bot
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from DataBase.orm_query import orm_add_admins, orm_get_admins
from Filters.chat_type import ChatTypeFilter

group_router = Router()
group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))
group_router.edited_message.filter(ChatTypeFilter(['group', 'supergroup']))


@group_router.message(Command('admin'))
async def get_admins(message: types.Message, bot: Bot, session: AsyncSession):
    chat_id = message.chat.id
    admins = await bot.get_chat_administrators(chat_id)
    admins = [member.user.id for member in admins if member.status == 'creator' or member.status == 'administrator']
    await message.delete()
    for id in admins:
        await orm_add_admins(session, id)
        for i in await orm_get_admins(session):
            print(i.id)
        bot.admins = [admin.id for admin in await orm_get_admins(session)]