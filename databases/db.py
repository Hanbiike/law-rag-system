import mysql.connector
from mysql.connector import Error, MySQLConnection
from typing import Optional, Dict, Any
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages MySQL database connections and provides connection pooling.
    
    This class handles the lifecycle of database connections including
    creation, validation, and cleanup.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DatabaseManager with configuration.
        
        Parameters:
        config (Dict[str, Any]): Database configuration dictionary
            containing host, user, password, database, and port.
        """
        self.config = config
        self._connection: Optional[MySQLConnection] = None
    
    def connect(self) -> bool:
        """
        Establish a connection to the MySQL database.
        
        Returns:
        bool: True if connection successful, False otherwise.
        """
        try:
            self._connection = mysql.connector.connect(**self.config)
            if self._connection.is_connected():
                print("Successfully connected to MySQL database")
                return True
            return False
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close the database connection if it's open."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            print("MySQL connection closed")
    
    @property
    def connection(self) -> Optional[MySQLConnection]:
        """
        Get the current database connection.
        
        Returns:
        Optional[MySQLConnection]: The active connection or None.
        """
        return self._connection
    
    def is_connected(self) -> bool:
        """
        Check if database connection is active.
        
        Returns:
        bool: True if connected, False otherwise.
        """
        return (self._connection is not None and 
                self._connection.is_connected())
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor.
        
        Yields:
        cursor: MySQL cursor object.
        
        Note:
        Automatically closes cursor after use.
        """
        cursor = self._connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()


class UserRepository:
    """
    Repository class for user-related database operations.
    
    This class provides methods for CRUD operations on the users table,
    following the repository pattern for data access abstraction.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize UserRepository with a database manager.
        
        Parameters:
        db_manager (DatabaseManager): Database manager instance.
        """
        self.db = db_manager
    
    def add_user(
        self, 
        telegram_id: int, 
        initial_balance: int = 10,
        lang: str = 'ru'
    ) -> bool:
        """
        Add a new user to the database.
        
        Parameters:
        telegram_id (int): Unique Telegram ID of the user.
        initial_balance (int): Initial balance. Defaults to 10.
        lang (str): Language preference. Defaults to 'ru'.
        
        Returns:
        bool: True if user added successfully, False otherwise.
        
        Note:
        Returns False if user with given telegram_id already exists
        due to UNIQUE constraint.
        """
        if not self.db.is_connected():
            print("Database not connected")
            return False
        
        try:
            with self.db.get_cursor() as cursor:
                query = """
                    INSERT INTO users (telegram_id, balance, lang) 
                    VALUES (%s, %s, %s)
                """
                cursor.execute(
                    query, 
                    (telegram_id, initial_balance, lang)
                )
                self.db.connection.commit()
                print(
                    f"User with telegram_id {telegram_id} "
                    f"added successfully"
                )
                return True
        except Error as e:
            print(f"Error adding user: {e}")
            return False
    
    def update_conversation(
        self, 
        telegram_id: int, 
        conversation_id: str
    ) -> bool:
        """
        Update the last conversation ID for a specific user.
        
        Parameters:
        telegram_id (int): The Telegram ID of the user.
        conversation_id (str): The conversation ID to store.
        
        Returns:
        bool: True if update successful, False otherwise.
        
        Note:
        Returns False if user doesn't exist.
        """
        if not self.db.is_connected():
            print("Database not connected")
            return False
        
        try:
            with self.db.get_cursor() as cursor:
                query = """
                    UPDATE users 
                    SET last_conversation = %s 
                    WHERE telegram_id = %s
                """
                cursor.execute(query, (conversation_id, telegram_id))
                self.db.connection.commit()
                
                rows_affected = cursor.rowcount
                
                if rows_affected > 0:
                    print(f"Conversation updated for user {telegram_id}")
                    return True
                else:
                    print(f"No user found with telegram_id {telegram_id}")
                    return False
        except Error as e:
            print(f"Error updating conversation: {e}")
            return False
    
    def update_balance(
        self,
        telegram_id: int, 
        amount: int,
        allow_negative: bool = False
    ) -> bool:
        """
        Update the balance for a specific user.
        
        Modifies user's balance by adding the specified amount.
        Amount can be positive (increase) or negative (decrease).
        
        Parameters:
        telegram_id (int): The Telegram ID of the user.
        amount (int): Amount to add to current balance.
        allow_negative (bool): If False, prevents negative balance.
            Defaults to False.
        
        Returns:
        bool: True if update successful, False otherwise.
        
        Note:
        - Returns False if user doesn't exist.
        - If allow_negative is False and operation would result in
          negative balance, update is rolled back and returns False.
        
        Examples:
        >>> user_repo.update_balance(123456, 5)  # Add 5
        >>> user_repo.update_balance(123456, -3)  # Subtract 3
        """
        if not self.db.is_connected():
            print("Database not connected")
            return False
        
        try:
            self.db.connection.start_transaction()
            
            with self.db.get_cursor() as cursor:
                # Check current balance if needed
                if not allow_negative:
                    cursor.execute(
                        "SELECT balance FROM users "
                        "WHERE telegram_id = %s",
                        (telegram_id,)
                    )
                    result = cursor.fetchone()
                    
                    if not result:
                        self.db.connection.rollback()
                        print(
                            f"No user found with telegram_id "
                            f"{telegram_id}"
                        )
                        return False
                    
                    current_balance = result[0]
                    new_balance = current_balance + amount
                    
                    if new_balance < 0:
                        self.db.connection.rollback()
                        print(
                            f"Insufficient balance for user "
                            f"{telegram_id}. Current: {current_balance}, "
                            f"Attempted: {amount}"
                        )
                        return False
                
                # Update balance
                query = """
                    UPDATE users 
                    SET balance = balance + %s 
                    WHERE telegram_id = %s
                """
                cursor.execute(query, (amount, telegram_id))
                
                rows_affected = cursor.rowcount
                
                if rows_affected > 0:
                    self.db.connection.commit()
                    print(
                        f"Balance updated for user {telegram_id} "
                        f"by {amount}"
                    )
                    return True
                else:
                    self.db.connection.rollback()
                    print(
                        f"No user found with telegram_id {telegram_id}"
                    )
                    return False
                    
        except Error as e:
            if self.db.connection:
                self.db.connection.rollback()
            print(f"Error updating balance: {e}")
            return False
    
    def update_lang(self, telegram_id: int, lang: str) -> bool:
        """
        Update the language preference for a specific user.
        
        Parameters:
        telegram_id (int): The Telegram ID of the user.
        lang (str): Language code (e.g., 'ru', 'en', 'uz').
            Must be 2-character ISO language code.
        
        Returns:
        bool: True if update successful, False otherwise.
        
        Note:
        - Returns False if user doesn't exist.
        - Language code is validated to be exactly 2 characters.
        - Common codes: 'ru' (Russian), 'en' (English),
          'uz' (Uzbek), 'kk' (Kazakh).
        """
        if not self.db.is_connected():
            print("Database not connected")
            return False
        
        # Validate language code format
        if not isinstance(lang, str) or len(lang) != 2:
            print(
                f"Invalid language code: {lang}. "
                f"Must be 2 characters."
            )
            return False
        
        try:
            with self.db.get_cursor() as cursor:
                query = """
                    UPDATE users 
                    SET lang = %s 
                    WHERE telegram_id = %s
                """
                cursor.execute(query, (lang.lower(), telegram_id))
                self.db.connection.commit()
                
                rows_affected = cursor.rowcount
                
                if rows_affected > 0:
                    print(
                        f"Language updated to '{lang}' "
                        f"for user {telegram_id}"
                    )
                    return True
                else:
                    print(
                        f"No user found with telegram_id {telegram_id}"
                    )
                    return False
        except Error as e:
            print(f"Error updating language: {e}")
            return False
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve user information by telegram_id.
        
        Parameters:
        telegram_id (int): The Telegram ID of the user.
        
        Returns:
        Optional[Dict[str, Any]]: User data dictionary or None if not
            found. Dictionary contains: id, telegram_id, lang, balance,
            last_conversation.
        """
        if not self.db.is_connected():
            print("Database not connected")
            return None
        
        try:
            with self.db.get_cursor() as cursor:
                query = """
                    SELECT id, telegram_id, lang, balance, 
                           last_conversation
                    FROM users 
                    WHERE telegram_id = %s
                """
                cursor.execute(query, (telegram_id,))
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
            print(f"Error retrieving user: {e}")
            return None


# MySQL connection settings
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'law_rag_db',
    'port': 8889
}

# Initialize database manager and repository
db_manager = DatabaseManager(db_config)
db_manager.connect()
user_repository = UserRepository(db_manager)




