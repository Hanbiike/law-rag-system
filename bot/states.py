"""
FSM States for Telegram bot.

This module defines finite state machine states
for managing user conversation flow.
"""
from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """
    User conversation states.

    States:
        selecting_language: User is choosing language.
        selecting_type: User is choosing response type.
        ready: User is ready to send queries.
    """
    selecting_language = State()
    selecting_type = State()
    ready = State()
