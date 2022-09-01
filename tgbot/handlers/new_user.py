import logging
from contextlib import suppress

from aiogram import Router, Bot, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ContentType

from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards.inline import (home_keyboard, menu_control_keyboard, raw_confirming_keyboard,
                                    make_departments_keyboard, fill_form_keyboard, living_conditions_keyboard,
                                    educations_keyboard, confirming_keyboard, make_confirming_keyboard,
                                    marital_status_keyboard)
from tgbot.keyboards.reply import user_menu, admin_menu
from tgbot.database.functions.users import add_user, get_department
from tgbot.database.models.models import Users
from tgbot.misc.states import NewUserStates
from tgbot.config import Config
from tgbot.misc.cbdata import MainCallbackFactory

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
    await call.message.answer("<b>Ro'yhatdan o'tish bekor qilindi!</b>",
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
        text="<b>Siz bilan bog'lanishimiz mumkin bo'lgan telefon raqamni kiriting.</b>\n(+998997219090)",
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
                                      "(+998997219090)", reply_markup=menu_control_keyboard)


@new_user_router.callback_query(text_contains="yes", state=NewUserStates.q3_phonenum)
async def ask_q4(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    """  Ask user for direction of department  """
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"<b>Telefon raqam:</b> {state_data['phonenum']}\n"
    keyboard_data = await make_departments_keyboard(session)
    if not keyboard_data:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
        await call.message.edit_text("<u><b>Xozircha ishga olish uchun mavjud bo'limlar yo'q!</b></u>",
                                     reply_markup=user_menu)
        return
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                message_id=state_data["form_message_id"])
    await call.message.edit_text("<b>Ishlamoqchi bo'lgan sohangizga mos bo'limni tanlang:</b>",
                                 reply_markup=keyboard_data[0])
    await state.update_data(form_text=form_text, first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])
    await state.set_state(NewUserStates.q4_department)


# Show next list of departments when user taps to next button
@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "next"),
                                state=NewUserStates.q4_department)
async def next_departments_list(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    keyboard_data = await make_departments_keyboard(session, start=state_data["last_button_id"] + 1)
    await call.message.edit_text("<b>Ishlamoqchi bo'lgan sohangizga mos bo'limni tanlang:</b>",
                                 reply_markup=keyboard_data[0])
    await state.update_data(first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])


# Show previous list of departments when user taps to previous button
@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "previous"),
                                state=NewUserStates.q4_department)
async def previous_departments_list(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    keyboard_data = await make_departments_keyboard(session, end=state_data["first_button_id"] - 1)
    await call.message.edit_text("<b>Ishlamoqchi bo'lgan sohangizga mos bo'limni tanlang:</b>",
                                 reply_markup=keyboard_data[0])
    await state.update_data(first_button_id=keyboard_data[1], last_button_id=keyboard_data[2])


@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "departments" and F.action == "select"),
                                state=NewUserStates.q4_department)
async def show_department_requirements(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                                       callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)  # Simple anti-flood
    selected_department = await get_department(session, department_id=callback_data.data)
    state_data = await state.get_data()

    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["question_message_id"])
    department_message = await call.message.answer_photo(
        photo=selected_department[2],
        caption=f"<b>{selected_department[0].capitalize()} bo'limi</b>\n{selected_department[1]}"
    )
    question_message = await call.message.answer(
        "<b>Siz tanlagan bo'lim hodimlari yuqorida ko'rsatilgan talablarga javob berishi kerak.</b>",
        reply_markup=fill_form_keyboard
    )
    await state.update_data(department_message_id=department_message.message_id, department=selected_department[0],
                            question_message_id=question_message.message_id, department_id=callback_data.data)
    await state.set_state(NewUserStates.confirming_department)


@new_user_router.callback_query(text="fill_form", state=NewUserStates.confirming_department)
async def ask_q5(call: CallbackQuery, bot: Bot, state: FSMContext):
    await call.answer(cache_time=1)  # Simple anti-flood
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"<b>Bo'lim:</b> {state_data['department'].capitalize()}\n"
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["department_message_id"])
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await call.message.edit_text("<b>Doimiy yashash manzilingizni kiriting.</b>\n(Alisher Navoiy ko'chasi 158 uy)",
                                 reply_markup=menu_control_keyboard)
    await state.update_data(form_text=form_text)
    await state.set_state(NewUserStates.q5_address)


@new_user_router.message(F.text, state=NewUserStates.q5_address)
async def ask_q6(message: Message, bot: Bot, state: FSMContext):
    await message.delete()
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"<b>Yashash manzil:</b> {message.text}\n"
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Yashash sharoitingiz:</b>", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=living_conditions_keyboard)
    await state.update_data(form_text=form_text, address=message.text)
    await state.set_state(NewUserStates.q6_living_conditions)


@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "living_conditions"),
                                state=NewUserStates.q6_living_conditions)
async def ask_q7(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    living_condition_uz = "Dom" if callback_data.data == "flat" else "Hovli"
    form_text = state_data["form_text"] + f"<b>Yashsh shroit:</b> {living_condition_uz}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await call.message.edit_text("<b>Ma'lumotingiz:</b>", reply_markup=educations_keyboard)
    await state.update_data(living_conditions=callback_data.data, form_text=form_text)
    await state.set_state(NewUserStates.q7_education)


@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "educations"),
                                state=NewUserStates.q7_education)
async def ask_q8(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    education_uz = "O'rta"
    if callback_data.data == "secondary_special":
        education_uz = "O'rta maxsus"
    elif callback_data.data == "bachelor":
        education_uz = "Oliy | Bakalavr"
    elif callback_data.data == "master":
        education_uz = "Oliy | Magistr"
    form_text = state_data["form_text"] + f"<b>Ma'lumot:</b> {education_uz}\n"
    keyboard = await make_confirming_keyboard(category="universities")
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await call.message.edit_text(text="<b>Biron bir o'quv yurtini tamomlaganmisiz?</b>\n",
                                 reply_markup=keyboard)
    await state.update_data(education=callback_data.data, form_text=form_text)
    await state.set_state(NewUserStates.q8_university)


@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "universities"),
                                state=NewUserStates.q8_university)
async def ask_university_name_or_q9(call: CallbackQuery, bot: Bot, state: FSMContext,
                                    callback_data: MainCallbackFactory):
    state_data = await state.get_data()
    if callback_data.data == "add":
        form_text = state_data["form_text"] + f"<b>O'quv yurti: </b>"
        await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                    message_id=state_data["form_message_id"])
        question_message = await call.message.edit_text(
            "<b>Qaysi o'quv yurtini tamomlagansiz?</b>\n(Qo'qon Universiteti)",
            reply_markup=menu_control_keyboard)
        await state.set_state(NewUserStates.university_name)
        await state.update_data(question_message_id=question_message.message_id, form_text=form_text, universities=[])

    else:
        try:
            universities = state_data["universities"]
        except KeyError:
            universities = None
        if not universities:  # If there isn't added universities
            form_text = state_data["form_text"] + "<b>O'quv yurti: </b>\U00002796\n"  # Emoji 'heavy_minus_sign'
            await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                        message_id=state_data["form_message_id"])
            await state.update_data(universities=[], form_text=form_text)

        keyboard = await make_confirming_keyboard(category="worked_companies")
        await call.message.edit_text("<b>Avval biron bir korxona yoki tashkilotda ishlaganmisiz?</b>",
                                     reply_markup=keyboard)
        await state.set_state(NewUserStates.q9_worked_companies)


@new_user_router.message(F.text, state=NewUserStates.university_name)
async def ask_university_direction(message: Message, bot: Bot, state: FSMContext):
    state_data = await state.get_data()
    university_name = message.text.strip()
    form_text = state_data["form_text"] + f"\n    <b>Nomi:</b> {university_name}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Qaysi yo'nalishida o'qigansiz?</b>\n(Moliya)", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=menu_control_keyboard)
    await state.update_data(form_text=form_text, university_name=university_name)
    await state.set_state(NewUserStates.university_direction)


@new_user_router.message(F.text, state=NewUserStates.university_direction)
async def ask_university_finished_year(message: Message, bot: Bot, state: FSMContext):
    state_data = await state.get_data()
    university_direction = message.text.strip()
    form_text = state_data["form_text"] + f"    <b>Yo'nalishi:</b> {university_direction}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text("<b>Qachon tamomlagansiz?</b>\n(2018)", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=menu_control_keyboard)
    await state.update_data(form_text=form_text, university_direction=university_direction)
    await state.set_state(NewUserStates.university_finished_year)


@new_user_router.message(F.text.regexp(r"^[1, 2][9, 0]\d\d$"), state=NewUserStates.university_finished_year)
async def ask_again_q8(message: Message, bot: Bot, state: FSMContext):
    state_data = await state.get_data()
    university_finished_year = message.text
    university_data = {"name": state_data["university_name"], "direction": state_data["university_direction"],
                       "finished_year": university_finished_year}
    universities = state_data["universities"]
    universities.append(university_data)
    logging.info(universities)
    form_text = state_data["form_text"] + f"    <b>Tamomlagan yili:</b> {university_finished_year}\n"
    keyboard = await make_confirming_keyboard(category="universities")
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Yana biron bir o'quv yurtini tamomlaganmisiz?</b>\n",
                                chat_id=message.chat.id, message_id=state_data["question_message_id"],
                                reply_markup=keyboard)
    await state.update_data(form_text=form_text, universities=universities)
    await state.set_state(NewUserStates.q8_university)


@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "worked_companies"),
                                state=NewUserStates.q9_worked_companies)
async def ask_company_name_or_q10(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    state_data = await state.get_data()
    if callback_data.data == "add":
        form_text = state_data["form_text"] + f"<b>Sobiq korxona: </b>"
        await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                    message_id=state_data["form_message_id"])
        question_message = await call.message.edit_text(
            "<b>Ishlagan korxonangizning nomi nima?</b>\n(General Sport)",
            reply_markup=menu_control_keyboard)
        await state.set_state(NewUserStates.company_name)
        await state.update_data(question_message_id=question_message.message_id, form_text=form_text, companies=[])

    else:
        try:
            companies = state_data["companies"]
        except KeyError:
            companies = None
        if not companies:  # If there isn't added universities
            form_text = state_data["form_text"] + "<b>Sobiq korxona: </b>\U00002796\n"  # Emoji 'heavy_minus_sign'
            await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                        message_id=state_data["form_message_id"])
            await state.update_data(companies=[], form_text=form_text)

        keyboard = await make_confirming_keyboard(category="trips")
        await call.message.edit_text("<b>Chet elga sayohat qilganmisiz?</b>",
                                     reply_markup=keyboard)
        await state.set_state(NewUserStates.q10_trip)


@new_user_router.message(F.text, state=NewUserStates.company_name)
async def ask_company_position(message: Message, bot: Bot, state: FSMContext):
    state_data = await state.get_data()
    company_name = message.text.strip()
    form_text = state_data["form_text"] + f"\n    <b>Nomi:</b> {company_name}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Qaysi lavozimda ishlagansiz?</b>\n(Buxgalter)", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=menu_control_keyboard)
    await state.update_data(form_text=form_text, company_name=company_name)
    await state.set_state(NewUserStates.company_position)


@new_user_router.message(F.text, state=NewUserStates.company_position)
async def ask_company_working_period(message: Message, bot: Bot, state: FSMContext):
    state_data = await state.get_data()
    company_position = message.text.strip()
    form_text = state_data["form_text"] + f"    <b>Lavozimi:</b> {company_position}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text("<b>Qachon ishga kirgansiz va qachon ishdan ketgansiz?</b>\n(2018 - 2021)",
                                chat_id=message.chat.id, message_id=state_data["question_message_id"],
                                reply_markup=menu_control_keyboard)
    await state.update_data(form_text=form_text, company_position=company_position)
    await state.set_state(NewUserStates.company_working_period)


@new_user_router.message(F.text.regexp(r"^[1, 2][9, 0]\d\d - [1, 2][9, 0]\d\d$"),
                         state=NewUserStates.company_working_period)
async def ask_company_leaving_reason(message: Message, bot: Bot, state: FSMContext):
    state_data = await state.get_data()
    company_working_period = message.text
    form_text = state_data["form_text"] + f"    <b>Ishlash davri:</b> {message.text}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Nima sababdan ishdan ketgansiz?</b>",
                                chat_id=message.chat.id, message_id=state_data["question_message_id"],
                                reply_markup=menu_control_keyboard)
    await state.update_data(form_text=form_text, company_working_period=company_working_period)
    await state.set_state(NewUserStates.company_leaving_reason)


@new_user_router.message(F.text, state=NewUserStates.company_leaving_reason)
async def ask_again_q9(message: Message, bot: Bot, state: FSMContext):
    state_data = await state.get_data()
    company_leaving_reason = message.text
    company_data = {"name": state_data["company_name"], "position": state_data["company_position"],
                    "working_period": state_data["company_working_period"], "leaving_reason": company_leaving_reason}
    companies = state_data["companies"]
    companies.append(company_data)
    form_text = state_data["form_text"] + f"    <b>Ketish sababi:</b> {company_leaving_reason}\n"
    keyboard = await make_confirming_keyboard(category="worked_companies")
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Yana biron bir korxona yoki tashkilotda ishlaganmisiz?</b>",
                                chat_id=message.chat.id, message_id=state_data["question_message_id"],
                                reply_markup=keyboard)
    await state.update_data(form_text=form_text, companies=companies)
    await state.set_state(NewUserStates.q9_worked_companies)


@new_user_router.callback_query(MainCallbackFactory.filter(F.category == "trips"),
                                state=NewUserStates.q10_trip)
async def ask_trip_country_or_q11(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    state_data = await state.get_data()
    if callback_data.data == "add":
        form_text = state_data["form_text"] + f"<b>Sayohat: </b>"
        await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                    message_id=state_data["form_message_id"])
        question_message = await call.message.edit_text(
            "<b>Qaysi davlatga sayohat qilgansiz?</b>\n(Germaniya)",
            reply_markup=menu_control_keyboard)
        await state.set_state(NewUserStates.company_name)
        await state.update_data(question_message_id=question_message.message_id, form_text=form_text, trips=[])

    else:
        try:
            trips = state_data["trips"]
        except KeyError:
            trips = None
        if not trips:  # If there isn't added universities
            form_text = state_data["form_text"] + "<b>Sayohat: </b>\U00002796\n"  # Emoji 'heavy_minus_sign'
            await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                        message_id=state_data["form_message_id"])
            await state.update_data(companies=[], form_text=form_text)

        await call.message.edit_text("<b>Oilaviy ahvolingiz:</b>",
                                     reply_markup=marital_status_keyboard)
        await state.set_state(NewUserStates.q10_trip)


@new_user_router.message(F.text, state=NewUserStates.trip_country)
async def ask_trip_country(message: Message, bot: Bot, state: FSMContext):
    """  Ask where the user has traveled  """
    state_data = await state.get_data()
    trip_country = message.text.strip()
    form_text = state_data["form_text"] + f"\n    <b>Davlat:</b> {trip_country}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Nima sababdan chet elga chiqqansiz?</b>", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=menu_control_keyboard)
    await state.update_data(form_text=form_text, trip_country=trip_country)
    await state.set_state(NewUserStates.trip_reason)
