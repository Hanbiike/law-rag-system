"""
Keyboard layouts for Telegram bot.

This module contains optimized inline keyboard markups used in the bot
with caching for frequently used keyboards.
"""
from functools import lru_cache
from typing import Final

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)

# Button text constants
LANG_RU_TEXT: Final[str] = "🇷🇺 Русский"
LANG_KG_TEXT: Final[str] = "🇰🇬 Кыргызча"

# Keyboard button texts by language
KEYBOARD_TEXTS: Final[dict] = {
    'ru': {
        'base': "📝 Базовый",
        'pro': "⚡ Продвинутый",
        'settings': "⚙️ Настройки",
        'change_lang': "🌐 Сменить язык",
        'change_type': "📋 Сменить режим"
    },
    'kg': {
        'base': "📝 Негизги",
        'pro': "⚡ Кеңейтилген",
        'settings': "⚙️ Жөндөөлөр",
        'change_lang': "🌐 Тилди өзгөртүү",
        'change_type': "📋 Режимди өзгөртүү"
    }
}

# Pre-built language keyboard (constant, can be cached)
_LANGUAGE_KEYBOARD: Final[InlineKeyboardMarkup] = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text=LANG_RU_TEXT, callback_data="lang_ru"),
            InlineKeyboardButton(text=LANG_KG_TEXT, callback_data="lang_kg")
        ]
    ]
)

# Singleton keyboard remover
_KEYBOARD_REMOVER: Final[ReplyKeyboardRemove] = ReplyKeyboardRemove()


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Get inline keyboard for language selection.
    
    Returns pre-built singleton keyboard for efficiency.

    Returns:
        InlineKeyboardMarkup: Keyboard with language options.
    """
    return _LANGUAGE_KEYBOARD


@lru_cache(maxsize=4)
def get_response_type_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Create inline keyboard for response type selection.
    
    Cached per language for performance.

    Parameters:
        lang (str): Language code ('ru' or 'kg').

    Returns:
        InlineKeyboardMarkup: Keyboard with response type options.
    """
    texts = KEYBOARD_TEXTS.get(lang, KEYBOARD_TEXTS['ru'])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=texts['base'], callback_data="type_base"),
            InlineKeyboardButton(text=texts['pro'], callback_data="type_pro")
        ]
    ])


@lru_cache(maxsize=4)
def get_main_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Create reply keyboard with settings button.
    
    Cached per language for performance.

    Parameters:
        lang (str): Language code ('ru' or 'kg').

    Returns:
        ReplyKeyboardMarkup: Keyboard with settings button.
    """
    texts = KEYBOARD_TEXTS.get(lang, KEYBOARD_TEXTS['ru'])
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts['settings'])]
        ],
        resize_keyboard=True,
        is_persistent=True
    )


@lru_cache(maxsize=4)
def get_settings_inline_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Create inline keyboard for settings menu.
    
    Cached per language for performance.

    Parameters:
        lang (str): Language code ('ru' or 'kg').

    Returns:
        InlineKeyboardMarkup: Keyboard with settings options.
    """
    texts = KEYBOARD_TEXTS.get(lang, KEYBOARD_TEXTS['ru'])
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=texts['change_lang'], callback_data="change_lang")],
        [InlineKeyboardButton(text=texts['change_type'], callback_data="change_type")]
    ])


def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Get keyboard remover.
    
    Returns singleton for efficiency.

    Returns:
        ReplyKeyboardRemove: Object to remove keyboard.
    """
    return _KEYBOARD_REMOVER
