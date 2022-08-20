import logging

from aiogram import Router, Bot, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ContentType

from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards.inline import home_keyboard, menu_control_keyboard, raw_confirming_keyboard, \
    make_departments_keyboard
from tgbot.keyboards.reply import user_menu, admin_menu
from tgbot.database.functions.users import add_user, get_departments
from tgbot.database.models.models import Users
from tgbot.misc.states import NewUserStates
from tgbot.config import Config
from tgbot.misc.cbdata import DepartmentsCallbackFactory

new_user_router = Router()


@new_user_router.callback_query(text_contains="home", state=NewUserStates)
async def cancel_form(call: CallbackQuery, state: FSMContext, bot: Bot, config: Config):
    """  Cancel form filling and back to home menu  """
    await call.answer(cache_time=30)  # It's a simple anti-flood
    # config: Config = call.bot.get("config")
    admin_ids = config.tg_bot.admin_ids
    current_state = await state.get_state()
    state_data = await state.get_data()
    if current_state != "NewUserStates:q1_name" and current_state != "NewUserStates:ready_form":
        await bot.delete_message(call.message.chat.id, state_data["question_message_id"])

    await bot.delete_message(call.message.chat.id, state_data["form_message_id"])
    await bot.delete_message(call.message.chat.id, state_data["anketa_text_message_id"])
    await call.message.answer("Ro'yhatdan o'tish bekor qilindi!",
                              reply_markup=admin_menu if call.from_user.id in admin_ids else user_menu)
    await state.clear()


@new_user_router.message(commands=["start"])
async def user_start(message: Message, state: FSMContext, session: AsyncSession):
    """  Great the user  """
    await state.clear()
    # Checking for user in database, if not exists adding to database
    user = await session.get(Users, message.from_user.id)
    if not user:
        await add_user(session=session, telegram_id=message.from_user.id, username=message.from_user.username,
                       telegram_name=message.from_user.full_name)
    await message.answer(
        f"<b>Assalamu Alaykum</b> {message.from_user.full_name}<b>!</b>\n"
        f"\"General Sport\" jamoasining hodimlarni boshqarish botiga xush kelibsiz!",
        reply_markup=user_menu)


@new_user_router.message(commands=["help"])
async def command_help(message: Message):
    """  Send help message to user  """
    await message.answer("Har qanday yuzaga kelgan xato, taklif va mulohazalaringizni botni ishlab chiqaruvchisi "
                         "@AyuB_Ismailoff'ga yuboring!\n"
                         "Bizning xizmatlarimizdan foydalanayotganingizdan minnatdormiz :)")


@new_user_router.message(text="\U0001f4dd Ro'yhatdan o'tish")
async def ask_q1(message: Message, state: FSMContext):
    """  Start form filling and ask user's name  """
    anketa_text_message = await message.answer("Anketa:", reply_markup=ReplyKeyboardRemove())
    form_message = await message.answer("<b>Ism va familiyangizni to'liq kiriting.</b>\n(Ahmadjon Ahmedov)",
                                        reply_markup=home_keyboard)
    await state.update_data(form_message_id=form_message.message_id,
                            anketa_text_message_id=anketa_text_message.message_id)
    await state.set_state(NewUserStates.q1_name)


@new_user_router.message(content_types=ContentType.TEXT, state=NewUserStates.q1_name)
async def ask_q2(message: Message, state: FSMContext, bot: Bot):
    """  Ask the user's birthday  """
    await message.delete()
    full_name = message.text
    form_text = f"<b>Ism va Familiya:</b> {full_name}\n"
    state_data = await state.get_data()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id,
                                message_id=state_data["form_message_id"])
    question_message = await message.answer("<b>Tug'ulgan sanangizni kiriting.</b>\n(24.03.1998)",
                                            reply_markup=menu_control_keyboard)
    await state.update_data(full_name=full_name, form_text=form_text, question_message_id=question_message.message_id)
    await state.set_state(NewUserStates.q2_birth_date)


@new_user_router.message(
    F.text.regexp(r"\s?(?:0?[1-9]|[12][0-9]|3[01])[-\.](?:0?[1-9]|1[012])[-\.](?:19[6-9]\d|200[0-9])\.?$"),
    state=NewUserStates.q2_birth_date)
async def ask_q3(message: Message, state: FSMContext, bot: Bot):
    """  Ask the user for phone number  """
    await message.delete()
    state_data = await state.get_data()
    text = state_data["form_text"] + f"<b>Tug'ilgan sana:</b> {message.text}\n"
    await bot.edit_message_text(text=text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>Siz bilan bog'lanishimiz mumkin bo'lgan telefon raqamni kiriting.</b>\n(+998916830071)",
        chat_id=message.chat.id, message_id=state_data["question_message_id"], reply_markup=menu_control_keyboard)
    await state.update_data(birthday=message.text, form_text=text)
    await state.set_state(NewUserStates.q3_phonenum)


@new_user_router.message(F.text.regexp(r"\+998[0-9]{9}$"), state=NewUserStates.q3_phonenum)
@new_user_router.message(content_types=ContentType.CONTACT, state=NewUserStates.q3_phonenum)
async def confirm_q3(message: Message, state: FSMContext, bot: Bot):
    """  Ask user to confirm that the phone number was correct  """
    await message.delete()
    phonenum = message.text
    state_data = await state.get_data()
    await bot.edit_message_text(text=f"<b>Raqamni to'g'ri terdingizmi?</b>\n{phonenum}",
                                chat_id=message.chat.id, message_id=state_data["question_message_id"],
                                reply_markup=raw_confirming_keyboard)
    await state.update_data(phonenum=phonenum)


@new_user_router.callback_query(text_contains="no", state=NewUserStates.q3_phonenum)
async def callback_no(call: CallbackQuery):
    """  Ask again user's phone number if previous was incorrect  """
    await call.answer(cache_time=1)  # Simple anti-flood
    await call.message.edit_text(text="<b>Siz bilan bog'lanishimiz mumkin bo'lgan telefon raqamni kiriting.</b>\n"
                                      "(+998916830071)", reply_markup=menu_control_keyboard)


@new_user_router.callback_query(text_contains="yes", state=NewUserStates.q3_phonenum)
async def ask_q4(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    """  Ask user for direction of department  """
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"<b>Telefon raqam:</b> {state_data['phonenum']}\n"
    keyboard_data = await make_departments_keyboard(session)
    if not keyboard_data:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
        await call.message.edit_text("<u><b>Xozircha ishga olish uchun mavjud bo'limlar yo'q!</b></u>\n"
                                         "Mavjud bo'lishi bilan sizga xabar beramiz.", reply_markup=user_menu)
        return
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                message_id=state_data["form_message_id"])
    await call.message.edit_text("<b>Ishlamoqchi bo'lgan sohangizga mos bo'limni tanlang.</b>",
                                 reply_markup=keyboard_data[0])
    await state.update_data(form_text=form_text, first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])
    await state.set_state(NewUserStates.q4_department)


# Show next list of departments when user taps to next button
@new_user_router.callback_query(DepartmentsCallbackFactory.filter(F.action == "next"),
                                state=NewUserStates.q4_department)
async def next_departments_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    keyboard_data = await make_departments_keyboard(session, start=state_data["last_button_id"] + 1)
    existing_departments = await get_departments(session, start=state_data["last_button_id"] + 1, limit=3)
    logging.info(f"first_button_id={keyboard_data[1]}")
    text = f"<b>Barcha mavjud bo'limlar:</b>\n"
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    await bot.edit_message_text(text, chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=keyboard_data[0])
    await state.update_data(first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])


# Show previous list of departments when user taps to previous button
@new_user_router.callback_query(DepartmentsCallbackFactory.filter(F.action == "previous"),
                                state=NewUserStates.q4_department)
async def previous_departments_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    keyboard_data = await make_departments_keyboard(session, end=state_data["first_button_id"] - 1)
    existing_departments = await get_departments(session, end=state_data["first_button_id"] - 1, limit=3)
    logging.info(f"first_button_id={state_data['first_button_id']}")
    text = f"<b>Barcha mavjud sohalar:</b>\n"
    for department_id, title in existing_departments:
        text += f"{department_id}. {title.capitalize()}\n"
    await bot.edit_message_text(text, chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=keyboard_data[0])
    await state.update_data(first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])


@new_user_router.callback_query(text_startswith="department_", state=NewUserStates.q4_department)
async def show_department_requirements(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    pass
