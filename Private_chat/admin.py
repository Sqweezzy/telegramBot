from aiogram import Router, types, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from Common.client_inf import FeedbackDesc
from Common.paginator import Pagination, get_keyboards
from DataBase.models import Feedback
from DataBase.orm_query import orm_add_tos, orm_get_all_tos, orm_add_service, orm_get_contact_information_id, \
    orm_add_worker, orm_get_worker, orm_get_services, orm_get_service, orm_update_service, orm_delete_service, \
    orm_delete_tos, orm_get_workers, orm_get_clients, orm_delete_ci, orm_delete_client, orm_delete_worker, \
    orm_get_feedbacks
from Filters.chat_type import ChatTypeFilter, IsAdmin
from Keyboards.inline import get_inline_kb

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(['private']))
admin_router.message.filter(IsAdmin())


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------ФУНКЦИИ---------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------

def is_float(varfl):
    try:
        float(varfl)
        return True
    except:
        return False


def is_string(strval: str):
    return any(i.isdecimal() for i in strval)

# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------КЛАВИАТУРЫ------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


ADMIN_KB = get_inline_kb(
    btns={
        'Услуги': 'services_',
        'Исполнители': 'workers_',
        'Клиенты': 'clients_',
        'Добавить услугу': 'AddService_',
        'Добавить исполнителя': 'AddWorker_',
        'Отзывы':'allFeedback'
    },
    sizes=(3, 2),
)

# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------СТАРТ-АДМИН-----------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


@admin_router.message(Command('admin'))
async def admin_start_cmd(message: types.Message, bot: Bot):
    try:
        await bot.delete_message(message.chat.id, message.message_id - 1)
    except:
        pass
    await message.delete()
    await message.answer('Админ-панель:', reply_markup=ADMIN_KB)


@admin_router.callback_query(F.data == 'AdminMenu_')
async def adminc_start_cmd(callback: types.CallbackQuery):
    await callback.message.edit_text('Админ-панель:', reply_markup=ADMIN_KB)

# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------FSM-ДОБАВЛЕНИЕ-УСЛУГ--------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


class NewTOS(StatesGroup):

    name = State()
    description = State()


class NewService(StatesGroup):

    name_types_of_services = State()
    name = State()
    description = State()
    price = State()

    updating = None

    state_desc = {
        'NewService:name': 'Введите название новой услуги:',
        'NewService:price': 'Введите цену услуги:',
    }


@admin_router.message(Command('admcancel'))
async def cancel_fsm(message: types.Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if current_state is None:
        await message.delete()
        return
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Действия отменены.\n\n'
                         'Админ-панель:', reply_markup=ADMIN_KB)
    await state.clear()


@admin_router.message(Command('admback'))
async def back_fsm(message: types.Message, state:  FSMContext, bot: Bot, session: AsyncSession):
    current_state = await state.get_state()
    if current_state is None:
        await message.delete()
        return
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    if current_state in NewTOS.__all_states__:
        if current_state == NewTOS.name:
            await message.answer('Выберите вид услуги:', reply_markup=get_inline_kb(
                                                                    btns={
                                                                        tos.name: f'tos_{tos.name}' for tos in await orm_get_all_tos(session)
                                                                    },
                                                                    row_btn=('Добавить', 'add_tos_'),
                                                                    sizes=(1,)))
            await state.set_state(NewService.name_types_of_services)
        else:
            await message.answer('Введите название нового вида услуг:')
            await state.set_state(NewTOS.name)
    elif current_state in NewService.__all_states__:
        if current_state == NewService.name_types_of_services:
            await message.answer('Предыдущего шага нет.\n\nВыберите вид услуг:',
                                 reply_markup=get_inline_kb(
                                     btns={
                                         tos.name: f'tos_{tos.name}' for tos in await orm_get_all_tos(session)
                                     },
                                     row_btn=('Добавить', 'add_tos_'),
                                     sizes=(1,)))
        else:
            previous = None
            for this_state in NewService.__all_states__:
                if this_state.state == current_state:
                    if previous.state == NewService.name_types_of_services:
                        await message.answer('Выберите вид услуг:',
                                             reply_markup=get_inline_kb(
                                                 btns={
                                                     tos.name: f'tos_{tos.name}' for tos in
                                                     await orm_get_all_tos(session)
                                                 },
                                                 row_btn=('Добавить', 'add_tos_'),
                                                 sizes=(1,)))
                        await state.set_state(previous)
                        return
                    elif previous.state == NewService.description:
                        await message.answer('Введите описание для этого вида услуг или пропустите:',
                                             reply_markup=get_inline_kb(
                                                 btns={
                                                     'Пропустить': 'skip_tos_'
                                                 }
                                             ))
                        await state.set_state(previous)
                        return
                    else:
                        await state.set_state(previous)
                        await message.answer(NewService.state_desc[previous.state])
                previous = this_state
    elif current_state in NewWorker.__all_states__:
        if current_state == NewWorker.id:
            await message.answer('Предыдущего шага нет\n\nВведите ID пользователя:')
        else:
            previous = None
            for this_state in NewWorker.__all_states__:
                if this_state.state == current_state:
                    await state.set_state(previous)
                    await message.answer(NewWorker.state_texts[previous.state])
                previous = this_state


@admin_router.callback_query(StateFilter(None), F.data == 'AddService_')
async def start_add_service(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.message.edit_text('Выберите вид услуги:', reply_markup=get_inline_kb(
                                                                    btns={
                                                                        tos.name: f'tos_{tos.name}' for tos in await orm_get_all_tos(session)
                                                                    },
                                                                    row_btn=('Добавить', 'add_tos_'),
                                                                    sizes=(1,)))
    await state.set_state(NewService.name_types_of_services)


@admin_router.callback_query(NewService.name_types_of_services, F.data == 'add_tos_')
async def add_new_tos(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите название нового вида услуг:')
    await state.set_state(NewTOS.name)


@admin_router.message(NewService.name_types_of_services)
async def error(message: types.Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Некорректные данные.\n\nВведите название нового вида услуг:')


@admin_router.message(NewTOS.name, F.text)
async def add_name_tos(message: types.Message, state: FSMContext, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await state.update_data(name=message.text.capitalize())
    await message.answer('Введите описание для этого вида услуг или пропустите:', reply_markup=get_inline_kb(
                                                                                       btns={
                                                                                        'Пропустить': 'skip_tos_'
                                                                                        }
                                                                                        ))
    await state.set_state(NewTOS.description)


@admin_router.message(NewTOS.description, F.text)
async def add_desc_tos(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await state.update_data(description=message.text.capitalize())
    try:
        data = await state.get_data()
        await orm_add_tos(session, data)
        await message.answer('Успешно\n\n'
                             'Выберите вид услуги', reply_markup=get_inline_kb(
                                                    btns={
                                                        tos.name: f'tos_{tos.name}' for tos in await orm_get_all_tos(session)
                                                    },
                                                    row_btn=('Добавить', 'add_tos_'),
                                                    sizes=(1,)))
        await state.set_state(NewService.name_types_of_services)
    except Exception as e:
        await message.answer(f'Ошибка\n{e}')
        await state.clear()


@admin_router.callback_query(NewTOS.description, F.data == 'skip_tos_')
async def add_nulldesc_tos(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.update_data(description='')
    try:
        data = await state.get_data()
        await orm_add_tos(session, data)
        await callback.message.edit_text('Успешно\n\n'
                             'Выберите вид услуги', reply_markup=get_inline_kb(
                                                    btns={
                                                        tos.name: f'tos_{tos.name}' for tos in await orm_get_all_tos(session)
                                                    },
                                                    row_btn=('Добавить', 'add_tos_'),
                                                    sizes=(1,)))
        await state.set_state(NewService.name_types_of_services)
    except Exception as e:
        await callback.message.answer(f'Ошибка\n{e}')
        await state.clear()


@admin_router.message(NewTOS.description)
async def error(message: types.Message, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await message.answer('Некорректные данные.\n\nВведите описание вида услуг:')


@admin_router.callback_query(StateFilter(None), F.data.startswith('update_'))
async def start_update_serv(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    id_serv = callback.data.split('_')[-1]
    NewService.updating = await orm_get_service(session, int(id_serv))
    await state.update_data(name_typesOfServices=NewService.updating.name_types_of_services)
    await callback.message.edit_text(f'Введите новое названия для этой услуги или напишите * чтобы '
                                     f'оставить этот пункт без изменений')
    await state.set_state(NewService.name)


@admin_router.callback_query(NewService.name_types_of_services, F.data.startswith('tos_'))
async def ns_ntos(callback: types.CallbackQuery, state: FSMContext):
    tos = callback.data.split('_')[-1]
    await callback.message.edit_text(f'Выбранный вид услуг - {tos}\n\nВведите название новой услуги:')
    await state.update_data(name_typesOfServices=tos)
    await state.set_state(NewService.name)


@admin_router.message(NewService.name, F.text)
async def ns_name(message: types.Message, state: FSMContext, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    if message.text == '*' and NewService.updating is not None:
        await state.update_data(name=NewService.updating.name)
    else:
        await state.update_data(name=message.text.capitalize())
    await message.answer('Введите описание для этой услуги или пропустите этот этап:', reply_markup=get_inline_kb(
                                                                                            btns={
                                                                                                'Пропустить': 'skip_sdesc_'
                                                                                            }
                                                                                        ))
    await state.set_state(NewService.description)


@admin_router.message(NewService.description, F.text)
async def ns_desc(message: types.Message, state: FSMContext, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    if message.text == '*' and NewService.updating is not None:
        await state.update_data(description=NewService.updating.description)
    else:
        await state.update_data(description=message.text.capitalize())
    if NewService.updating == None:
        await message.answer(f'Вы ввели такое описание:\n{message.text.capitalize()}\n\nВведите стоимость услуги:')
    else:
        await message.answer(f'Вы ввели такое описание:\n{message.text.capitalize()}\n\nВведите стоимость услуги или '
                             f'напишите * чтобы оставить этот пункт без изменений:')
    await state.set_state(NewService.price)


@admin_router.callback_query(NewService.description, F.data == 'skip_sdesc_')
async def ns_skip_desc(callback: types.CallbackQuery, state: FSMContext):
    if NewService.updating == None:
        await callback.message.edit_text('Введите стоимость услуги:')
    else:
        await callback.message.edit_text(f'Введите стоимость услуги или напишите * чтобы оставить этот '
                                         f'пункт без изменений:')
    await state.update_data(description='')
    await state.set_state(NewService.price)


@admin_router.message(NewService.price, F.text)
async def ns_price(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    if message.text == '*' and NewService.updating is not None:
        await state.update_data(price=NewService.updating.price)
    else:
        if is_float(message.text):
            await state.update_data(price=message.text)
        else:
            await message.answer('Введите корректные данные для цены')
            return
    data = await state.get_data()
    if NewService.updating == None:
        try:
            await orm_add_service(session, data)
            await message.answer('Услуга успешно добавлена\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)
            await state.clear()
        except Exception as e:
            await message.answer(f'Ошибка\n{e}\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)
            await state.clear()
    else:
        try:
            await orm_update_service(session, NewService.updating.id, data)
            await message.answer('Услуга успешно изменена\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)
            NewService.updating = None
            await state.clear()
        except Exception as e:
            await message.answer(f'Ошибка\n{e}\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)
            await state.clear()


@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_service(callback: types.CallbackQuery, session: AsyncSession):
    id_serv = int(callback.data.split('_')[-1])
    try:
        await orm_delete_service(session, id_serv)
        await callback.message.edit_text('Услуга успешно удалена\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)
    except Exception as e:
        await callback.message.edit_text(f'Ошибка\n{e}\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)

# ------------------------------------FSM-ДОБАВЛЕНИЕ-ИСПОЛНИТЕЛЕЙ-------------------------------------------------------


class NewWorker(StatesGroup):
    id = State()
    specialty = State()
    grade = State()

    state_texts = {
        'NewWorker:id': 'Введите ID пользователя:',
        'NewWorker:specialty': 'Введите специальность исполнителя:'
    }


@admin_router.callback_query(StateFilter(None), F.data == 'AddWorker_')
async def nw_add_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите ID пользователя:')
    await state.set_state(NewWorker.id)


@admin_router.message(NewWorker.id, F.text)
async def nw_id(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    user = await orm_get_contact_information_id(session, message.text)
    if user is None:
        await message.answer('Такого пользователя не существует, напишите правильный ID или отмените действие.')
    elif await orm_get_worker(session, message.text) is not None:
        await message.answer('Исполнитель с таким ID уже есть, напишите другой ID или отмените действие.')
    else:
        await state.update_data(id=message.text)
        await message.answer(f'Вы ввели - {message.text}\nЕго имя: {user.firstName}\nФамилия: {user.lastName}\n'
                             f'Отчество: {user.patronymic}\n\nНапишите специальность исполнителя: ')
        await state.set_state(NewWorker.specialty)


@admin_router.message(NewWorker.specialty, F.text)
async def nw_spec(message: types.Message, state: FSMContext, bot: Bot):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await state.update_data(specialty=message.text.capitalize())
    await message.answer(f'Вы ввели - {message.text}\n\nНапишите разряд исполнителся: ')
    await state.set_state(NewWorker.grade)


@admin_router.message(NewWorker.grade, F.text)
async def nw_grade(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    await bot.delete_message(message.chat.id, message.message_id - 1)
    await message.delete()
    await state.update_data(grade=message.text.lower())
    data = await state.get_data()
    try:
        await orm_add_worker(session, data)
        worker = await orm_get_worker(session, data['id'])
        await message.answer(f'Исполнитель: {worker.id_contact_information}\nСпециальность: {worker.specialty}\n'
                             f'Разряд: {worker.grade}\nУспешно добавлен!\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)
        await state.clear()
        bot.workers = [worker.id_contact_information for worker in await orm_get_workers(session)]
    except Exception as e:
        await message.answer(f'Ошибка\n{e}\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)
        await state.clear()


@admin_router.callback_query(F.data == 'delTOS_')
async def delete_tos(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.edit_text('Нажмите на тип услуги который хотите удалить:',
                                     reply_markup=get_inline_kb(btns={
                                            tos.name: f'tosdel_{tos.name}' for tos in await orm_get_all_tos(session)
                                                },
                                                sizes=(1,),
                                            row_btn=('Назад', 'AdminMenu_')))


@admin_router.callback_query(F.data.startswith('tosdel_'))
async def delete_tos(callback: types.CallbackQuery, session: AsyncSession):
    name_tos = callback.data.split('_')[-1]
    try:
        await orm_delete_tos(session, name_tos)
        await callback.message.edit_text('Тип услуг успешно удалён.', reply_markup=ADMIN_KB)
    except Exception as e:
        await callback.message.edit_text(f'Ошибка\n{e}\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)


@admin_router.callback_query(F.data.startswith('cidelete_'))
async def delete_ci(callback: types.CallbackQuery, session: AsyncSession):
    ci_id = int(callback.data.split('_')[-1])
    try:
        await orm_delete_ci(session, ci_id)
        await orm_delete_client(session, ci_id)
        await orm_delete_worker(session, ci_id)
        await callback.message.edit_text(f'Контактная информация об пользователе с ID {ci_id} успешно удалена',
                                         reply_markup=ADMIN_KB)
    except Exception as e:
        await callback.message.edit_text(f'Ошибка\n{e}\n\nЧто хотите сделать?', reply_markup=ADMIN_KB)

# ------------------------------------ПАГИНАЦИЯ-УСЛУГ-------------------------------------------------------------------


@admin_router.callback_query(F.data == 'services_')
async def type_of_serv(callback: types.CallbackQuery, session: AsyncSession):

    await callback.message.edit_text('Какой тип услуг вас интересует?',
                                     reply_markup=get_inline_kb(
                                            btns={
                                            tos.name: f'admtos_{tos.name}' for tos in await orm_get_all_tos(session)
                                                },
                                                sizes=(1,),
                                            row_btn=('Удалить тип услуги', 'delTOS_'),
                                            row_btn2=('Назад', 'AdminMenu_')
                                                ))


@admin_router.callback_query(F.data.startswith('admtos_'))
async def start_pagination_services(callback: types.CallbackQuery, session: AsyncSession):
    tos_name = callback.data.split('_')[-1]
    page = 0
    services = await orm_get_services(session, tos_name)
    service = services[page]
    await callback.message.edit_text(f'{service.name}\n\n{service.description}\n\n{service.price} руб.',
                                     reply_markup=
                                     await get_keyboards(session=session, pref='servADM', page=page,
                                                         tos_name=tos_name, back='AdminMenu_'))


@admin_router.callback_query(Pagination.filter(F.pref == 'servADM'))
async def pagination_services(callback: types.CallbackQuery,callback_data: Pagination, session: AsyncSession):
    tos_name = callback_data.tos_name
    page = callback_data.page
    services = await orm_get_services(session, tos_name)
    service = services[page]
    await callback.message.edit_text(f'{service.name}\n\n{service.description}\n\n{service.price} руб.',
                                     reply_markup=
                                     await get_keyboards(session=session, pref='servADM', page=page,
                                                         tos_name=tos_name, back='AdminMenu_'))


@admin_router.callback_query(F.data == 'workers_')
async def start_pagination_workers(callback: types.CallbackQuery, session: AsyncSession):
    try:
        workers_id = await orm_get_workers(session)
        page = 0
        worker_id = workers_id[page].id_contact_information
        worker = await orm_get_contact_information_id(session, worker_id)
        await callback.message.edit_text(f'ID: {worker.id} | tg://openmessage?user_id={worker.id}'
                                         f'\nИмя: {worker.firstName}\nФамилия: {worker.lastName}'
                                         f'\nОтчество: {worker.patronymic}\nНомер телефона: {worker.phoneNumber}\n'
                                         f'Специальность: {workers_id[page].specialty}\nРазряд: {workers_id[page].grade}',
                                         reply_markup=
                                         await get_keyboards(session=session, page=page, pref='workersADM',
                                                             back='AdminMenu_'))
    except:
        await callback.message.edit_text('Исполнителей нет.', reply_markup=ADMIN_KB)


@admin_router.callback_query(Pagination.filter(F.pref == 'workersADM'))
async def pagination_workers(callback: types.CallbackQuery, callback_data: Pagination,session: AsyncSession):
    workers_id = await orm_get_workers(session)
    page = callback_data.page
    worker_id = workers_id[page].id_contact_information
    worker = await orm_get_contact_information_id(session, worker_id)
    await callback.message.edit_text(f'ID: {worker.id} | tg://openmessage?user_id={worker.id}'
                                     f'\nИмя: {worker.firstName}\nФамилия: {worker.lastName}'
                                     f'\nОтчество: {worker.patronymic}\nНомер телефона: {worker.phoneNumber}\n'
                                     f'Специальность: {workers_id[page].specialty}\nРазряд: {workers_id[page].grade}',
                                     reply_markup=
                                     await get_keyboards(session=session, page=page, pref='workersADM',
                                                         back='AdminMenu_'))


@admin_router.callback_query(F.data == 'clients_')
async def start_pagination_clients(callback: types.CallbackQuery, session: AsyncSession):
    clients_id = await orm_get_clients(session)
    try:
        page = 0
        client_id = clients_id[page].id_contact_information
        client = await orm_get_contact_information_id(session, client_id)
        await callback.message.edit_text(f'ID: {client.id} | tg://openmessage?user_id={client.id}\n'
                                         f'Имя: {client.firstName}\nФамилия: {client.lastName}\n'
                                         f'Отчество: {client.patronymic}\nНомер телефона: {client.phoneNumber}\n'
                                         f'Почта: {client.email}',
                                         reply_markup=
                                         await get_keyboards(session=session, page=page, pref='clientsADM',
                                                             back='AdminMenu_'))
    except:
        await callback.message.edit_text('Клиентов пока нет.', reply_markup=ADMIN_KB)


@admin_router.callback_query(Pagination.filter(F.pref == 'clientsADM'))
async def pagination_clients(callback: types.CallbackQuery, callback_data: Pagination, session: AsyncSession):
    clients_id = await orm_get_clients(session)
    page = int(callback_data.page)
    client_id = clients_id[page].id_contact_information
    client = await orm_get_contact_information_id(session, client_id)
    await callback.message.edit_text(f'ID: {client.id} | tg://openmessage?user_id={client.id}\n'
                                     f'Имя: {client.firstName}\nФамилия: {client.lastName}\n'
                                     f'Отчество: {client.patronymic}\nНомер телефона: {client.phoneNumber}\n'
                                     f'Почта: {client.email}',
                                     reply_markup=
                                     await get_keyboards(session=session, page=page, pref='clientsADM',
                                                         back='AdminMenu_'))


@admin_router.callback_query(F.data == 'allFeedback')
async def all_feedback(callback: CallbackQuery, session: AsyncSession):
    feedbacks = await orm_get_feedbacks(session)
    page = 0
    try:
        await callback.message.edit_text(await FeedbackDesc(session=session, page=page, id_feedback=feedbacks[page].id)
                                         .get_desc_for_admin(),
                                         reply_markup= await get_keyboards(session=session, pref='feedBackADM', page=page,
                                                                           array_feedback=feedbacks, back='AdminMenu_'))
    except IndexError:
        await callback.message.edit_text('Отзывов пока нет.', reply_markup=ADMIN_KB)

@admin_router.callback_query(Pagination.filter(F.pref == 'feedBackADM'))
async def pagination_all_feedback(callback: CallbackQuery, callback_data: Pagination, session: AsyncSession):
    feedbacks = await orm_get_feedbacks(session)
    page = callback_data.page
    await callback.message.edit_text(await FeedbackDesc(session=session, page=page, id_feedback=feedbacks[page].id)
                                     .get_desc_for_admin(),
                                     reply_markup=await get_keyboards(session=session, pref='feedBackADM', page=page,
                                                                      array_feedback=feedbacks, back='AdminMenu_'))
