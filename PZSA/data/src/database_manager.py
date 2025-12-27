from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from .base import Base

from PZSA.configs import logger
from PZSA.configs import get_settings

cfg = get_settings()

class DatabaseManager:
    """
    A singleton class to manage database interactions using SQLAlchemy.

    This class centralizes database management to ensure:
    - Thread-safe database sessions.
    - Automatic table creation upon initialization.
    - Efficient handling of transactions with commit, rollback, and flush methods.

    ### Key Features:
    - Ensures a single instance of the manager is used across the application.
    - Provides session factory for thread-safe database operations.
    - Supports clearing the database (useful during testing or reset scenarios).

    ### Attributes:
    - `engine` (`sqlalchemy.engine.Engine`): The SQLAlchemy engine for database connections.
    - `Session` (`sqlalchemy.orm.scoped_session`): A thread-safe session factory for database operations.
    - `Exists` (`bool`): Indicates if an instance of `DatabaseManager` has already been initialized.

    ### Example Usage:
    ```python
    from your_project.database_manager import DatabaseManager

    # Initialize the database manager
    db_manager = DatabaseManager("sqlite:///my_database.db")

    # Get a session
    session = db_manager.get_session()

    # Perform database operations
    session.add(some_entity)
    db_manager.commit()

    # Clean up
    db_manager.close()
    ```
    """

    Exists = False  # Tracks if an instance of the class has been created.

    def __init__(self):
        """
        Initialize the DatabaseManager with a specified database URL.

        ### Args:
        - `db_url` (`str`): The database connection string (default: SQLite `graph_database.db`).

        ### Raises:
        - `ValueError`: If an instance of `DatabaseManager` already exists.
        """
        if not DatabaseManager.Exists:
            DatabaseManager.Exists = True

            # Initialize the database engine
            self.engine = create_engine(cfg.DATABASE_URL)
            logger.info(f"Database engine created with URL: {cfg.DATABASE_URL}")

            # Create a thread-safe session factory
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            logger.info("Thread-safe session factory created.")

            # Automatically create all tables defined in SQLAlchemy models
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created (if they didn't exist).")
        else:
            logger.error("Attempted to initialize a second DatabaseManager instance.")
            raise ValueError("This DatabaseManager has already been initialized.")

    def get_session(self):
        """
        Get or create a thread-safe session.

        ### Returns:
        - `sqlalchemy.orm.Session`: A SQLAlchemy session instance.
        """
        logger.debug("Creating a new database session.")
        return self.Session()

    def close(self):
        """
        Close the current session.

        Ensures that all resources associated with the session are released.
        """
        logger.debug("Closing the current database session.")
        self.Session.remove()

    def flush(self):
        """
        Flush pending changes to the database.

        This operation sends any changes to the database but does not commit them.
        Useful for generating IDs for new entities without committing the transaction.
        """
        logger.debug("Flushing pending changes to the database.")
        self.Session.flush()

    def commit(self):
        """
        Commit all pending changes to the database.

        Use this method to persist changes made during the session.
        """
        try:
            session = self.get_session()
            session.commit()
            logger.info("Changes committed to the database.")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            raise

    def rollback(self):
        """
        Roll back any uncommitted changes in the current transaction.

        Use this method to revert the database to its state before the current transaction.
        """
        try:
            session = self.get_session()
            session.rollback()
            logger.info("Changes rolled back.")
        except Exception as e:
            logger.error(f"Failed to roll back changes: {e}")
            raise

    def clear_database(self):
        """
        Delete all data from all tables in the database.

        **Warning:** This method will permanently delete all records from the database.
        Use with caution in production environments.

        ### Example:
        ```python
        db_manager = DatabaseManager()
        db_manager.clear_database()  # Clears all tables in the database.
        ```
        """
        try:
            with self.Session.begin():
                for table in reversed(Base.metadata.sorted_tables):
                    self.Session.execute(table.delete())
                self.Session.commit()
            logger.warning("All data cleared from the database.")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            raise

    def __del__(self):
        """
        Reset the singleton status when the instance is deleted.

        Allows creating a new `DatabaseManager` instance after the current instance is garbage collected.
        """
        DatabaseManager.Exists = False
        logger.info("DatabaseManager instance deleted and singleton status reset.")