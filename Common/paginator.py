from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from DataBase.orm_query import orm_get_services, orm_get_workers, orm_get_clients, orm_get_feedback

# Кастомные коллбэки
class PaginationOrders(CallbackData, prefix='pag_ord'):
    action: str
    page: int


class PaginationWorker(CallbackData, prefix='pag_work'):
    action: str
    page: int


class PaginationFinishedClient(CallbackData, prefix='pag_fin_c'):
    action: str
    page: int


class PaginationFinishedWorker(CallbackData, prefix='pag_fin_w'):
    action: str
    page: int


class PaginationServices(CallbackData, prefix='pag_serv'):
    action: str
    page: int
    tos_name: str


class PaginationUser(CallbackData, prefix='pag_user'):
    action: str
    page: int
    tos_name: str


class PaginationUserOrders(CallbackData, prefix='pag_user_order'):
   action: str
   page: int
   id: int


class PaginationClients(CallbackData, prefix='pag_cli'):
    action: str
    page: int


class PaginationWorkers(CallbackData, prefix='pag_wrk'):
    action: str
    page: int


class Pagination(CallbackData, prefix='pag'):
    page: int
    pref: str


def paginator(array: list, page: int, pref: str):
    builder = InlineKeyboardBuilder()
    btn_row = []
    if len(array) != 1:
        if page == 0:
            btn_row.append(
                InlineKeyboardButton(text='<<', callback_data=Pagination(page=len(array) - 1, pref=pref).pack()))
        if page > 0:
            btn_row.append(
                InlineKeyboardButton(text='<<', callback_data=Pagination(page=page - 1, pref=pref).pack()))
        if page < len(array) - 1:
            btn_row.append(
                InlineKeyboardButton(text='>>', callback_data=Pagination(page=page + 1, pref=pref).pack()))
        if page == len(array) - 1:
            btn_row.append(
                InlineKeyboardButton(text='>>', callback_data=Pagination(page=0, pref=pref).pack()))

    builder.row(*btn_row)

    return builder.as_markup()






async def paginator_for_finished(array: list, back: str, page: int = 0, id_worker: int = 0, id_client: int = 0, session: AsyncSession = None):
    builder = InlineKeyboardBuilder()
    btn_row = []
    if id_worker == 0:
        if len(array) != 1:
            if page == 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationFinishedClient
                    (action='prev', page=len(array) - 1,
                                                                                   ).pack()))
            if page > 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationFinishedClient
                    (action='prev', page=page - 1
                                                                                   ).pack()))
            if page < len(array) - 1:
                btn_row.append(
                    InlineKeyboardButton(text='>>', callback_data=PaginationFinishedClient
                    (action='next', page=page + 1
                                                                                   ).pack()))
            if page == len(array) - 1:
                btn_row.append(InlineKeyboardButton(text='>>', callback_data=PaginationFinishedClient
                (action='next', page=0,
                                                                                              ).pack()))
        if await orm_get_feedback(session, array[page].id) is None:
            builder.row(InlineKeyboardButton(text='Оставить отзыв', callback_data=f'feedback_{array[page].id}'))
        else:
            builder.row(InlineKeyboardButton(text='Вы уже оставили отзыв', callback_data='а1212'))
    else:
        if len(array) != 1:
            if page == 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationFinishedWorker
                    (action='prev', page=len(array) - 1,
                                                                                   ).pack()))
            if page > 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationFinishedWorker
                    (action='prev', page=page - 1
                                                                                   ).pack()))
            if page < len(array) - 1:
                btn_row.append(
                    InlineKeyboardButton(text='>>', callback_data=PaginationFinishedWorker
                    (action='next', page=page + 1
                                                                                   ).pack()))
            if page == len(array) - 1:
                btn_row.append(InlineKeyboardButton(text='>>', callback_data=PaginationFinishedWorker
                (action='next', page=0,
                                                                                              ).pack()))
    builder.row(*btn_row)
    builder.row(InlineKeyboardButton(text='Назад', callback_data=back))

    return builder.as_markup()

# Функция для создания кнопок пагинации
async def paginator_for_workers(array: list, back: str, page: int = 0, id_worker: int = 0):
    builder = InlineKeyboardBuilder()
    btn_row = []
    if id_worker == 0:
        if len(array) != 1:
            if page == 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationWorker(action='prev', page=len(array) - 1,
                                                                                 ).pack()))
            if page > 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationWorker(action='prev', page=page - 1
                                                                                 ).pack()))
            if page < len(array) - 1:
                btn_row.append(
                    InlineKeyboardButton(text='>>', callback_data=PaginationWorker(action='next', page=page + 1
                                                                                 ).pack()))
            if page == len(array) - 1:
                btn_row.append(InlineKeyboardButton(text='>>', callback_data=PaginationWorker(action='next', page=0,
                                                                                 ).pack()))
        builder.row(InlineKeyboardButton(text='Взять заказ', callback_data=f'takeOrder_{array[page].id}'))
    else:
        if len(array) != 1:
            if page == 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationOrders(action='prev', page=len(array) - 1,
                                                                                 ).pack()))
            if page > 0:
                btn_row.append(
                    InlineKeyboardButton(text='<<', callback_data=PaginationOrders(action='prev', page=page - 1
                                                                                 ).pack()))
            if page < len(array) - 1:
                btn_row.append(
                    InlineKeyboardButton(text='>>', callback_data=PaginationOrders(action='next', page=page + 1
                                                                                 ).pack()))
            if page == len(array) - 1:
                btn_row.append(InlineKeyboardButton(text='>>', callback_data=PaginationOrders(action='next', page=0,
                                                                                 ).pack()))
        builder.row(InlineKeyboardButton(text='Завершить заказ',
                    callback_data=f'changeStatus_{array[page].id}'))
        builder.row(InlineKeyboardButton(text='Завершённые заказы',
                                         callback_data='workerFinished_'))

    builder.row(*btn_row)
    builder.row(InlineKeyboardButton(text='Назад', callback_data=back))

    return builder.as_markup()


# функция для создания кнопок
async def paginator_workers(session: AsyncSession, back: str, page: int = 0):
    builder = InlineKeyboardBuilder()
    cor = await orm_get_workers(session)

    btn_row = []
    if len(cor) != 1:
        if page == 0:
            btn_row.append(InlineKeyboardButton(text='<<',
            callback_data=PaginationWorkers(action='prev', page=len(cor)-1,
                                    ).pack()))
        if page > 0:
            btn_row.append(InlineKeyboardButton(text='<<',
            callback_data=PaginationWorkers(action='prev', page=page-1,
                                    ).pack()))
        if page < len(cor) - 1:
            btn_row.append(InlineKeyboardButton(text='>>',
            callback_data=PaginationWorkers(action='next', page=page+1,
                                    ).pack()))
        if page == len(cor) - 1:
            btn_row.append(InlineKeyboardButton(text='>>',
            callback_data=PaginationWorkers(action='next', page=0,
                                    ).pack()))

    builder.row(*btn_row)

    adm_btns = [InlineKeyboardButton(text='Удалить', callback_data=f'cidelete_{cor[page].id_contact_information}')
                    ]
    builder.row(*adm_btns)
    builder.row(InlineKeyboardButton(text='Назад', callback_data=back))

    return builder.as_markup()


async def paginator_clients(session: AsyncSession, back: str, page: int = 0):
    builder = InlineKeyboardBuilder()
    cor = await orm_get_clients(session)

    btn_row = []
    if len(cor) != 1:
        if page == 0:
            btn_row.append(InlineKeyboardButton(text='<<',
            callback_data=PaginationClients(action='prev', page=len(cor)-1,
                                    ).pack()))
        if page > 0:
            btn_row.append(InlineKeyboardButton(text='<<',
            callback_data=PaginationClients(action='prev', page=page-1,
                                    ).pack()))
        if page < len(cor) - 1:
            btn_row.append(InlineKeyboardButton(text='>>',
            callback_data=PaginationClients(action='next', page=page+1,
                                    ).pack()))
        if page == len(cor) - 1:
            btn_row.append(InlineKeyboardButton(text='>>',
            callback_data=PaginationClients(action='next', page=0,
                                    ).pack()))

    builder.row(*btn_row)

    adm_btns = [InlineKeyboardButton(text='Удалить', callback_data=f'cidelete_{cor[page].id_contact_information}')
                    ]
    builder.row(*adm_btns)
    builder.row(InlineKeyboardButton(text='Назад', callback_data=back))

    return builder.as_markup()


async def paginator_services(session: AsyncSession, back: str, tos_name = None,   page: int = 0):

    builder = InlineKeyboardBuilder()
    cor = await orm_get_services(session, tos_name)

    btn_row = []
    if len(cor) != 1:
        if page == 0:
            btn_row.append(InlineKeyboardButton(text='<<',
            callback_data=PaginationServices(action='prev', page=len(cor)-1,
                                    tos_name=tos_name).pack()))
        if page > 0:
            btn_row.append(InlineKeyboardButton(text='<<',
            callback_data=PaginationServices(action='prev', page=page-1,
                                    tos_name=tos_name).pack()))
        if page < len(cor) - 1:
            btn_row.append(InlineKeyboardButton(text='>>',
            callback_data=PaginationServices(action='next', page=page+1,
                                    tos_name=tos_name).pack()))
        if page == len(cor) - 1:
            btn_row.append(InlineKeyboardButton(text='>>',
            callback_data=PaginationServices(action='next', page=0,
                                    tos_name=tos_name).pack()))

    builder.row(*btn_row)

    adm_btns = [InlineKeyboardButton(text='Изменить', callback_data=f'update_{cor[page].id}'),
                InlineKeyboardButton(text='Удалить', callback_data=f'delete_{cor[page].id}')
                ]
    builder.row(*adm_btns)

    builder.row(InlineKeyboardButton(text='Назад', callback_data=back))

    return builder.as_markup()


async def paginator_user(array: list, back: str, page: int = 0, id_client: int = 0, tos_name: str = ' '):
    builder = InlineKeyboardBuilder()
    cor = array
    btn_row = []
    if id_client == 0:
        if len(cor) != 1:
            if page == 0:
                btn_row.append(InlineKeyboardButton(text='<<', callback_data=PaginationUser(action='prev', page=len(cor)-1,
                                                                                            tos_name=tos_name).pack()))
            if page > 0:
                btn_row.append(InlineKeyboardButton(text='<<', callback_data=PaginationUser(action='prev', page=page-1,
                                                                                            tos_name=tos_name).pack()))
            if page < len(cor) - 1:
                btn_row.append(InlineKeyboardButton(text='>>', callback_data=PaginationUser(action='next', page=page+1,
                                                                                            tos_name=tos_name).pack()))
            if page == len(cor) - 1:
                btn_row.append(InlineKeyboardButton(text='>>',callback_data=PaginationUser(action='next', page=0,
                                                                                           tos_name=tos_name).pack()))
        builder.row(InlineKeyboardButton(text='Заказать', callback_data=f'toOrder_{cor[page].id}'))
    else:
        if len(cor) != 1:
            if page == 0:
                btn_row.append(InlineKeyboardButton(text='<<', callback_data=PaginationUserOrders(action='prev',
                                                                                                  page=len(cor)-1,
                                                                                            id=id_client).pack()))
            if page > 0:
                btn_row.append(InlineKeyboardButton(text='<<', callback_data=PaginationUserOrders(action='prev',
                                                                                                  page=page-1,
                                                                                            id=id_client).pack()))
            if page < len(cor) - 1:
                btn_row.append(InlineKeyboardButton(text='>>', callback_data=PaginationUserOrders(action='next',
                                                                                                  page=page+1,
                                                                                            id=id_client).pack()))
            if page == len(cor) - 1:
                btn_row.append(InlineKeyboardButton(text='>>',callback_data=PaginationUserOrders(action='next',
                                                                                                 page=0,
                                                                                           id=id_client).pack()))
        builder.row(InlineKeyboardButton(text='Завершенные заказы', callback_data='UserFinished_'))
    builder.row(*btn_row)

    builder.row(InlineKeyboardButton(text='Назад', callback_data=back))

    return builder.as_markup()
