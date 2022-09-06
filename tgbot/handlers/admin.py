import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards.reply import admin_menu
from tgbot.filters.admin import AdminFilter
from tgbot.database.functions.users import add_user
from tgbot.database.models.models import Users


admin_router = Router()
admin_router.message.filter(AdminFilter())


@admin_router.message(AdminFilter(is_admin=True), commands="start", state="*")
async def admin_start(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await session.get(Users, message.from_user.id)
    if not user:
        await add_user(session=session, telegram_id=message.from_user.id, username=message.from_user.username,
                       telegram_name=message.from_user.full_name)
    await message.answer(f"Assalamu Alaykum {message.from_user.full_name}!", reply_markup=admin_menu)
