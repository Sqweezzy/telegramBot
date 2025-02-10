from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


del_kbd = ReplyKeyboardRemove()


def get_inline_kb(
        *,
        btns: dict[str, str],
        sizes: tuple = (2,),
        row_btn: tuple[str, str] = None,
        row_btn2: tuple[str, str] = None,
):
    keyboard = InlineKeyboardBuilder()
    for text, cmd in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=cmd))
    if row_btn is not None:
        keyboard.row(InlineKeyboardButton(text=row_btn[0], callback_data=row_btn[-1]))
    if row_btn2 is not None:
        keyboard.row(InlineKeyboardButton(text=row_btn2[0], callback_data=row_btn2[-1]))
    return keyboard.adjust(*sizes).as_markup()


def get_keyboard(
        *btns: str,
        placeholder: str = None,
        request_contact: int = None,
        request_location: int = None,
        sizes: tuple[int] = (2,),
):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text='Отправить номер телефона от телеграма', request_contact=True))
    keyboard.adjust(2).as_markup(resize_keyboard=True)

    for index, text in enumerate(btns, start=0):
        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))
        elif request_location and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
        resize_keyboard=True, input_field_placeholder=placeholder)

remove_keyboard = ReplyKeyboardRemove()
