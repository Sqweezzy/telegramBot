from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from DataBase.engine import session_maker
from DataBase.models import ContactInformation, Client, Admins, TypesOfServices, Services, Worker, Awaiting, Feedback


async def orm_add_admins(session: AsyncSession, id: int):
    obj = Admins(
        id=id
    )

    session.add(obj)
    await session.commit()


async def orm_get_admins(session: AsyncSession):
    query = select(Admins)
    result = await session.execute(query)
    return result.scalars().all()

# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------CONTACT-INFORMATION----------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
async def orm_add_client(session: AsyncSession, data: dict):
    obj = Client(
        id_contact_information=data['id'],
        status=data['status']
    )

    session.add(obj)
    await session.commit()


async def orm_get_clients(session: AsyncSession):
    query = select(Client)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_client(session: AsyncSession, id_client: int):
    query = delete(Client).where(Client.id_contact_information == id_client)
    await session.execute(query)
    await session.commit()


async def orm_add_contact_information(session: AsyncSession, data: dict):
    obj = ContactInformation(
        id=data['id'],
        firstName=data['firstName'],
        lastName=data['lastName'],
        patronymic=data['patronymic'],
        email=data['email'],
        phoneNumber=data['phone']
    )
    session.add(obj)
    await session.commit()


async def orm_get_contact_information_id(session: AsyncSession, id_client: int):
    query = select(ContactInformation).where(ContactInformation.id == id_client)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_ci_fn(session: AsyncSession, id_client: int, new_fname: str):
    query = update(ContactInformation).where(ContactInformation.id == id_client).values(
        firstName=new_fname
    )
    await session.execute(query)
    await session.commit()


async def orm_update_ci_sn(session: AsyncSession, id_client: int, new_lname: str):
    query = update(ContactInformation).where(ContactInformation.id == id_client).values(
        lastName=new_lname
    )
    await session.execute(query)
    await session.commit()


async def orm_update_ci_patr(session: AsyncSession, id_client: int, new_patr: str):
    query = update(ContactInformation).where(ContactInformation.id == id_client).values(
        patronymic=new_patr
    )
    await session.execute(query)
    await session.commit()


async def orm_update_ci_mail(session: AsyncSession, id_client: int, new_mail: str):
    query = update(ContactInformation).where(ContactInformation.id == id_client).values(
        email=new_mail
    )
    await session.execute(query)
    await session.commit()


async def orm_update_ci_phone(session: AsyncSession, id_client: int, new_phone):
    query = update(ContactInformation).where(ContactInformation.id == id_client).values(
        phoneNumber=new_phone
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_ci(session: AsyncSession, ci_id: int):
    query = delete(ContactInformation).where(ContactInformation.id == ci_id)
    await session.execute(query)
    await session.commit()

# ----------------------------------------------------------------------------------------------------------------------
# -----------------------------------SERVICES---------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


async def orm_add_tos(session: AsyncSession, data: dict):
    obj = TypesOfServices(
        name=data['name'],
        description=data['description']
    )
    session.add(obj)
    await session.commit()


async def orm_delete_tos(session: AsyncSession, name: str):
    query = delete(TypesOfServices).where(TypesOfServices.name == name)
    await session.execute(query)
    await session.commit()


async def orm_get_all_tos(session: AsyncSession):
    query = select(TypesOfServices)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_add_service(session: AsyncSession, data: dict):
    obj = Services(
        name_types_of_services=data['name_typesOfServices'],
        name=data['name'],
        description=data['description'],
        price=data['price']
    )
    session.add(obj)
    await session.commit()


async def orm_get_services(session: AsyncSession, tos_name: str):
    query = select(Services).where(Services.name_types_of_services == tos_name)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_update_service(session: AsyncSession, id: int, data: dict):
    query = update(Services).where(Services.id == id).values(
        name_types_of_services=data['name_typesOfServices'],
        name=data['name'],
        description=data['description'],
        price=data['price']
    )
    await session.execute(query)
    await session.commit()


async def orm_get_service(session: AsyncSession, id: int):
    query = select(Services).where(Services.id == id)
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_service(session: AsyncSession, id: int):
    query = delete(Services).where(Services.id == id)
    await session.execute(query)
    await session.commit()


async def orm_add_worker(session: AsyncSession, data: dict):
    obj = Worker(
        id_contact_information=data['id'],
        specialty=data['specialty'],
        grade=data['grade']
    )
    session.add(obj)
    await session.commit()


async def orm_get_worker(session: AsyncSession, worker_id: int):
    query = select(Worker).where(Worker.id_contact_information == worker_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_workers(session: AsyncSession):
    query = select(Worker)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_worker(session: AsyncSession, work_id: int):
    query = delete(Worker).where(Worker.id_contact_information == work_id)
    await session.execute(query)
    await session.commit()


async def orm_add_awaiting(session: AsyncSession, client_id, id_service):
    obj = Awaiting(
        id_services=id_service,
        id_client=client_id,
        status='В ожидании.',
        id_workers=0,
    )
    session.add(obj)
    await session.commit()


async def orm_update_awaiting(session: AsyncSession, id_awaiting: int, id_worker: int):
    query = update(Awaiting).where(Awaiting.id == id_awaiting).values(
        id_workers=id_worker,
        status='В процессе.',
    )
    await session.execute(query)
    await session.commit()


async def orm_finish_order(session: AsyncSession, id_awaiting: int):
    query = update(Awaiting).where(Awaiting.id == id_awaiting).values(
        status='Завершен.'
    )
    await session.execute(query)
    await session.commit()


async def orm_get_awaitings_for_client(session: AsyncSession, client_id):
    query = select(Awaiting).where(and_(Awaiting.id_client == client_id, Awaiting.status != 'Завершен.'))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_all_awaitings(session: AsyncSession):
    query = select(Awaiting).where(Awaiting.status == 'В ожидании.')
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_awaitings_for_worker(session: AsyncSession, id_worker: int):
    query = select(Awaiting).where(and_(Awaiting.id_workers == id_worker, Awaiting.status == 'В процессе.'))
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_finished_for_worker(session: AsyncSession, id_worker: int):
    query = select(Awaiting).where(and_(Awaiting.id_workers == id_worker, Awaiting.status == 'Завершен.'))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_finished_for_clients(session: AsyncSession, id_client: int):
    query = select(Awaiting).where(and_(Awaiting.id_client == id_client, Awaiting.status == 'Завершен.'))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_awaiting(session: AsyncSession, id_awaiting: int):
    query = delete(Awaiting).where(Awaiting.id == id_awaiting)
    await session.execute(query)
    await session.commit()


async def orm_add_feedback(session: AsyncSession, data: dict):
    obj = Feedback(
        id_awaiting=data['id_awaiting'],
        mark=data['mark'],
        text=data['text']
    )
    session.add(obj)
    await session.commit()


async def orm_get_feedback(session: AsyncSession, id_awaiting: int):
    query = select(Feedback).where(Feedback.id_awaiting == id_awaiting)
    result = await session.execute(query)
    return result.scalar()
