import logging
from contextlib import suppress

from aiogram import Router, Bot, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ContentType
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.database.functions.users import get_all_departments, get_departments, get_department, add_department, \
    delete_department
from tgbot.keyboards.inline import (cancel_keyboard, raw_confirming_keyboard,
                                    make_departments_id_keyboard, department_menu_keyboard)
from tgbot.keyboards.reply import admin_menu
from tgbot.misc.cbdata import MainCallbackFactory
from tgbot.misc.states import DepartmentStates

superuser_router = Router()


# Add a new department to database
@superuser_router.message(commands=["add_department"])
async def ask_department_title(message: Message, state: FSMContext):
    """  Ask the user for input the title of the department  """
    await state.clear()
    await message.answer("<b>Siz yangi bo'lim qo'shmoqchisiz!</b>\n", reply_markup=ReplyKeyboardRemove())
    first_message = await message.answer("Yangi bo'limning nomini kiriting:", reply_markup=cancel_keyboard)
    await state.update_data(first_message_id=first_message.message_id)
    await state.set_state(DepartmentStates.asking_title)


@superuser_router.message(content_types=ContentType.TEXT, state=DepartmentStates.asking_title)
async def ask_department_description(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    """  Ask the user for input the description of the department  """
    await message.delete()
    state_data = await state.get_data()
    department_title = message.text.strip()
    existing_departments = [title[1] for title in await get_all_departments(session)]
    if department_title.lower() in existing_departments:
        text = "<b><u>Bunday bo'lim avval qo'shilgan!</u></b>\n\n<b>Mavjud bo'limlar:</b>\n"
        for title in existing_departments:
            text += f"{title.capitalize()}\n"
        await bot.delete_message(chat_id=message.chat.id, message_id=state_data["first_message_id"])
        await message.answer(text, reply_markup=admin_menu)
        await state.clear()
    else:
        department_text = f"<b>Yangi bo'lim:</b>\n<i>Nomi</i> - {department_title}\n"
        await bot.edit_message_text(text=department_text, chat_id=message.chat.id,
                                    message_id=state_data["first_message_id"])
        second_message = await message.answer("Yangi bo'limga tavsif bering:", reply_markup=cancel_keyboard)
        await state.update_data(department_title=department_title.lower(), department_text=department_text,
                                second_message_id=second_message.message_id)
        await state.set_state(DepartmentStates.asking_description)


@superuser_router.message(content_types=ContentType.TEXT, state=DepartmentStates.asking_description)
async def ask_department_photo(message: Message, bot: Bot, state: FSMContext):
    """  Ask the user for send the photo of the department  """
    await message.delete()
    state_data = await state.get_data()
    department_description = message.text.strip()
    department_text = state_data["department_text"] + f"<i>Tavsifi</i> - {department_description}"
    await bot.edit_message_text(text=department_text, chat_id=message.chat.id,
                                message_id=state_data["first_message_id"])
    await bot.edit_message_text(text="Yangi bo'limga bo'lgan talablar haqida tasvir yuboring:", chat_id=message.chat.id,
                                message_id=state_data["second_message_id"], reply_markup=cancel_keyboard)
    await state.update_data(department_description=department_description, department_text=department_text)
    await state.set_state(DepartmentStates.asking_photo)


@superuser_router.message(content_types=ContentType.PHOTO, state=DepartmentStates.asking_photo)
async def ask_for_confirmation(message: Message, state: FSMContext, bot: Bot):
    """  Ask the user is he really going to add this department  """
    await message.delete()
    state_data = await state.get_data()
    department_photo_id = message.photo[-1].file_id
    department_text = state_data["department_text"]
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=state_data["second_message_id"])
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=state_data["first_message_id"])
    first_message = await message.answer_photo(photo=department_photo_id, caption=department_text)
    second_message = await message.answer("Yangi bo'lim qo'shishni tasdiqlaysizmi?",
                                          reply_markup=raw_confirming_keyboard)
    await state.update_data(first_message_id=first_message.message_id, second_message_id=second_message.message_id,
                            department_photo_id=department_photo_id)
    await state.set_state(DepartmentStates.waiting_for_confirmation)


@superuser_router.callback_query(text="yes", state=DepartmentStates.waiting_for_confirmation)
async def add_new_department(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    """  Add the new department to database  """
    state_data = await state.get_data()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["second_message_id"])
    await add_department(session, title=state_data["department_title"],
                         description=state_data["department_description"],
                         photo_id=state_data["department_photo_id"])
    await call.message.answer("Yangi bo'lim qo'shildi\U0001F389")
    await state.clear()


@superuser_router.callback_query(text="no", state=DepartmentStates.waiting_for_confirmation)
@superuser_router.callback_query(text="home", state=DepartmentStates)
async def cancel_adding_department(call: CallbackQuery, state: FSMContext, bot: Bot):
    """  Cancel adding a new department and go home  """
    state_data = await state.get_data()
    with suppress(KeyError):
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["first_message_id"])
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["second_message_id"])
    await call.message.answer("<b>Yangi bo'lim qo'shish bekor qilindi!</b>",
                              reply_markup=admin_menu)
    await state.clear()


# Get all existing departments from database
@superuser_router.message(commands=["get_departments"])
async def show_departments(message: Message, state: FSMContext, session: AsyncSession):
    existing_departments = await get_departments(session, limit=10)
    await message.answer("<b>Soha bo'limlari ro'yxati:</b>", reply_markup=ReplyKeyboardRemove())
    if not existing_departments:
        await message.answer("<u><b>Mavjud bo'limlar yo'q!</b></u>")
        return
    text = str()
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    keyboard_data = await make_departments_id_keyboard(session)
    departments_message = await message.answer(text, reply_markup=keyboard_data[0])
    await state.update_data(departments_message_id=departments_message.message_id, first_button_id=keyboard_data[1],
                            last_button_id=keyboard_data[2])
    await state.set_state(DepartmentStates.showing_departments_list)


# Show next list of departments when user taps to next button
@superuser_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "next"),
                                 state=DepartmentStates.showing_departments_list)
async def next_departments_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    keyboard_data = await make_departments_id_keyboard(session, start=state_data["last_button_id"] + 1)
    existing_departments = await get_departments(session, start=state_data["last_button_id"] + 1)
    text = f"<b>Barcha mavjud bo'limlar:</b>\n"
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    await bot.edit_message_text(text, chat_id=call.message.chat.id,
                                message_id=state_data["departments_message_id"], reply_markup=keyboard_data[0])
    await state.update_data(first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])


# Show previous list of departments when user taps to previous button
@superuser_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "previous"),
                                 state=DepartmentStates.showing_departments_list)
async def previous_departments_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    keyboard_data = await make_departments_id_keyboard(session, end=state_data["first_button_id"] - 1)
    existing_departments = await get_departments(session, end=state_data["first_button_id"] - 1)
    text = f"<b>Barcha mavjud bo'limlar:</b>\n"
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    await bot.edit_message_text(text, chat_id=call.message.chat.id,
                                message_id=state_data["departments_message_id"], reply_markup=keyboard_data[0])
    await state.update_data(first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])


# Open selected department and show additional data about it
@superuser_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "open"),
                                 state=DepartmentStates.showing_departments_list)
async def open_department(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                          callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    department_id = callback_data.data
    department_data = await get_department(session, department_id)
    text = f"<b>ID:</b> {department_id}\n<b>Nomi:</b> {department_data[0].capitalize()}\n" \
           f"<b>Tavsifi:</b> {department_data[1]}"
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["departments_message_id"])
    departments_message = await call.message.answer_photo(photo=department_data[2], caption=text,
                                                          reply_markup=department_menu_keyboard)
    await state.update_data(departments_message_id=departments_message.message_id, department_id=department_id,
                            department_title=department_data[0])
    await state.set_state(DepartmentStates.showing_department)


# Ask user for confirm deleting selected department
@superuser_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "delete"),
                                 state=DepartmentStates.showing_department)
async def start_deleting_department(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=1)  # Simple anti-flood
    await call.message.edit_reply_markup()
    text = "Siz rosdan ham bu bo'limni <u>o'chirmoqchimisiz</u>?"
    confirming_message = await call.message.answer(text, reply_markup=raw_confirming_keyboard)
    await state.update_data(confirming_message_id=confirming_message.message_id)
    await state.set_state(DepartmentStates.deleting_department)


# Cancel deleting department
@superuser_router.callback_query(text="no", state=DepartmentStates.deleting_department)
async def cancel_deleting_department(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["confirming_message_id"])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["departments_message_id"])
    await state.clear()
    existing_departments = await get_departments(session, limit=10, start=state_data["first_button_id"])
    text = f"<b>Barcha mavjud bo'limlar:</b>\n"
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    keyboard_data = await make_departments_id_keyboard(session, start=state_data["first_button_id"])
    departments_message = await call.message.answer(text, reply_markup=keyboard_data[0])
    await state.update_data(departments_message_id=departments_message.message_id, first_button_id=keyboard_data[1],
                            last_button_id=keyboard_data[2])
    await state.set_state(DepartmentStates.showing_departments_list)


# Deleting selected department
@superuser_router.callback_query(text="yes", state=DepartmentStates.deleting_department)
async def complete_deleting_department(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    await delete_department(session, department_id=state_data["department_id"])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["confirming_message_id"])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["departments_message_id"])
    await call.message.answer(
        f"<u><b>\"{state_data['department_title'].capitalize()}\" bo'limi ma'lumotlar bazasidan o'chirildi!</b></u>")
    await state.clear()
    existing_departments = await get_departments(session, limit=10)
    text = f"<b>Barcha mavjud bo'limlar:</b>\n"
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    keyboard_data = await make_departments_id_keyboard(session)
    departments_message = await call.message.answer(text, reply_markup=keyboard_data[0])
    await state.update_data(departments_message_id=departments_message.message_id, last_button_id=keyboard_data[2])
    await state.set_state(DepartmentStates.showing_departments_list)


# Go back to the departments list
@superuser_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "back"),
                                 state=DepartmentStates.showing_department)
async def back_to_departments_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    existing_departments = await get_departments(session, limit=10, start=state_data["first_button_id"])
    text = f"<b>Barcha mavjud bo'limlar:</b>\n"
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    keyboard_data = await make_departments_id_keyboard(session, start=state_data["first_button_id"])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["departments_message_id"])
    departments_message = await call.message.answer(text, reply_markup=keyboard_data[0])
    await state.update_data(departments_message_id=departments_message.message_id, first_button_id=keyboard_data[1],
                            last_button_id=keyboard_data[2])
    await state.set_state(DepartmentStates.showing_departments_list)


# Delete all messages about departments and go home
@superuser_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "home"),
                                 state=DepartmentStates)
async def go_home(call: CallbackQuery, bot: Bot, state: FSMContext):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["departments_message_id"])
    await call.message.answer("<b>Asosiy menu!</b>",
                              reply_markup=admin_menu)
    await state.clear()
