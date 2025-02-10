from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from Common.client_inf import OrderService
from Common.paginator import PaginationWorker, paginator_for_workers, PaginationOrders, paginator_for_finished, \
    PaginationFinishedWorker, paginator, Pagination
from DataBase.orm_query import orm_get_all_awaitings, orm_update_awaiting, orm_get_awaitings_for_worker, \
    orm_finish_order, orm_get_finished_for_worker
from Filters.chat_type import IsWorker, ChatTypeFilter
from Keyboards.inline import get_inline_kb

worker_router = Router()
worker_router.message.filter(ChatTypeFilter(['private']))
worker_router.message.filter(IsWorker())

WORKER_KB = get_inline_kb(btns={
    'Заказы':'orders_',
    'Мои заказы':'yourOrders_',
})


@worker_router.message(Command('worker'))
async def start_worker(message: Message, bot: Bot):
    try:
        await bot.delete_message(message.chat.id, message.message_id - 1)
    except:
        pass
    await message.delete()
    await message.answer('Панель работника:', reply_markup=WORKER_KB)


@worker_router.callback_query(F.data == 'WorkerMenu_')
async def start_worker_call(callback: CallbackQuery):
    await callback.message.edit_text('Панель работника:', reply_markup=WORKER_KB)


@worker_router.callback_query(F.data == 'orders_')
async def check_orders(callback: CallbackQuery, session: AsyncSession):
    array = await orm_get_all_awaitings(session)
    page = 0
    try:
        await callback.message.edit_text(await OrderService(session, array[page].id_services, array[page].id_client, page)
                                         .get_description(),
                                         reply_markup=await paginator_for_workers(
                                             array=array, page=page, back='WorkerMenu_'))
    except IndexError:
        await callback.message.edit_text('Заказов пока нет.',
                                         reply_markup=get_inline_kb(
                                             btns={'Назад':'WorkerMenu_'}
                                         ))


@worker_router.callback_query(PaginationWorker.filter())
async def pagination_check_orders(callback: CallbackQuery, callback_data: PaginationWorker, session: AsyncSession):
    array = await orm_get_all_awaitings(session)
    page = callback_data.page
    await callback.message.edit_text(await OrderService(session,array[page].id_services, array[page].id_client, page)
                                     .get_description(),
                                     reply_markup=await paginator_for_workers(
                                         array=array, page=page, back='WorkerMenu_'))


@worker_router.callback_query(F.data.startswith('takeOrder_'))
async def take_order(callback: CallbackQuery, session: AsyncSession):
    try:
        await orm_update_awaiting(session=session,id_awaiting=int(callback.data.split('_')[-1]),
                                  id_worker=callback.from_user.id)
        await callback.message.edit_text('Услуга успешно взята! Что хотите сделать?',reply_markup=WORKER_KB)
    except Exception as e:
        await callback.message.edit_text(f'Ошибка\n{e}', reply_markup=WORKER_KB)


@worker_router.callback_query(F.data == 'yourOrders_')
async def check_yours_orders(callback: CallbackQuery, session: AsyncSession):
    your_orders = await orm_get_awaitings_for_worker(session, callback.from_user.id)
    page = 0
    try:
        await callback.message.edit_text(await OrderService
        (session, your_orders[page].id_services, your_orders[page].id_client, page, id_worker=callback.from_user.id)
                                         .get_description_for_worker(),
                                         reply_markup=await
                                         paginator_for_workers
                                         (array=your_orders,back='WorkerMenu_',page=page, id_worker=callback.from_user.id))
    except IndexError:
        await callback.message.edit_text('Заказов пока нет. Хотите посмотреть завершённые заказы?',
                                         reply_markup=get_inline_kb(
            btns={'Завершенные заказы':'workerFinished_',
                'Назад':'WorkerMenu_'},sizes=(1,)
        ))


@worker_router.callback_query(PaginationOrders.filter())
async def pagination_your_orders(callback: CallbackQuery, callback_data: PaginationOrders,session: AsyncSession):
    your_orders = await orm_get_awaitings_for_worker(session, callback.from_user.id)
    page = callback_data.page
    await callback.message.edit_text(await OrderService
    (session, your_orders[page].id_services, your_orders[page].id_client, page, id_worker=callback.from_user.id)
                                     .get_description_for_worker(),
                                     reply_markup=await
                                     paginator_for_workers
                                     (array=your_orders, back='WorkerMenu_', page=page,
                                      id_worker=callback.from_user.id))


@worker_router.callback_query(F.data.startswith('changeStatus_'))
async def change_status_order(callback: CallbackQuery, session: AsyncSession):
    try:
        await orm_finish_order(session, int(callback.data.split('_')[-1]))
        await callback.message.edit_text('Статус заказа - Завершен\nЧто хотите сделать?', reply_markup=WORKER_KB)
    except Exception as e:
        await callback.message.edit_text(f'Ошибка\n{e}', reply_markup=WORKER_KB)


@worker_router.callback_query(F.data == 'workerFinished_')
async def finished_orders(callback: CallbackQuery, session: AsyncSession):
    finished = await orm_get_finished_for_worker(session, callback.from_user.id)
    page = 0
    try:
        await callback.message.edit_text(await OrderService(
            session, finished[page].id_services, finished[page].id_client, page, callback.from_user.id).
                                         get_description_for_finished_worker(), reply_markup=await paginator_for_finished(
            finished, 'WorkerMenu_', page, id_worker=callback.from_user.id
        ))
    except IndexError:
        await callback.message.edit_text('Завершённых заказов пока нет.', reply_markup=get_inline_kb(
            btns={'Назад':'WorkerMenu_'}
        ))


@worker_router.callback_query(PaginationFinishedWorker.filter())
async def pagination_finished(callback: CallbackQuery, callback_data: PaginationFinishedWorker, session: AsyncSession):
    finished = await orm_get_finished_for_worker(session, callback.from_user.id)
    page = callback_data.page
    await callback.message.edit_text(await OrderService(
        session, finished[page].id_services, finished[page].id_client, page, callback.from_user.id).
                                     get_description_for_finished_worker(), reply_markup=await paginator_for_finished(
        finished, 'WorkerMenu_', page, id_worker=callback.from_user.id
    ))
