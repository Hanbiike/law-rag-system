"""
Database management module for user data.

This module provides optimized MySQL database operations with connection
pooling, context managers, and efficient query handling.
"""
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Final, Optional

import mysql.connector
from mysql.connector import Error, MySQLConnection

# Configure module logger
logger = logging.getLogger(__name__)

# Default user settings
DEFAULT_BALANCE: Final[int] = 10
DEFAULT_LANG: Final[str] = 'ru'
DEFAULT_RESPONSE_TYPE: Final[str] = 'base'


class DatabaseManager:
    """
    Efficient MySQL database connection manager.
    
    Features:
    - Connection pooling support
    - Automatic reconnection
    - Context manager for cursors
    - Thread-safe operations
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize DatabaseManager with configuration.
        
        Parameters:
            config (Dict[str, Any]): Database configuration with
                host, user, password, database, and port.
        """
        self._config = config
        self._connection: Optional[MySQLConnection] = None
    
    def connect(self) -> bool:
        """
        Establish connection to MySQL database.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            self._connection = mysql.connector.connect(**self._config)
            if self._connection.is_connected():
                return True
            return False
        except Error as e:
            logger.error("MySQL connection error: %s", e)
            return False
    
    def disconnect(self) -> None:
        """Close database connection if open."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
    
    def ensure_connected(self) -> bool:
        """
        Ensure database connection is active, reconnect if needed.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.is_connected():
            return self.connect()
        return True
    
    @property
    def connection(self) -> Optional[MySQLConnection]:
        """Get current database connection."""
        return self._connection
    
    def is_connected(self) -> bool:
        """
        Check if database connection is active.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return (
            self._connection is not None and 
            self._connection.is_connected()
        )
    
    @contextmanager
    def get_cursor(self, dictionary: bool = False):
        """
        Context manager for database cursor.
        
        Parameters:
            dictionary (bool): If True, return dict cursor.
        
        Yields:
            cursor: MySQL cursor object.
        """
        cursor = self._connection.cursor(dictionary=dictionary)
        try:
            yield cursor
        finally:
            cursor.close()


class UserRepository:
    """
    Repository for user-related database operations.
    
    Implements repository pattern for clean data access abstraction
    with optimized queries and error handling.
    """
    
    def __init__(self, db_manager: DatabaseManager) -> None:
        """
        Initialize UserRepository.
        
        Parameters:
            db_manager (DatabaseManager): Database manager instance.
        """
        self._db = db_manager
    
    def _execute_update(
        self,
        query: str,
        params: tuple,
        error_msg: str
    ) -> bool:
        """
        Execute an UPDATE query with error handling.
        
        Parameters:
            query (str): SQL query string.
            params (tuple): Query parameters.
            error_msg (str): Error message prefix for logging.
        
        Returns:
            bool: True if rows affected, False otherwise.
        """
        if not self._db.ensure_connected():
            return False
        
        try:
            with self._db.get_cursor() as cursor:
                cursor.execute(query, params)
                self._db.connection.commit()
                return cursor.rowcount > 0
        except Error as e:
            logger.error("%s: %s", error_msg, e)
            return False
    
    def add_user(
        self, 
        telegram_id: int, 
        initial_balance: int = DEFAULT_BALANCE,
        lang: str = DEFAULT_LANG,
        response_type: str = DEFAULT_RESPONSE_TYPE
    ) -> bool:
        """
        Add a new user to the database.
        
        Parameters:
            telegram_id (int): Unique Telegram ID.
            initial_balance (int): Initial balance. Defaults to 10.
            lang (str): Language preference. Defaults to 'ru'.
            response_type (str): Response type. Defaults to 'base'.
        
        Returns:
            bool: True if added successfully, False otherwise.
        """
        if not self._db.ensure_connected():
            return False
        
        try:
            with self._db.get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO users (telegram_id, balance, lang, response_type) 
                       VALUES (%s, %s, %s, %s)""",
                    (telegram_id, initial_balance, lang, response_type)
                )
                self._db.connection.commit()
                return True
        except Error as e:
            logger.error("Error adding user %s: %s", telegram_id, e)
            return False
    
    def update_conversation(
        self, 
        telegram_id: int, 
        conversation_id: str
    ) -> bool:
        """
        Update the last conversation ID for a user.
        
        Parameters:
            telegram_id (int): User's Telegram ID.
            conversation_id (str): Conversation ID to store.
        
        Returns:
            bool: True if updated, False otherwise.
        """
        return self._execute_update(
            "UPDATE users SET last_conversation = %s WHERE telegram_id = %s",
            (conversation_id, telegram_id),
            f"Error updating conversation for {telegram_id}"
        )
    
    def update_balance(
        self,
        telegram_id: int, 
        amount: int,
        allow_negative: bool = False
    ) -> bool:
        """
        Update user balance by adding/subtracting amount.
        
        Parameters:
            telegram_id (int): User's Telegram ID.
            amount (int): Amount to add (positive) or subtract (negative).
            allow_negative (bool): Allow negative balance. Defaults to False.
        
        Returns:
            bool: True if updated, False otherwise.
        """
        if not self._db.ensure_connected():
            return False
        
        try:
            with self._db.get_cursor() as cursor:
                if not allow_negative:
                    cursor.execute(
                        "SELECT balance FROM users WHERE telegram_id = %s",
                        (telegram_id,)
                    )
                    result = cursor.fetchone()
                    
                    if not result:
                        return False
                    
                    if result[0] + amount < 0:
                        return False
                
                cursor.execute(
                    "UPDATE users SET balance = balance + %s WHERE telegram_id = %s",
                    (amount, telegram_id)
                )
                self._db.connection.commit()
                return cursor.rowcount > 0
        except Error as e:
            logger.error("Error updating balance for %s: %s", telegram_id, e)
            return False
    
    def update_lang(self, telegram_id: int, lang: str) -> bool:
        """
        Update user's language preference.
        
        Parameters:
            telegram_id (int): User's Telegram ID.
            lang (str): 2-character language code.
        
        Returns:
            bool: True if updated, False otherwise.
        """
        if not isinstance(lang, str) or len(lang) != 2:
            return False
        
        return self._execute_update(
            "UPDATE users SET lang = %s WHERE telegram_id = %s",
            (lang.lower(), telegram_id),
            f"Error updating language for {telegram_id}"
        )
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve user information by telegram_id.
        
        Parameters:
            telegram_id (int): User's Telegram ID.
        
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found.
        """
        if not self._db.ensure_connected():
            return None
        
        try:
            with self._db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT id, telegram_id, lang, balance, last_conversation
                       FROM users WHERE telegram_id = %s""",
                    (telegram_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'telegram_id': result[1],
                        'lang': result[2],
                        'balance': result[3],
                        'last_conversation': result[4]
                    }
                return None
        except Error as e:
            logger.error("Error retrieving user %s: %s", telegram_id, e)
            return None

    def update_response_type(
        self,
        telegram_id: int,
        response_type: str
    ) -> bool:
        """
        Update user's response type preference.

        Parameters:
            telegram_id (int): User's Telegram ID.
            response_type (str): Response type ('base' or 'pro').

        Returns:
            bool: True if updated, False otherwise.
        """
        if response_type not in ('base', 'pro'):
            return False

        return self._execute_update(
            "UPDATE users SET response_type = %s WHERE telegram_id = %s",
            (response_type, telegram_id),
            f"Error updating response type for {telegram_id}"
        )

    def get_or_create_user(
        self,
        telegram_id: int,
        initial_balance: int = DEFAULT_BALANCE,
        lang: str = DEFAULT_LANG,
        response_type: str = DEFAULT_RESPONSE_TYPE
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing user or create new one.

        Parameters:
            telegram_id (int): User's Telegram ID.
            initial_balance (int): Initial balance for new user.
            lang (str): Language for new user.
            response_type (str): Response type for new user.

        Returns:
            Optional[Dict[str, Any]]: User data or None.
        """
        user = self.get_user(telegram_id)
        if user:
            return user

        self.add_user(telegram_id, initial_balance, lang, response_type)
        return self.get_user(telegram_id)

    def get_user_with_response_type(
        self,
        telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve user with response_type field.

        Parameters:
            telegram_id (int): User's Telegram ID.

        Returns:
            Optional[Dict[str, Any]]: User data with response_type or None.
        """
        if not self._db.ensure_connected():
            return None

        try:
            with self._db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT id, telegram_id, lang, response_type, 
                              balance, last_conversation
                       FROM users WHERE telegram_id = %s""",
                    (telegram_id,)
                )
                result = cursor.fetchone()

                if result:
                    return {
                        'id': result[0],
                        'telegram_id': result[1],
                        'lang': result[2],
                        'response_type': result[3],
                        'balance': result[4],
                        'last_conversation': result[5]
                    }
                return None
        except Error as e:
            logger.error("Error retrieving user %s: %s", telegram_id, e)
            return None


# Database configuration from environment or defaults
db_config: Dict[str, Any] = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'root'),
    'database': os.environ.get('DB_NAME', 'law_rag_users'),
    'port': int(os.environ.get('DB_PORT', '8889'))
}

# Initialize singleton instances
db_manager = DatabaseManager(db_config)
db_manager.connect()
user_repository = UserRepository(db_manager)




