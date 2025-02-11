
import re

from aiogram import Router, F, types, Bot
from aiogram.filters import StateFilter, Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from Common.client_inf import ClientInformation, OrderService, FeedbackDesc
from Common.paginator import get_keyboards, Pagination
from DataBase.orm_query import orm_add_contact_information, orm_add_client, \
    orm_update_ci_fn, orm_update_ci_sn, orm_update_ci_patr, orm_update_ci_mail, orm_update_ci_phone, orm_get_all_tos, \
    orm_get_services, orm_add_awaiting, orm_get_awaitings_for_client, orm_get_service, orm_get_finished_for_clients, \
    orm_add_feedback, orm_get_feedback, orm_delete_feedback, orm_get_feedback_one, orm_update_feedback
from Filters.chat_type import ChatTypeFilter
from Keyboards.inline import get_inline_kb

client_router = Router()
client_router.message.filter(ChatTypeFilter(['private']))

# ------------------------------------КЛАВИАТУРЫ------------------------------------------------------------------------

PHONE_KB = ReplyKeyboardBuilder()
PHONE_KB.add(KeyboardButton(text='Отправить номер телефона от телеграма', request_contact=True))
REREGISTERKB = get_inline_kb(
    btns={
        'Имя': 'ReReg_FName_',
        'Фамилия': 'ReReg_SName_',
        'Отчество': 'ReReg_Patronymic_',
        'Почту': 'ReReg_Email_',
        'Номер телефона': 'ReReg_Phone_',
        'Назад◀◀': 'MainMenu_'
    },
    sizes=(3, 2),
)

MAINMENU_KB = get_inline_kb(
    btns={
        'Мои данные': 'ReRegister_',
        'Услуги': 'Services_',
        'Мои заказы': 'MyOrders_',
        'Мои отзывы': 'MyFeedback_',
    }
)

SKIP_PATRONYMIC = get_inline_kb(
    btns={
        'Пропустить': 'patronymic_null'
        }
)

# -----------------------------------ФУНКЦИИ----------------------------------------------------------------------------


def check_phone(phone):
    phone = list(phone)
    if phone[0] == '8':
        phone = ['+', '7', *phone[1:]]
    if phone[0] != '+' or len(phone) != 12:
        return True

    for i in phone[1:]:
        if i not in '0123456789':
            return True
    return False


def check_names(name: str):
    for i in name.lower():
        if i not in 'йцукенгшщзхъфывапролджэячсмитьбю-':
            return True
    return False


def check_email(email: str):
    regex = re.compile(
        r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])"
    )
    if re.fullmatch(regex, email):
        return False
    return True

# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------СТАРТ-И-МЕНЮ-----------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


@client_router.message(Command('start'))
async def start_cmd(message: Message, session: AsyncSession, bot: Bot):
    client = ClientInformation(session, message.from_user.id)
    user = await client.get_user_names()
    try:
        await bot.delete_message(message.chat.id, message.message_id - 1)
    except:
        pass
    await message.delete()
    if user is None:
        await message.answer('Для дальнейшего пользования ботом нужно зарегистрироваться🔽🔽🔽',
                             reply_markup=get_inline_kb(
                                 btns={
                                     'Регистрация': 'registration_'
                                 }
                             ))
    else:
        await message.answer(f'Приветствуем {user[0]} {user[1]}, что хотите сделать?', reply_markup=MAINMENU_KB)


@client_router.callback_query(F.data == 'MainMenu_')
async def main_menu_cmd(callback: types.CallbackQuery, session: AsyncSession):
    client = ClientInformation(session, callback.from_user.id)
    user = await client.get_user_names()
    await callback.message.edit_text(f'Что хотите сделать {user[0]}?', reply_markup=MAINMENU_KB)


# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------FSM-РЕГИСТРАЦИЯ--------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


class FSMReRegistr(StatesGroup):
    firstName = State()
    lastName = State()
    patronymic = State()
    email = State()
    phone = State()


class FSMRegistration(StatesGroup):
    id = State()
    firstName = State()
    lastName = State()
    patronymic = State()
    email = State()
    phone = State()

    fsm_state_desc = {
        'FSMRegistration:firstName': 'Введите заново свое имя:',
        'FSMRegistration:lastName': 'Введите свою фамилию заново:',
        'FSMRegistration:email': 'Введите свой адрес электронной почты еще раз:',
    }

    # Client
    status = State()


@client_router.message(Command('cancel'))
async def cancel_fsm(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    current_state = await state.get_state()
    if current_state is None:
        await message.delete()
        return
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    if await state.get_state() in FSMRegistration:
        await message.answer('Действия отменены\n\nДля дальнейшего пользования ботом нужно зарегистрироваться🔽🔽🔽',
                             reply_markup=get_inline_kb(
                                 btns={
                                     'Регистрация': 'registration_'
                                 }
                             ))
        await state.clear()
    else:
        client = ClientInformation(session, message.from_user.id)
        user = await client.get_user_names()
        await message.answer(f'Действия отменены\n\nЧто хотите сделать {user[0]}?', reply_markup=MAINMENU_KB)
        await state.clear()


@client_router.message(StateFilter(FSMRegistration), Command('back'))
async def back_fsm(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if current_state is None:
        await message.delete()
        return
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    current_state = await state.get_state()

    if current_state == FSMRegistration.firstName:
        await message.answer('Предыдущего шага нет, введите своё имя:')
    else:
        previous_state = None
        for state_fsm in FSMRegistration.__all_states__:
            if state_fsm.state == current_state:
                if previous_state == FSMRegistration.patronymic:
                    await state.set_state(previous_state)
                    await message.answer('Введите своё отчество или пропустите этот этап:', reply_markup=SKIP_PATRONYMIC)
                    return
                await state.set_state(previous_state)
                await message.answer(FSMRegistration.fsm_state_desc[previous_state])

            previous_state = state_fsm


@client_router.callback_query(F.data == 'ReRegister_')
async def re_register_cmd(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    await callback.message.edit_text(
        f'{await ClientInformation(session, callback.from_user.id).get_all_user_inf()}.\nХотите что-то изменить?',
        reply_markup=REREGISTERKB)


@client_router.callback_query(StateFilter(None), or_f(F.data == 'registration_', F.data == 'ReReg_FName_'))
async def start_reg(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text('Введите свое имя:')
    if callback.data == 'ReReg_FName_':
        await state.set_state(FSMReRegistr.firstName)
    else:
        await state.set_state(FSMRegistration.firstName)


@client_router.message(F.text, or_f(FSMRegistration.firstName, FSMReRegistr.firstName))
async def fsm_add_first_name(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if check_names(message.text):
        await bot.delete_message(message.chat.id, message.message_id - 1)
        await message.delete()
        await message.answer('Введите имя на русском без пробелов и спец. символов')
        return
    if await state.get_state() == 'FSMReRegistr:firstName':
        try:
            await orm_update_ci_fn(session, message.from_user.id, message.text.capitalize())
            await bot.delete_message(message.chat.id, message.message_id - 1)
            await message.delete()
            await message.answer(
                f'{await ClientInformation(session, message.from_user.id).get_all_user_inf()}.\nИзменить что-то еще?',
                reply_markup=REREGISTERKB)
            await state.clear()
            return
        except Exception as e:
            await message.answer(f'Ошибка {str(e)}')
            await state.clear()
            return
    else:
        await state.update_data(id=message.from_user.id)
        await state.update_data(firstName=message.text.capitalize())

    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Введите свою фамилию:')
    await state.set_state(FSMRegistration.lastName)


@client_router.message(or_f(FSMRegistration.firstName, FSMReRegistr.firstName))
async def error(message: Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Некорректные данные.\n\nВведите имя:')


@client_router.callback_query(StateFilter(None), F.data == 'ReReg_SName_')
async def rereg_sname(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text('Введите новую фамилию:')
    await state.set_state(FSMReRegistr.lastName)


@client_router.message(or_f(FSMRegistration.lastName, FSMReRegistr.lastName), F.text)
async def fsm_add_second_name(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if check_names(message.text):
        await bot.delete_message(message.chat.id, message.message_id - 1)
        await message.delete()
        await message.answer('Введите фамилию на русском без пробелов и спец. символов')
        return

    if await state.get_state() == 'FSMReRegistr:lastName':
        try:
            await orm_update_ci_sn(session, message.from_user.id, message.text.capitalize())
            await bot.delete_message(message.chat.id, message.message_id - 1)
            await message.delete()
            await message.answer(
                f'{await ClientInformation(session, message.from_user.id).get_all_user_inf()}.\nИзменить что-то еще?',
                reply_markup=REREGISTERKB)
            await state.clear()
            return
        except Exception as e:
            await message.answer(f'Ошибка {str(e)}')
            await state.clear()
            return
    else:
        await state.update_data(lastName=message.text.capitalize())

    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Введите отчество или нажмите "Пропустить" если его нет:', reply_markup=SKIP_PATRONYMIC)

    await state.set_state(FSMRegistration.patronymic)


@client_router.message(or_f(FSMRegistration.lastName, FSMReRegistr.lastName))
async def error(message: Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Некорректные данные.\n\nВведите фамилию:')


@client_router.callback_query(StateFilter(None), F.data == 'ReReg_Patronymic_')
async def rereg_patronymic(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text('Введите отчество или нажмите "Пропустить" если его нет:',
                                     reply_markup=SKIP_PATRONYMIC)
    await state.set_state(FSMReRegistr.patronymic)


@client_router.message(or_f(FSMRegistration.patronymic, FSMReRegistr.patronymic),
                       F.text)
async def fsm_add_patronymic(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if check_names(message.text):
        await bot.delete_message(message.chat.id, message.message_id - 1)
        await message.delete()
        await message.answer('Введите отчество на русском без пробелов и спец. символов, или пропустите этот этап',
                             reply_markup=SKIP_PATRONYMIC)
        return
    if await state.get_state() == 'FSMReRegistr:patronymic':
        try:
            await orm_update_ci_patr(session, message.from_user.id, message.text.capitalize())
            await bot.delete_message(message.chat.id, message.message_id - 1)
            await message.delete()
            await message.answer(
                f'{await ClientInformation(session, message.from_user.id).get_all_user_inf()}.\nИзменить что-то еще?',
                reply_markup=REREGISTERKB)
            await state.clear()
            return
        except Exception as e:
            await message.answer(f'Ошибка {str(e)}')
            await state.clear()
            return
    else:
        await state.update_data(patronymic=message.text.capitalize())

    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Введите адрес электронной почты:')
    await state.set_state(FSMRegistration.email)


@client_router.callback_query(or_f(FSMRegistration.patronymic, FSMReRegistr.patronymic), F.data == 'patronymic_null')
async def fsm_patronymic_null(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    if await state.get_state() == 'FSMReRegistr:patronymic':
        try:
            await orm_update_ci_patr(session, callback.from_user.id, 'NULL')
            await callback.answer()
            await callback.message.edit_text(
                f'{await ClientInformation(session, callback.from_user.id).get_all_user_inf()}.\nИзменить что-то еще?',
                reply_markup=REREGISTERKB)
            await state.clear()
            return
        except Exception as e:
            await callback.message.answer(f'Ошибка {str(e)}')
            await state.clear()
            return
    else:
        await state.update_data(patronymic='NULL')
        await callback.answer()

    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.message.answer('Введите адрес электронной почты:')
    await state.set_state(FSMRegistration.email)


@client_router.message(or_f(FSMRegistration.patronymic, FSMReRegistr.patronymic))
async def error(message: Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Некорректные данные.\n\nВведите отчество или пропустите этот этап',
                         reply_markup=SKIP_PATRONYMIC)


@client_router.callback_query(StateFilter(None), F.data == 'ReReg_Email_')
async def rereg_email(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text('Введите адрес электронной почты:')
    await state.set_state(FSMReRegistr.email)


@client_router.message(or_f(FSMRegistration.email, FSMReRegistr.email), F.text)
async def fsm_add_email(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if check_email(message.text):
        await bot.delete_message(message.chat.id, message.message_id - 1)
        await message.delete()
        await message.answer('Неверный адрес электронной почты!')
        return
    if await state.get_state() == 'FSMReRegistr:email':
        try:
            await orm_update_ci_mail(session, message.from_user.id, message.text)
            await bot.delete_message(message.chat.id, message.message_id - 1)
            await message.delete()
            await message.answer(
                f'{await ClientInformation(session, message.from_user.id).get_all_user_inf()}.\nИзменить что-то еще?',
                reply_markup=REREGISTERKB)
            await state.clear()
            return
        except Exception as e:
            await message.answer(f'Ошибка {str(e)}')
            await state.clear()
            return
    else:
        await state.update_data(email=message.text)

    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Введите номер телефона (Пример: 89526412665):')

    await state.set_state(FSMRegistration.phone)


@client_router.message(or_f(FSMRegistration.email, FSMReRegistr.email))
async def error(message: Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Некорректные данные.\n\nВведите адрес электронной почты:')


@client_router.callback_query(StateFilter(None), F.data == 'ReReg_Phone_')
async def rereg_phone(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)

    await callback.message.answer('Введите номер телефона (Пример: 89526412665):')
    await state.set_state(FSMReRegistr.phone)


@client_router.message(or_f(FSMRegistration.phone, FSMReRegistr.phone), F.text)
async def fsm_add_phone(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if check_phone(message.text):
        await bot.delete_message(message.chat.id, message.message_id - 1)
        await message.delete()
        await message.answer('Неверный номер телефона, напишите номер по шаблону - +70000000000 или 89999999999')
        return
    if await state.get_state() == 'FSMReRegistr:phone':
        try:
            await orm_update_ci_phone(session, message.from_user.id, message.text)
            await bot.delete_message(message.chat.id, message.message_id - 1)
            await message.delete()
            await message.answer(
                f'{await ClientInformation(session, message.from_user.id).get_all_user_inf()}.\nИзменить что-то еще?',
                reply_markup=REREGISTERKB)
            await state.clear()
            return
        except Exception as e:
            await message.answer(f'Ошибка {str(e)}')
            await state.clear()
            return
    else:
        await state.update_data(phone=message.text)
        data = await state.get_data()
        client = {'id': data['id'], 'status': 'Пользователь'}
        try:
            await orm_add_contact_information(session, data)
            await orm_add_client(session, client)
            await bot.delete_message(message.chat.id, message.message_id - 1)
            await message.delete()
            await message.answer('Вы успешно зарегистрировались! Что хотите сделать?', reply_markup=MAINMENU_KB)
            await state.clear()
        except Exception as e:
            print(e)
            await message.answer(f'Ошибка\n{str(e)}')
            await state.clear()


@client_router.message(FSMRegistration.phone, FSMReRegistr.phone)
async def error(message: Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Некорректные данные.\n\nВведите номер телефона по шаблону - +70000000000 или 89999999999')

# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------Услуги-----------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


@client_router.callback_query(F.data == 'Services_')
async def type_of_serv(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.edit_text('Какой тип услуг вас интересует?',
                                     reply_markup=get_inline_kb(
                                            btns={
                                            tos.name: f'tos_{tos.name}' for tos in await orm_get_all_tos(session)
                                                },
                                                sizes=(1,), row_btn=('Назад','MainMenu_')))


@client_router.callback_query(F.data.startswith('tos_'))
async def start_pagination_services(callback: types.CallbackQuery, session: AsyncSession):
    tos_name = callback.data.split('_')[-1]
    page = 0
    services = await orm_get_services(session, tos_name)
    service = services[page]
    await callback.message.edit_text(f'{service.name}\n\n{service.description}\n\n{service.price}',
                                     reply_markup=
                                     await get_keyboards(
                                         session=session, pref='servUS', page=page,
                                         tos_name=tos_name, back='MainMenu_'))


@client_router.callback_query(Pagination.filter(F.pref == 'servUS'))
async def pagination_services(callback: types.CallbackQuery,callback_data: Pagination, session: AsyncSession):
    tos_name = callback_data.tos_name
    page = callback_data.page
    services = await orm_get_services(session, tos_name)
    service = services[page]
    await callback.message.edit_text(f'{service.name}\n\n{service.description}\n\n{service.price}',
                                     reply_markup=
                                     await get_keyboards(
                                         session=session, pref='servUS', page=page,
                                         tos_name=tos_name, back='MainMenu_'))


@client_router.callback_query(F.data.startswith('toOrder_'))
async def buy_order(callback: types.CallbackQuery, session: AsyncSession):
    id_service = int(callback.data.split('_')[-1])
    id_client = callback.from_user.id
    try:
        await orm_add_awaiting(session, id_client, id_service)
        await callback.answer('Успешно!')
    except Exception as e:
        await callback.message.answer(f'Ошибка!\n\n{e}')


@client_router.callback_query(F.data == 'MyOrders_')
async def my_orders(callback: types.CallbackQuery, session: AsyncSession):
    page = 0
    awaitings = await orm_get_awaitings_for_client(session, callback.from_user.id)
    try:
        await callback.message.edit_text(await OrderService
        (session, awaitings[page].id_services, callback.from_user.id, page)
                                         .get_description_for_client(),
                                         reply_markup=
                                         await
                                         get_keyboards(session=session, pref='ordersUS', page=page,
                                                       id_client=callback.from_user.id, back='MainMenu_'))
    except IndexError:
        await callback.message.edit_text('Активных заказов пока нет, хотите посмотреть завершённые?',
                                         reply_markup=get_inline_kb(
                                             btns={'Завершенные заказы':'UserFinished_',
                                                   'Назад':'MainMenu_'}, sizes=(1,)
                                         ))

# Перехват кастомного callbacka'а
@client_router.callback_query(Pagination.filter(F.pref == 'ordersUS'))
async def pagination_my_orders(callback: types.CallbackQuery,
                               callback_data: Pagination, session: AsyncSession):
    page = callback_data.page
    awaitings = await orm_get_awaitings_for_client(session, callback.from_user.id)
    await callback.message.edit_text(await OrderService
    (session, awaitings[page].id_services, callback.from_user.id, page)
                                     .get_description_for_client(),
                                     reply_markup=await
                                     get_keyboards(session=session, pref='ordersUS', page=page,
                                                id_client=callback.from_user.id, back='MainMenu_'))


@client_router.callback_query(F.data == 'UserFinished_')
async def finished_orders_user(callback: types.CallbackQuery, session: AsyncSession):
    finished = await orm_get_finished_for_clients(session, callback.from_user.id)
    page = 0
    try:
        await callback.message.edit_text(await OrderService(
            session, finished[page].id_services, finished[page].id_client, page, callback.from_user.id).
                                         get_description_for_finished_client(), reply_markup=
        await get_keyboards(session=session, page=page, pref='finiteUS',
                            id_client=callback.from_user.id, back='MainMenu_'))
    except IndexError:
        await callback.message.edit_text('Заказов пока нет.', reply_markup=get_inline_kb(
            btns={'Назад':'MainMenu'}
        ))


@client_router.callback_query(Pagination.filter(F.pref == 'finiteUS'))
async def pagination_finished_orders_user(callback: types.CallbackQuery, callback_data: Pagination,
                                          session: AsyncSession):
    finished = await orm_get_finished_for_clients(session, callback.from_user.id)
    page = callback_data.page
    await callback.message.edit_text(await OrderService(
        session, finished[page].id_services, finished[page].id_client, page, callback.from_user.id).
                                     get_description_for_finished_client(), reply_markup=
        await get_keyboards(session=session, page=page, pref='finiteUS',
                            id_client=callback.from_user.id, back='MainMenu_'))


class FSMFeedback(StatesGroup):
    id_awaiting = State()
    mark = State()
    text = State()

    editinig = None

MARK = get_inline_kb(btns={
'⭐':'1',
'⭐⭐':'2',
'⭐⭐⭐':'3',
'⭐⭐⭐⭐':'4',
'⭐⭐⭐⭐⭐':'5',},sizes=(1,))


@client_router.callback_query(or_f(F.data.startswith('feedback_'), F.data.startswith('editMyFeedback_')),
                              StateFilter(None))
async def start_fsm_feedback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    pref, id_awaiting = callback.data.split('_')
    if pref == 'editMyFeedback':
        FSMFeedback.editinig = await orm_get_feedback_one(session, int(id_awaiting))
        await state.update_data(id_awaiting=FSMFeedback.editinig.id_awaiting)
        await callback.message.edit_text('Оцените нашу работу:', reply_markup=MARK)
    else:
        await state.update_data(id_awaiting=id_awaiting)
        await callback.message.edit_text('Оцените нашу работу:', reply_markup=MARK)
    await state.set_state(FSMFeedback.mark)


@client_router.callback_query(FSMFeedback.mark)
async def feedback_text(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(mark=int(callback.data))
    if FSMFeedback.editinig is not None:
        await callback.message.edit_text(f'Ваш прошлый текст сообщения:\n{FSMFeedback.editinig.text}')
    else:
        await callback.message.edit_text('Напишите, что вам больше всего понравилось или то, чем вы недовольны.')
    await state.set_state(FSMFeedback.text)

@client_router.message(FSMFeedback.mark)
async def error(message: Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Выберите оценку из кнопок ниже:',reply_markup=MARK)


@client_router.message(FSMFeedback.text, F.text)
async def feedback_last_state(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    await state.update_data(text=message.text)
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    data = await state.get_data()
    if FSMFeedback.editinig is not None:
        try:
            await orm_update_feedback(session=session, id_awaiting= FSMFeedback.editinig.id_awaiting, data=data)
            await message.answer('Отзыв успешно изменён!\nЧто-то ещё?', reply_markup=MAINMENU_KB)
            await state.clear()
            FSMFeedback.editinig = None
        except Exception as e:
            await message.answer(f'Ошибка {e}', reply_markup=MAINMENU_KB)
            await state.clear()
            FSMFeedback.editinig = None
    else:
        try:
            await orm_add_feedback(session, data)
            await message.answer('Отзыв успешно отправлен!\nЧто-то ещё?', reply_markup=MAINMENU_KB)
            await state.clear()
        except Exception as e:
            await message.answer(f'Ошибка\n{e}', reply_markup=MAINMENU_KB)
            await state.clear()


@client_router.callback_query(F.data == 'MyFeedback_')
async def my_feedback(callback: types.CallbackQuery, session: AsyncSession):
    page = 0
    awaitings = await orm_get_finished_for_clients(session, callback.from_user.id)
    feedbacks = []
    i = page
    while i != len(awaitings):
        if await orm_get_feedback(session, awaitings[i].id) is not None: feedbacks.append(await orm_get_feedback(session, awaitings[i].id))
        i+= 1
    feedback = feedbacks[page]
    await callback.message.edit_text(await FeedbackDesc(session=session, page=page, id_feedback=feedback.id).get_desc_for_client(),
                                     reply_markup=await get_keyboards(session=session, pref='feedBackUS',page=page,
                                                                      array_feedback=feedbacks, back='MainMenu_'))

@client_router.callback_query(Pagination.filter(F.pref == 'feedBackUS'))
async def pagination_feedback_user(callback: types.CallbackQuery, callback_data: Pagination, session: AsyncSession):
    page = callback_data.page
    awaitings = await orm_get_finished_for_clients(session, callback.from_user.id)
    feedbacks = []
    i = page
    while i != len(awaitings):
        if await orm_get_feedback(session, awaitings[i].id) is not None: feedbacks.append(
            await orm_get_feedback(session, awaitings[i].id))
        i += 1
    feedback = feedbacks[page]
    await callback.message.edit_text(
        await FeedbackDesc(session=session, page=page, id_feedback=feedback.id).get_desc_for_client(),
        reply_markup=await get_keyboards(session=session, pref='feedBackUS', page=page,
                                         array_feedback=feedbacks, back='MainMenu_'))


@client_router.callback_query(F.data.startswith('deleteMyFeedback_'))
async def delete_feedback(callback: types.CallbackQuery, session: AsyncSession):
    try:
        await orm_delete_feedback(session, callback.data.split('_')[-1])
        await callback.message.edit_text(f'Отзыв успешно удален.\n\nЧто хотите сделать?', reply_markup=MAINMENU_KB)
    except Exception as e:
        await callback.message.edit_text(f'Ошибка {e}', reply_markup=MAINMENU_KB)

