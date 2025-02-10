from sqlalchemy import Text, String, Numeric, ForeignKey, DateTime, func, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    ...


class TypesOfServices(Base):
    __tablename__ = 'types_of_services'

    name: Mapped[str] = mapped_column(String(45), primary_key=True, unique=True)

    description: Mapped[str] = mapped_column(Text)


class Services(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(45))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2))

    name_types_of_services: Mapped[int] = mapped_column(
        ForeignKey('types_of_services.name', ondelete='CASCADE'),
        nullable=False)

    types_of_services: Mapped['TypesOfServices'] = relationship(backref='services')


class ContactInformation(Base):
    __tablename__ = 'contact_information'

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True)

    firstName: Mapped[str] = mapped_column(String(30), nullable=False)
    lastName: Mapped[str] = mapped_column(String(50), nullable=False)
    patronymic: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(Text)
    phoneNumber: Mapped[str] = mapped_column(String(12))

class Client(Base):
    __tablename__ = 'client'

    id_contact_information: Mapped[int] = mapped_column(
        ForeignKey('contact_information.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True)

    status: Mapped[str] = mapped_column(String(100))

    contact_information: Mapped['ContactInformation'] = relationship(backref='client')


class Worker(Base):
    __tablename__ = 'worker'

    id_contact_information: Mapped[int] = mapped_column(
        ForeignKey('contact_information.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True)

    specialty: Mapped[str] = mapped_column(String(70), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)

    contact_information: Mapped['ContactInformation'] = relationship(backref='worker')


class Awaiting(Base):
    __tablename__ = 'awaiting'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    id_services: Mapped[int] = mapped_column(
        ForeignKey('services.id', ondelete='CASCADE'),
        nullable=False)

    id_client: Mapped[int] = mapped_column(
        ForeignKey('client.id_contact_information', ondelete='CASCADE'),
        nullable=False)

    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    status: Mapped[str] = mapped_column(String(40))
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    id_workers: Mapped[int] = mapped_column(
        ForeignKey('worker.id_contact_information', ondelete='CASCADE'),
        nullable=False)

    services: Mapped['Services'] = relationship(backref='awaiting')
    client: Mapped['Client'] = relationship(backref='awaiting')
    worker: Mapped['Worker'] = relationship(backref='awaiting')


class Admins(Base):
    __tablename__ = 'admins'
    
    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())


class Feedback(Base):
    __tablename__ = 'feedback'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    id_awaiting: Mapped[int] = mapped_column(ForeignKey('awaiting.id'), nullable=False)

    mark: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    awaiting: Mapped['Awaiting'] = relationship(backref='feedback')
