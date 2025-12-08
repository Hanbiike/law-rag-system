"""
Message and callback handlers for Telegram bot.

This module contains all handlers for processing user messages,
callbacks, and documents. Uses MySQL database for user data storage.
"""
import base64
import logging
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards import (
    get_language_keyboard,
    get_response_type_keyboard,
    get_main_reply_keyboard,
    get_settings_inline_keyboard
)
from bot.messages import (
    get_message,
    SETTINGS_BUTTON_RU,
    SETTINGS_BUTTON_KG
)
from bot.states import UserState
from databases.db import user_repository
from searchers.search import ProLawRAGSearch

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = Router()

# Initialize searcher
searcher = ProLawRAGSearch(top_k=3, n_llm_questions=10)

# Maximum document size (20 MB)
MAX_DOC_SIZE = 20 * 1024 * 1024

# Cost per query type
COST_BASE = 1      # Base text query cost
COST_PRO = 2       # Pro text query cost
COST_DOCUMENT = 3  # Document query cost


def get_query_cost(response_type: str, is_document: bool = False) -> int:
    """
    Calculate query cost based on type.

    Parameters:
        response_type (str): Response type ('base' or 'pro').
        is_document (bool): Whether this is a document query.

    Returns:
        int: Cost in balance units.
    """
    if is_document:
        return COST_DOCUMENT
    if response_type == 'pro':
        return COST_PRO
    return COST_BASE


def get_user_data(telegram_id: int) -> Optional[dict]:
    """
    Get user data from database.

    Parameters:
        telegram_id (int): User's Telegram ID.

    Returns:
        Optional[dict]: User data or None.
    """
    return user_repository.get_user_with_response_type(telegram_id)


def ensure_user_exists(telegram_id: int) -> dict:
    """
    Ensure user exists in database, create if not.

    Parameters:
        telegram_id (int): User's Telegram ID.

    Returns:
        dict: User data.
    """
    user = user_repository.get_or_create_user(telegram_id)
    if user:
        # Get full user data with response_type
        return user_repository.get_user_with_response_type(telegram_id) or user
    return {'lang': 'ru', 'response_type': 'base', 'balance': 10}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Handle /start command.

    For new users: starts onboarding (language -> type selection).
    For existing users: shows settings to reconfigure (language -> type).
    Balance is preserved for existing users.

    Parameters:
        message (Message): Incoming message object.
        state (FSMContext): FSM context for state management.
    """
    await state.clear()
    telegram_id = message.from_user.id

    # Check if user exists
    user = get_user_data(telegram_id)

    if user:
        # Existing user - show language selection for reconfiguration
        # Mark as existing user in state to preserve balance
        await state.update_data(is_existing_user=True)
        lang = user.get('lang', 'ru')

        await state.set_state(UserState.selecting_language)
        await message.answer(
            get_message('welcome', lang),
            reply_markup=get_language_keyboard()
        )
    else:
        # New user, start onboarding
        await state.set_state(UserState.selecting_language)
        await message.answer(
            get_message('welcome', 'ru'),
            reply_markup=get_language_keyboard()
        )


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Handle language selection callback.

    Parameters:
        callback (CallbackQuery): Callback query object.
        state (FSMContext): FSM context for state management.
    """
    lang = callback.data.split("_")[1]
    telegram_id = callback.from_user.id

    user = get_user_data(telegram_id)

    # Update or create user with selected language
    if user:
        user_repository.update_lang(telegram_id, lang)
    else:
        user_repository.add_user(telegram_id, lang=lang)

    await state.update_data(lang=lang)
    await state.set_state(UserState.selecting_type)

    await callback.message.edit_text(
        get_message('select_type', lang),
        reply_markup=get_response_type_keyboard(lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("type_"))
async def process_type_selection(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Handle response type selection callback.

    Parameters:
        callback (CallbackQuery): Callback query object.
        state (FSMContext): FSM context for state management.
    """
    response_type = callback.data.split("_")[1]
    telegram_id = callback.from_user.id

    # Update user response type
    user_repository.update_response_type(telegram_id, response_type)

    # Get updated user data
    user = get_user_data(telegram_id)
    lang = user.get('lang', 'ru') if user else 'ru'
    balance = user.get('balance', 10) if user else 10

    await state.set_state(UserState.ready)

    mode_name = get_message(f"mode_{response_type}", lang)

    # Edit the inline message to show confirmation
    await callback.message.edit_text(
        get_message('type_changed', lang, mode=mode_name),
        parse_mode="Markdown"
    )

    # Send ready message with reply keyboard
    await callback.message.answer(
        get_message('ready', lang, mode=mode_name, balance=balance),
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(F.text.in_([SETTINGS_BUTTON_RU, SETTINGS_BUTTON_KG]))
async def process_settings_button(message: Message, state: FSMContext) -> None:
    """
    Handle settings reply button press.

    Parameters:
        message (Message): Incoming message object.
        state (FSMContext): FSM context for state management.
    """
    telegram_id = message.from_user.id
    user = get_user_data(telegram_id)

    if not user:
        user = ensure_user_exists(telegram_id)

    lang = user.get('lang', 'ru')
    response_type = user.get('response_type', 'base')
    balance = user.get('balance', 0)
    mode_name = get_message(f"mode_{response_type}", lang)

    await state.set_state(UserState.ready)

    await message.answer(
        get_message('settings_menu', lang, mode=mode_name, balance=balance),
        reply_markup=get_settings_inline_keyboard(lang),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "change_lang")
async def process_change_lang(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Handle change language callback from settings.

    Parameters:
        callback (CallbackQuery): Callback query object.
        state (FSMContext): FSM context for state management.
    """
    telegram_id = callback.from_user.id
    user = get_user_data(telegram_id)
    lang = user.get('lang', 'ru') if user else 'ru'

    await callback.message.edit_text(
        get_message('select_new_lang', lang),
        reply_markup=get_language_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "change_type")
async def process_change_type(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """
    Handle change response type callback from settings.

    Parameters:
        callback (CallbackQuery): Callback query object.
        state (FSMContext): FSM context for state management.
    """
    telegram_id = callback.from_user.id
    user = get_user_data(telegram_id)
    lang = user.get('lang', 'ru') if user else 'ru'

    await callback.message.edit_text(
        get_message('select_new_type', lang),
        reply_markup=get_response_type_keyboard(lang)
    )
    await callback.answer()


@router.message(UserState.ready, F.text)
async def process_text_query(message: Message, state: FSMContext) -> None:
    """
    Handle text message queries.

    Parameters:
        message (Message): Incoming message object.
        state (FSMContext): FSM context for state management.
    """
    # Skip settings button (handled by separate handler)
    if message.text in [SETTINGS_BUTTON_RU, SETTINGS_BUTTON_KG]:
        return

    telegram_id = message.from_user.id
    user = get_user_data(telegram_id)

    if not user:
        user = ensure_user_exists(telegram_id)

    lang = user.get('lang', 'ru')
    response_type = user.get('response_type', 'base')
    balance = user.get('balance', 0)

    # Calculate query cost based on type
    query_cost = get_query_cost(response_type, is_document=False)

    # Check balance
    if balance < query_cost:
        await message.answer(
            get_message('insufficient_balance', lang, balance=balance),
            parse_mode="Markdown"
        )
        return

    # Send processing message
    processing_msg = await message.answer(get_message('processing', lang))

    try:
        # Deduct balance
        user_repository.update_balance(telegram_id, -query_cost)

        # Get response from RAG system
        response = await get_rag_response(
            query=message.text,
            response_type=response_type,
            lang=lang
        )

        if response:
            # Delete processing message
            await processing_msg.delete()
            # Send response (split if too long)
            await send_long_message(message, response, lang)
        else:
            # Refund balance on failure
            user_repository.update_balance(telegram_id, query_cost)
            await processing_msg.edit_text(get_message('no_response', lang))

    except Exception as e:
        logger.error(f"Error processing text query: {e}")
        # Refund balance on error
        user_repository.update_balance(telegram_id, query_cost)
        await processing_msg.edit_text(get_message('error', lang))


@router.message(UserState.ready, F.document)
async def process_document(
    message: Message,
    state: FSMContext,
    bot: Bot
) -> None:
    """
    Handle document uploads.

    Converts document to base64 and processes it.

    Parameters:
        message (Message): Incoming message object.
        state (FSMContext): FSM context for state management.
        bot (Bot): Bot instance for file operations.
    """
    telegram_id = message.from_user.id
    user = get_user_data(telegram_id)

    if not user:
        user = ensure_user_exists(telegram_id)

    lang = user.get('lang', 'ru')
    response_type = user.get('response_type', 'base')
    balance = user.get('balance', 0)

    document = message.document

    # Check file size
    if document.file_size > MAX_DOC_SIZE:
        await message.answer(get_message('doc_too_large', lang))
        return

    # Check file format (only PDF supported)
    if document.mime_type != 'application/pdf':
        await message.answer(get_message('unsupported_format', lang))
        return

    # Document query cost
    query_cost = COST_DOCUMENT

    # Check balance
    if balance < query_cost:
        await message.answer(
            get_message('insufficient_balance', lang, balance=balance),
            parse_mode="Markdown"
        )
        return

    # Send processing message
    processing_msg = await message.answer(get_message('processing_doc', lang))

    try:
        # Deduct balance
        user_repository.update_balance(telegram_id, -query_cost)

        # Download file
        file = await bot.get_file(document.file_id)
        file_data = await bot.download_file(file.file_path)

        # Convert to base64
        file_bytes = file_data.read()
        document_base64 = base64.b64encode(file_bytes).decode('utf-8')

        # Get query from caption or default
        query = message.caption or get_default_doc_query(lang)

        # Get response from RAG system
        response = await get_rag_response_from_doc(
            query=query,
            document_base64=document_base64,
            response_type=response_type,
            lang=lang
        )

        if response:
            await processing_msg.delete()
            await send_long_message(message, response, lang)
        else:
            # Refund balance on failure
            user_repository.update_balance(telegram_id, query_cost)
            await processing_msg.edit_text(get_message('no_response', lang))

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        # Refund balance on error
        user_repository.update_balance(telegram_id, query_cost)
        await processing_msg.edit_text(get_message('error', lang))


@router.message(UserState.selecting_language)
@router.message(UserState.selecting_type)
async def process_invalid_state_message(
    message: Message,
    state: FSMContext
) -> None:
    """
    Handle messages sent during selection states.

    Parameters:
        message (Message): Incoming message object.
        state (FSMContext): FSM context for state management.
    """
    current_state = await state.get_state()
    telegram_id = message.from_user.id
    user = get_user_data(telegram_id)
    lang = user.get('lang', 'ru') if user else 'ru'

    if current_state == UserState.selecting_language:
        await message.answer(
            get_message('welcome', lang),
            reply_markup=get_language_keyboard()
        )
    elif current_state == UserState.selecting_type:
        await message.answer(
            get_message('select_type', lang),
            reply_markup=get_response_type_keyboard(lang),
            parse_mode="Markdown"
        )


@router.message(F.text)
async def process_text_without_state(
    message: Message,
    state: FSMContext
) -> None:
    """
    Handle text messages when user has no state (e.g., after bot restart).

    Parameters:
        message (Message): Incoming message object.
        state (FSMContext): FSM context for state management.
    """
    # Handle settings button
    if message.text in [SETTINGS_BUTTON_RU, SETTINGS_BUTTON_KG]:
        await process_settings_button(message, state)
        return

    telegram_id = message.from_user.id
    user = get_user_data(telegram_id)

    if user:
        # User exists, set ready state and process
        await state.set_state(UserState.ready)
        await process_text_query(message, state)
    else:
        # New user, start onboarding
        await state.set_state(UserState.selecting_language)
        await message.answer(
            get_message('welcome', 'ru'),
            reply_markup=get_language_keyboard()
        )


@router.message(F.document)
async def process_document_without_state(
    message: Message,
    state: FSMContext,
    bot: Bot
) -> None:
    """
    Handle document messages when user has no state.

    Parameters:
        message (Message): Incoming message object.
        state (FSMContext): FSM context for state management.
        bot (Bot): Bot instance for file operations.
    """
    telegram_id = message.from_user.id
    user = get_user_data(telegram_id)

    if user:
        await state.set_state(UserState.ready)
        await process_document(message, state, bot)
    else:
        await state.set_state(UserState.selecting_language)
        await message.answer(
            get_message('welcome', 'ru'),
            reply_markup=get_language_keyboard()
        )


async def get_rag_response(
    query: str,
    response_type: str,
    lang: str
) -> Optional[str]:
    """
    Get response from RAG system for text query.

    Parameters:
        query (str): User's text query.
        response_type (str): Response type ('base' or 'pro').
        lang (str): Language code ('ru' or 'kg').

    Returns:
        Optional[str]: Response text or None if error.
    """
    try:
        response = await searcher.get_response_text(
            query=query,
            type=response_type,
            lang=lang
        )
        return response
    except Exception as e:
        logger.error(f"RAG response error: {e}")
        return None


async def get_rag_response_from_doc(
    query: str,
    document_base64: str,
    response_type: str,
    lang: str
) -> Optional[str]:
    """
    Get response from RAG system for document query.

    Parameters:
        query (str): User's text query about the document.
        document_base64 (str): Base64 encoded document.
        response_type (str): Response type ('base' or 'pro').
        lang (str): Language code ('ru' or 'kg').

    Returns:
        Optional[str]: Response text or None if error.
    """
    try:
        response = await searcher.get_response_from_doc_text(
            query=query,
            document_base64=document_base64,
            type=response_type,
            lang=lang
        )
        return response
    except Exception as e:
        logger.error(f"RAG document response error: {e}")
        return None


def get_default_doc_query(lang: str) -> str:
    """
    Get default query for document analysis.

    Parameters:
        lang (str): Language code ('ru' or 'kg').

    Returns:
        str: Default query string.
    """
    if lang == 'ru':
        return (
            "Проанализируй этот документ и проверь "
            "его на соответствие законодательству."
        )
    return "Бул документти талдап, мыйзамдарга шайкештигин текшериңиз."


async def send_long_message(
    message: Message,
    text: str,
    lang: str,
    max_length: int = 4096
) -> None:
    """
    Send long message by splitting into chunks if needed.

    Parameters:
        message (Message): Message object to reply to.
        text (str): Text to send.
        lang (str): Language code for keyboard.
        max_length (int): Maximum message length (Telegram limit).
    """
    if len(text) <= max_length:
        await message.answer(
            text,
            parse_mode="Markdown"
        )
    else:
        # Split message into chunks
        chunks = [
            text[i:i + max_length]
            for i in range(0, len(text), max_length)
        ]
        for chunk in chunks:
            await message.answer(chunk, parse_mode="Markdown")
