"""
Keyboard layouts for Telegram bot.

This module contains all inline keyboard markups used in the bot
for language selection and response type selection.
"""
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard for language selection.

    Returns:
        InlineKeyboardMarkup: Keyboard with language options (Russian, Kyrgyz).
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang_kg")
        ]
    ])
    return keyboard


def get_response_type_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Create inline keyboard for response type selection.

    Parameters:
        lang (str): Language code ('ru' or 'kg') for button labels.

    Returns:
        InlineKeyboardMarkup: Keyboard with response type options (Base, Pro).
    """
    if lang == 'ru':
        base_text = "📝 Базовый"
        pro_text = "⚡ Продвинутый"
    else:
        base_text = "📝 Негизги"
        pro_text = "⚡ Кеңейтилген"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=base_text, callback_data="type_base"),
            InlineKeyboardButton(text=pro_text, callback_data="type_pro")
        ]
    ])
    return keyboard


def get_main_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Create reply keyboard with settings button.

    Parameters:
        lang (str): Language code ('ru' or 'kg') for button label.

    Returns:
        ReplyKeyboardMarkup: Keyboard with settings button.
    """
    if lang == 'ru':
        settings_text = "⚙️ Настройки"
    else:
        settings_text = "⚙️ Жөндөөлөр"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=settings_text)]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
    return keyboard


def get_settings_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Create inline keyboard for settings menu.

    Parameters:
        lang (str): Language code ('ru' or 'kg') for button labels.

    Returns:
        InlineKeyboardMarkup: Keyboard with language and type change options.
    """
    if lang == 'ru':
        change_lang_text = "🌐 Сменить язык"
        change_type_text = "📋 Сменить режим"
    else:
        change_lang_text = "🌐 Тилди өзгөртүү"
        change_type_text = "📋 Режимди өзгөртүү"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=change_lang_text, callback_data="change_lang")],
        [InlineKeyboardButton(text=change_type_text, callback_data="change_type")]
    ])
    return keyboard


def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Remove reply keyboard.

    Returns:
        ReplyKeyboardRemove: Object to remove keyboard.
    """
    return ReplyKeyboardRemove()
