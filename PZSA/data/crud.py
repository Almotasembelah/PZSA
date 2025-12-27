from sqlalchemy.orm import Session
from .entities import Violation
from .database_manager import DatabaseManager

from PZSA.configs import logger

class CRUDViolation:
    def __init__(self):
        '''
        # Constructor
        Initializes the CRUDViolation instance, preparing attributes for database interaction.

        **Attributes**:
        - `__em` (DatabaseManager): The database manager instance.
        - `__session` (Session): SQLAlchemy session for database interaction.
        '''
        self.__em: DatabaseManager
        self.__session: Session
        logger.debug("CRUDViolation instance initialized.")

    def set_db_manager(self, em):
        '''
        # Set Database Manager
        Associates a DatabaseManager instance with this object.

        **Args**:
        - `em` (DatabaseManager): The database manager instance.

        **Returns**:
        - `Session`: The SQLAlchemy session object.

        **Example**:
        ```python
        session = crud_violation.set_db_manager(db_manager)
        ```
        '''
        self.__em = em
        self.__session = self.__em.get_session()
        logger.debug("Database manager set for ICRUDViolation.")
        return self.__session

    def create_violation(self, violation: Violation):
        '''
        # Create Violation
        Inserts a new violation into the database.

        **Args**:
        - `violation` (Violation): The violation instance to be added.

        **Returns**:
        - `int`: The ID of the created violation.

        **Raises**:
        - `ValueError`: If the database manager is not set.

        **Example**:
        ```python
        violation_id = crud_violation.create_violation(violation_instance)
        ```
        '''
        if self.__em is not None:
            self.__session.add(violation)
            self.__em.flush()
            logger.info(f"Violation created with ID: {violation.id}")
            return violation.id
        else:
            logger.error("No Database Manager set for ICRUDViolation.")
            raise ValueError("No Database Manager")

    def update_violation(self, violation: Violation):
        '''
        # Update Violation
        Updates an existing violation in the database.

        **Args**:
        - `violation` (Violation): The violation instance to be updated.

        **Returns**:
        - `bool`: `True` if the update was successful.

        **Raises**:
        - `ValueError`: If the database manager is not set.

        **Example**:
        ```python
        success = crud_violation.update_violation(violation_instance)
        ```
        '''
        if self.__em is not None:
            self.__session.add(violation)
            logger.info(f"Violation updated with ID: {violation.id}")
            return True
        else:
            logger.error("No Database Manager set for ICRUDViolation.")
            raise ValueError("No Database Manager")

    def delete_violation(self, violation):
        '''
        # Delete Violation
        Removes a violation from the database.

        **Args**:
        - `violation` (Violation): The violation instance to be deleted.

        **Returns**:
        - `bool`: `True` if the deletion was successful.

        **Raises**:
        - `ValueError`: If the database manager is not set.

        **Example**:
        ```python
        success = crud_violation.delete_violation(violation_instance)
        ```
        '''
        if self.__em is not None:
            self.__session.delete(violation)
            logger.info(f"Violation deleted with ID: {violation.id}")
            return True
        else:
            logger.error("No Database Manager set for ICRUDViolation.")
            raise ValueError("No Database Manager")

    def read_violation(self, violation_id):
        '''
        # Read Violation
        Fetches a violation from the database using its ID.

        **Args**:
        - `violation_id` (int): The ID of the violation to fetch.

        **Returns**:
        - `Violation`: The fetched violation instance.

        **Example**:
        ```python
        violation = crud_violation.read_violation(1)
        ```
        '''
        violation = self.__session.get(Violation, violation_id)
        if violation:
            logger.debug(f"Violation read with ID: {violation_id}")
        else:
            logger.warning(f"Violation not found with ID: {violation_id}")
        return violation
