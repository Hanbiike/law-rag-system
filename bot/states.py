"""
FSM States for Telegram bot.

This module defines finite state machine states
for managing user conversation flow efficiently.
"""
from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """
    User conversation states.

    Defines the finite state machine states for bot interaction flow.
    
    States:
        selecting_language: User is choosing interface language.
        selecting_type: User is choosing response type (base/pro).
        ready: User is ready to send queries (main operational state).
    """
    
    selecting_language = State()
    selecting_type = State()
    ready = State()
