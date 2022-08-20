import logging
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.database.functions.users import get_all_departments, get_departments
from tgbot.misc.cbdata import DepartmentsCallbackFactory


async def make_departments_keyboard(session: AsyncSession, limit=3, start=1, end=None) -> Optional[
    tuple[InlineKeyboardMarkup, int, int]
]:
    builder = InlineKeyboardBuilder()
    all_departments = await get_all_departments(session)
    logging.info(end)
    try:
        first_department_id = all_departments[0][0]
        last_department_id = all_departments[-1][0]
    except IndexError:
        return
    existing_departments = {k: v for k, v in await get_departments(session, limit=limit, start=start, end=end)}
    logging.info(f"{existing_departments=}")
    first_button_id = list(existing_departments)[0]
    last_button_id = list(existing_departments)[-1]
    for department_id, title in existing_departments.items():
        builder.row(InlineKeyboardButton(
            text=title.capitalize(),
            callback_data=DepartmentsCallbackFactory(action="select", department_id=department_id).pack()))

    if first_button_id != first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(text="\U000023EE",
                                         callback_data=DepartmentsCallbackFactory(action="previous").pack()))
        builder.add(InlineKeyboardButton(text="\U000023ED",
                                         callback_data=DepartmentsCallbackFactory(action="next").pack()))
    elif first_button_id == first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(text="\U000023ED",
                                         callback_data=DepartmentsCallbackFactory(action="next").pack()))
    elif first_button_id != first_department_id and last_button_id == last_department_id:
        builder.row(InlineKeyboardButton(text="\U000023EE",
                                         callback_data=DepartmentsCallbackFactory(action="previous").pack()))

    builder.row(
        InlineKeyboardButton(text="\U00002B05",
                             callback_data=DepartmentsCallbackFactory(action="back").pack()),  # Emoji "arrow_left"
        InlineKeyboardButton(text="\U0001F3E0",
                             callback_data=DepartmentsCallbackFactory(action="home").pack())  # Emoji "house"
    )
    return builder.as_markup(), first_button_id, last_button_id


async def make_departments_id_keyboard(session: AsyncSession, limit=10, start=1, end=None) -> Optional[
    tuple[InlineKeyboardMarkup, int, int]
]:
    builder = InlineKeyboardBuilder()
    all_departments = await get_all_departments(session)
    try:
        first_department_id = all_departments[0][0]
        last_department_id = all_departments[-1][0]
    except IndexError:
        return
    existing_departments = {k: v for k, v in await get_departments(session, limit=limit, start=start, end=end)}
    first_button_id = list(existing_departments)[0]
    last_button_id = list(existing_departments)[-1]
    for k in existing_departments:
        builder.add(InlineKeyboardButton(text=k, callback_data=DepartmentsCallbackFactory(
            action="open", department_id=k).pack()))
    builder.adjust(5)
    if first_button_id != first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(text="\U000023EE",
                                         callback_data=DepartmentsCallbackFactory(action="previous").pack()))
        builder.add(InlineKeyboardButton(text="\U000023ED",
                                         callback_data=DepartmentsCallbackFactory(action="next").pack()))
    elif first_button_id == first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(text="\U000023ED",
                                         callback_data=DepartmentsCallbackFactory(action="next").pack()))
    elif first_button_id != first_department_id and last_button_id == last_department_id:
        builder.row(InlineKeyboardButton(text="\U000023EE",
                                         callback_data=DepartmentsCallbackFactory(action="previous").pack()))

    builder.row(InlineKeyboardButton(text="\U0001F3E0",
                                     callback_data=DepartmentsCallbackFactory(action="home").pack()))
    return builder.as_markup(), first_button_id, last_button_id


department_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0000274C", callback_data=DepartmentsCallbackFactory(action="delete").pack())
        ],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data=DepartmentsCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0", callback_data=DepartmentsCallbackFactory(action="home").pack())
        ]
    ]
)

home_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F3E0", callback_data="home")]  # Emoji "house"
    ]
)

cancel_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="\U0000274C", callback_data="home")]
    ]
)

menu_control_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U00002B05", callback_data="back"),  # Emoji "arrow_left"
            InlineKeyboardButton(text="\U0001F3E0", callback_data="home")  # Emoji "house"
        ]
    ]
)

raw_confirming_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U00002714", callback_data="yes"),  # Emoji "heavy_check_mark"
            InlineKeyboardButton(text="\U0000274C", callback_data="no")  # Emoji "x"
        ]
    ]
)
