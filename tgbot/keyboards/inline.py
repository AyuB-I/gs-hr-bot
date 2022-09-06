import logging
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.database.functions.users import get_all_departments, get_departments
from tgbot.misc.cbdata import MainCallbackFactory

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

confirming_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U00002714", callback_data="yes"),  # Emoji "heavy_check_mark"
            InlineKeyboardButton(text="\U0000274C", callback_data="no")  # Emoji "x"
        ],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data="back"),  # Emoji "arrow_left"
            InlineKeyboardButton(text="\U0001F3E0", callback_data="home")  # Emoji "house"
        ]
    ]
)

fill_form_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Davom etish", callback_data="fill_form")],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data="back"),  # Emoji "arrow_left"
            InlineKeyboardButton(text="\U0001F3E0", callback_data="home")  # Emoji "house"
        ]
    ]
)

living_conditions_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001F3E2 Dom", callback_data=MainCallbackFactory(
                category="living_conditions", data="flat").pack())
        ],
        [
            InlineKeyboardButton(text="\U0001F3E0 Hovli", callback_data=MainCallbackFactory(
                category="living_conditions", data="house").pack())
        ],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data=MainCallbackFactory(
                category="living_conditions", data="back").pack()),  # Emoji "arrow_left"
            InlineKeyboardButton(text="\U0001F3E0", callback_data=MainCallbackFactory(
                category="living_conditions", data="home").pack())  # Emoji "house"
        ]
    ],

)

educations_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="O'rta", callback_data=MainCallbackFactory(
            category="educations", data="secondary").pack())],
        [InlineKeyboardButton(text="O'rta maxsus", callback_data=MainCallbackFactory(
                category="educations", data="secondary_special").pack())],
        [InlineKeyboardButton(text="Oliy | Bakalavr", callback_data=MainCallbackFactory(
                category="educations", data="bachelor").pack())],
        [InlineKeyboardButton(text="Oliy | Magistr", callback_data=MainCallbackFactory(
                category="educations", data="master").pack())],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data=MainCallbackFactory(
                category="educations", data="back").pack()),  # Emoji "arrow_left"
            InlineKeyboardButton(text="\U0001F3E0", callback_data=MainCallbackFactory(
                category="educations", data="home").pack())  # Emoji "house"
        ]
    ]
)

department_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0000274C",
                                 callback_data=MainCallbackFactory(category="departments", action="delete").pack())
        ],
        [
            InlineKeyboardButton(text="\U00002B05",
                                 callback_data=MainCallbackFactory(category="departments", action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",
                                 callback_data=MainCallbackFactory(category="departments", action="home").pack())
        ]
    ]
)


marital_status_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Turmush qurgan", callback_data=MainCallbackFactory(category="marital_status",
                                                                                       data="married").pack())],
        [InlineKeyboardButton(text="Turmush qurmagan", callback_data=MainCallbackFactory(category="marital_status",
                                                                                         data="not_married").pack())],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data="back"),  # Emoji "arrow_left"
            InlineKeyboardButton(text="\U0001F3E0", callback_data="home")  # Emoji "house"
        ]
    ]
)


async def make_confirming_keyboard(category: str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="\U00002795",  # Emoji 'heavy_plus_sign'
                                  callback_data=MainCallbackFactory(category=category, data="add").pack())],
            [
                InlineKeyboardButton(text="\U00002B05",  # Emoji 'arrow_left'
                                     callback_data=MainCallbackFactory(category=category, data="back").pack()),
                InlineKeyboardButton(text="\U000027A1",  # Emoji 'arrow_right'
                                     callback_data=MainCallbackFactory(category=category, data="next").pack()),
            ],
            [InlineKeyboardButton(text="\U0001F3E0",
                                  callback_data=MainCallbackFactory(category=category, data="home").pack())]
        ]
    )
    return keyboard


async def make_departments_keyboard(session: AsyncSession, limit=8, start=1, end=None) -> Optional[
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
    for department_id, title in existing_departments.items():
        builder.row(InlineKeyboardButton(
            text=title.capitalize(),
            callback_data=MainCallbackFactory(category="departments", action="select", data=department_id).pack()))

    if first_button_id != first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(
            text="\U000023EE",
            callback_data=MainCallbackFactory(category="departments", action="previous").pack()))
        builder.add(InlineKeyboardButton(
            text="\U000023ED",
            callback_data=MainCallbackFactory(category="departments", action="next").pack()))
    elif first_button_id == first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(
            text="\U000023ED",
            callback_data=MainCallbackFactory(category="departments", action="next").pack()))
    elif first_button_id != first_department_id and last_button_id == last_department_id:
        builder.row(InlineKeyboardButton(
            text="\U000023EE",
            callback_data=MainCallbackFactory(category="departments", action="previous").pack()))

    builder.row(
        InlineKeyboardButton(
            text="\U00002B05",
            callback_data=MainCallbackFactory(category="departments", action="back").pack()),  # Emoji "arrow_left"
        InlineKeyboardButton(
            text="\U0001F3E0",
            callback_data=MainCallbackFactory(category="departments", action="home").pack())  # Emoji "house"
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
        builder.add(InlineKeyboardButton(text=k, callback_data=MainCallbackFactory(
            category="departments", action="open", data=k).pack()))
    builder.adjust(5)
    if first_button_id != first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(
            text="\U000023EE",
            callback_data=MainCallbackFactory(category="departments", action="previous").pack()))
        builder.add(InlineKeyboardButton(
            text="\U000023ED",
            callback_data=MainCallbackFactory(category="departments", action="next").pack()))
    elif first_button_id == first_department_id and last_button_id != last_department_id:
        builder.row(InlineKeyboardButton(
            text="\U000023ED",
            callback_data=MainCallbackFactory(category="departments", action="next").pack()))
    elif first_button_id != first_department_id and last_button_id == last_department_id:
        builder.row(InlineKeyboardButton(
            text="\U000023EE",
            callback_data=MainCallbackFactory(category="departments", action="previous").pack()))

    builder.row(InlineKeyboardButton(
        text="\U0001F3E0",
        callback_data=MainCallbackFactory(category="departments", action="home").pack()))
    return builder.as_markup(), first_button_id, last_button_id
