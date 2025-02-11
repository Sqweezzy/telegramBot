from sqlalchemy.ext.asyncio import AsyncSession

from DataBase.orm_query import orm_get_contact_information_id, orm_get_service, orm_get_all_awaitings, \
    orm_get_awaitings_for_client, orm_get_awaitings_for_worker, orm_get_finished_for_worker, \
    orm_get_finished_for_clients, orm_get_feedback_one, orm_get_awaiting_one


class ClientInformation:
    def __init__(self, session: AsyncSession, client_id: int):
        self.session = session
        self.client_id = client_id

    async def get_user_names(self):
        user = await orm_get_contact_information_id(self.session, self.client_id)
        if user is not None:
            return user.firstName, user.lastName
        else:
            return None

    async def get_all_user_inf(self):
        user = await orm_get_contact_information_id(self.session, self.client_id)
        if user is not None:
            if user.patronymic != 'NULL':
                return f'ID: {user.id}\nИмя: {user.firstName}\nФамилия: {user.lastName}\nОтчество: {user.patronymic}\nНомер телефона:{user.phoneNumber}\nПочта: {user.email}'
            else:
                return f'ID: {user.id}\nИмя: {user.firstName}\nФамилия: {user.lastName}\nОтчество: у Вас его нет\nНомер телефона: {user.phoneNumber}\nПочта: {user.email}'
        elif user is None:
            return None


class OrderService:
    def __init__(self, session: AsyncSession, id_service: int, id_client: int, page: int, id_worker: int = 0):
        self.page=page
        self.session=session
        self.id_worker=id_worker
        self.id_service=id_service
        self.id_client=id_client

    async def get_description(self):
        service = await orm_get_service(self.session, self.id_service)
        orders = await orm_get_all_awaitings(self.session)
        client= await orm_get_contact_information_id(self.session, self.id_client)
        return f'Услуга - {service.name}\n\n{service.description}\nСтоимость - {service.price} руб.\n\nЗаказано - {orders[self.page].created} {client.id} | tg://openmessage?user_id={client.id}\nИмя: {client.firstName}\nФамилия: {client.lastName}\nНомер телефона: {client.phoneNumber}'

    async def get_description_for_worker(self):
        service = await orm_get_service(self.session, self.id_service)
        orders = await orm_get_awaitings_for_worker(self.session, self.id_worker)
        client = await orm_get_contact_information_id(self.session, self.id_client)
        return f'Услуга - {service.name}\n\n{service.description}\n\nСтоимость - {service.price} руб.\nЗаказано - {orders[self.page].created} {client.id} | tg://openmessage?user_id={client.id}\nИмя: {client.firstName}\nФамилия: {client.lastName}\nНомер телефона: {client.phoneNumber}\nСтатус - {orders[self.page].status}'

    async def get_description_for_client(self):
        service = await orm_get_service(self.session, self.id_service)
        orders = await orm_get_awaitings_for_client(self.session, self.id_client)
        return f'Услуга - {service.name}\n\n{service.description}\nСтоимость - {service.price} руб.\n\nЗаказано - {orders[self.page].created}\nСтатус - {orders[self.page].status}'

    async def get_description_for_finished_worker(self):
        service = await orm_get_service(self.session, self.id_service)
        orders = await orm_get_finished_for_worker(self.session, self.id_worker)
        client = await orm_get_contact_information_id(self.session, self.id_client)
        return f'Услуга - {service.name}\n\n{service.description}\n\nСтоимость - {service.price} руб.\nЗаказано - {orders[self.page].created} {client.id} | tg://openmessage?user_id={client.id}\nИмя: {client.firstName}\nФамилия: {client.lastName}\nНомер телефона: {client.phoneNumber}\nСтатус - {orders[self.page].status}'

    async def get_description_for_finished_client(self):
        service = await orm_get_service(self.session, self.id_service)
        orders = await orm_get_finished_for_clients(self.session, self.id_client)
        client = await orm_get_contact_information_id(self.session, self.id_client)
        return f'Услуга - {service.name}\n\n{service.description}\n\nСтоимость - {service.price} руб.\nЗаказано - {orders[self.page].created} {client.id} | tg://openmessage?user_id={client.id}\nИмя: {client.firstName}\nФамилия: {client.lastName}\nНомер телефона: {client.phoneNumber}\nСтатус - {orders[self.page].status}'


class FeedbackDesc:
    def __init__(self, session: AsyncSession, page: int, id_feedback: int):
        self.session = session
        self.id_feedback = id_feedback
        self.page = page

    async def get_desc_for_client(self):
        feedback = await orm_get_feedback_one(self.session, self.id_feedback)
        awaiting = await orm_get_awaiting_one(self.session, feedback.id_awaiting)
        ci_worker = await orm_get_contact_information_id(self.session, awaiting.id_workers)
        service = await orm_get_service(self.session, awaiting.id_services)
        return f'Отзыв на услугу от {awaiting.updated}\n\nВыполнил {ci_worker.firstName} {ci_worker.lastName} | {ci_worker.phoneNumber}\n\n Услуга {service.name}\n{service.description}\n{service.price} руб.\n\nОценка: {feedback.mark}\nТекст отзыва:\n{feedback.text}'

    async def get_desc_for_worker(self):
        feedback = await orm_get_feedback_one(self.session, self.id_feedback)
        awaiting = await orm_get_awaiting_one(self.session, feedback.id_awaiting)
        ci_client = await orm_get_contact_information_id(self.session, awaiting.id_client)
        service = await orm_get_service(self.session, awaiting.id_services)
        return f'Отзыв на услугу от {awaiting.updated}\n\nКлиент {ci_client.firstName} {ci_client.lastName} | {ci_client.phoneNumber}\n\n Услуга {service.name}\n{service.description}\n{service.price} руб.\n\nОценка: {feedback.mark}\nТекст отзыва:\n{feedback.text}'

    async def get_desc_for_admin(self):
        feedback = await orm_get_feedback_one(self.session, self.id_feedback)
        awaiting = await orm_get_awaiting_one(self.session, feedback.id_awaiting)
        ci_worker = await orm_get_contact_information_id(self.session, awaiting.id_workers)
        ci_client = await orm_get_contact_information_id(self.session, awaiting.id_client)
        service = await orm_get_service(self.session, awaiting.id_services)
        return f'Отзыв на услугу от {awaiting.updated}\n\nКлиент {ci_client.firstName} {ci_client.lastName} | {ci_client.phoneNumber}\nИсполнитель {ci_worker.firstName} {ci_worker.lastName} | {ci_worker.phoneNumber}\n\n Услуга {service.name}\n{service.description}\n{service.price} руб.\n\nОценка: {feedback.mark}\nТекст отзыва:\n{feedback.text}'
