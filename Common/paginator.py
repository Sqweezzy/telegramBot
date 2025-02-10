from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from DataBase.orm_query import orm_get_services, orm_get_workers, orm_get_clients, orm_get_feedback, \
    orm_get_awaitings_for_client, orm_get_finished_for_clients, orm_get_all_awaitings, orm_get_awaitings_for_worker, \
    orm_get_finished_for_worker


class Pagination(CallbackData, prefix='pag'):
    pref: str
    page: int
    id_worker: int
    tos_name: str
    id_client: int


async def get_keyboards(
        session: AsyncSession,
        pref: str,
        page: int,
        id_worker: int = None,
        tos_name: str = None,
        back: str = None,
        id_client: int = None):
    builder = InlineKeyboardBuilder()

    if pref == 'servUS':
        array = await orm_get_services(session, tos_name)
        pag_btns = paginator(array=array, page=page, pref=pref, tos_name=tos_name)
        builder.row(InlineKeyboardButton(text='Заказать',
                                         callback_data=f'toOrder_{array[page].id}'))
        builder.row(*pag_btns)
    elif pref == 'ordersUS':
        array = await orm_get_awaitings_for_client(session, id_client)
        pag_btns = paginator(array=array, page=page, pref=pref, id_client=id_client)
        builder.row(InlineKeyboardButton(text='Завершенные заказы',
                                         callback_data='UserFinished_'))
        builder.row(*pag_btns)
    elif pref == 'finiteUS':
        array = await orm_get_finished_for_clients(session, id_client)
        pag_btns = paginator(array=array, page=page, pref=pref, id_client=id_client)
        if await orm_get_feedback(session, array[page].id) is None:
            builder.row(InlineKeyboardButton(text='Оставить отзыв',
                                             callback_data=f'feedback_{array[page].id}'))
        else:
            builder.row(InlineKeyboardButton(text='Вы уже оставили отзыв', callback_data='null'))
        builder.row(*pag_btns)
    elif pref == 'servADM':
        array = await orm_get_services(session, tos_name)
        pag_btns = paginator(array=array, page=page, pref=pref, tos_name=tos_name)
        adm_btns = [InlineKeyboardButton(text='Изменить', callback_data=f'update_{array[page].id}'),
                    InlineKeyboardButton(text='Удалить', callback_data=f'delete_{array[page].id}')
                    ]
        builder.row(*adm_btns)
        builder.row(*pag_btns)
    elif pref == 'workersADM':
        array = await orm_get_workers(session)
        pag_btns = paginator(array=array, page=page, pref=pref)
        builder.row(InlineKeyboardButton(text='Удалить',
                                         callback_data=f'cidelete_{array[page].id_contact_information}'))
        builder.row(*pag_btns)
    elif pref == 'clientsADM':
        array = await orm_get_clients(session)
        pag_btns = paginator(array=array, page=page, pref=pref)
        builder.row(InlineKeyboardButton(text='Удалить',
                                         callback_data=f'cidelete_{array[page].id_contact_information}'))
        builder.row(*pag_btns)
    elif pref == 'ordersWRK':
        array = await orm_get_all_awaitings(session)
        pag_btns = paginator(array=array, page=page, pref=pref)
        builder.row(InlineKeyboardButton(text='Взять заказ', callback_data=f'takeOrder_{array[page].id}'))
        builder.row(*pag_btns)
    elif pref == 'yourOrderWRK':
        array = await orm_get_awaitings_for_worker(session=session, id_worker=id_worker)
        pag_btns = paginator(array=array, page=page, pref=pref, id_worker=id_worker)
        builder.row(InlineKeyboardButton(text='Завершить заказ',
                                         callback_data=f'changeStatus_{array[page].id}'))
        builder.row(InlineKeyboardButton(text='Завершённые заказы',
                                         callback_data='workerFinished_'))
        builder.row(*pag_btns)
    elif pref == 'finiteWRK':
        array = await orm_get_finished_for_worker(session, id_worker)
        pag_btns = paginator(array=array, page=page, pref=pref, id_worker=id_worker)
        builder.row(*pag_btns)

    if back is not None:
        builder.row(InlineKeyboardButton(text='Назад', callback_data=back))

    return builder.as_markup()

def paginator(array: list, page: int, pref: str, id_worker: int = 0, tos_name: str = 'A', id_client: int = 0):
    btn_row = []
    if len(array) != 1:
        if page == 0:
            btn_row.append(
                InlineKeyboardButton(
                    text='<<',
                    callback_data=
                    Pagination(
                        page=len(array) - 1, pref=pref, id_worker=id_worker, tos_name=tos_name, id_client=id_client)
                    .pack()))
        if page > 0:
            btn_row.append(
                InlineKeyboardButton(
                    text='<<',
                    callback_data=
                    Pagination(page=page - 1, pref=pref, id_worker=id_worker, tos_name=tos_name, id_client=id_client)
                    .pack()))
        if page < len(array) - 1:
            btn_row.append(
                InlineKeyboardButton(
                    text='>>',
                    callback_data=
                    Pagination(page=page + 1, pref=pref, id_worker=id_worker, tos_name=tos_name, id_client=id_client)
                    .pack()))
        if page == len(array) - 1:
            btn_row.append(
                InlineKeyboardButton(
                    text='>>',
                    callback_data=
                    Pagination(page=0, pref=pref, id_worker=id_worker, tos_name=tos_name, id_client=id_client)
                    .pack()))

    return btn_row
