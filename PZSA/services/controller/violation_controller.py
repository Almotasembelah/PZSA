from PZSA.data.database_manager import DatabaseManager
from PZSA.data.crud import CRUDViolation
from PZSA.data.entities import Violation
from PZSA.configs import logger
from PZSA.configs.database_cfg import get_settings
import os, cv2
from datetime import datetime

cfg = get_settings()

class ViolationController:
    """
    A controller class for managing violations, add them to database, save violation frames and delete the violations
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the ViolationController.

        Args:
            db_manager (DatabaseManager): An instance of the DatabaseManager.
        """
        self._dm = db_manager
        self._crud_violation = CRUDViolation()

        self._crud_violation.set_db_manager(self._dm)

        self._db_violation = None

        logger.info("Violation Controller initialized.")

    def create_violation(self, **data:dict) -> None:
        """
        Create a new violation in the database.

        Args:
            data (json): Violation data.
        """
        self._db_violation = Violation(**data)
        self._crud_violation.create_violation(self._db_violation)
        logger.info(f"Violation created.")

    def update_violation(self, violation:Violation) -> None:
        raise 'Not Supported'

    
    def read_violation(self, violation_identifier: int) -> None:
        """
        Load a violation from the database.

        Args:
            violation_identifier (int): Violation ID.

        Raises:
            ValueError: If the violation is not found.
        """
        self._db_violation = self._crud_violation.read_violation(violation_identifier)

        if not self._db_violation:
            logger.error(f"Violation not found: {violation_identifier}")
            raise ValueError("Invalid violation identifier.")

        logger.info(f"Violation loaded: {violation_identifier}")

    def delete_violation(self, violation_identifier: int) -> None:
        """
        Delete a violation from the database.

        Args:
            violation_identifier (int): Violation ID.
        """
        violation = self._crud_violation.read_violation(violation_identifier)

        if violation:
            self._crud_violation.delete_violation(violation=violation)
            logger.info(f"Violation deleted: {violation_identifier}")


    def save_frame(self, frame, timestamp):
        """
        Save Violation frame.

        Return:
            path: path of the saved frame.
        """
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        timestamp = timestamp.replace(":", "-").replace(" ", "_")

        root = cfg.VIOLATION_FRAME_FOLDER_PATH
        name = f'frame_{timestamp}.jpg'
        if not os.path.exists(root):
            os.makedirs(root)
        path = os.path.join(root, name)
        succes = cv2.imwrite(path, frame)
        if succes:
            logger.info(f"Violation Frame saved into {path}")
            return path
        else:
            logger.error(f'Failed to save Frame at path {path}!!!')
            return ''


    def save_to_db(self) -> None:
        """
        Commit all changes to the database.

        Raises:
            Exception: If commit fails, a rollback is performed.
        """
        try:
            self._dm.commit()
            logger.info("Changes saved to the database.")
        except Exception as e:
            logger.error(f"Failed to save changes: {e}")
            self._dm.rollback()

    def delete_databse(self) -> None:
        """
        Clear all violations from database.
        """
        self._dm.clear_database()
        logger.info("Violation cleared.")