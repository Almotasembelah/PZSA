from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    JSON,
    create_engine,
)

from PZSA.configs import get_settings

from .base import Base

cfg = get_settings()

class Violation(Base):
    """
    ## Violation Model

    Represents a detected hygiene violation event.

    Each record corresponds to a complete violation episode — starting from
    the moment a worker's hand enters a Region of Interest (ROI) **without a scooper**,
    until the hand returns and subsequently interacts with pizza.

    The model stores frame location, temporal context, timestamp, and
    detection metadata for later review and analysis.

    ---

    ### Stored Fields

    | Field | Type | Description |
    |------|------|-------------|
    | `id` | int | Unique violation identifier |
    | `frame_path` | str | File path to the saved violation frame image |
    | `first_frame_index` | int | Frame index marking the beginning of the violation |
    | `last_frame_index` | int | Frame index marking the confirmed violation |
    | `timestamp` | datetime | Date and time the violation occurred |
    | `boxes` | JSON | Bounding-box coordinates of related objects |
    | `labels` | JSON | Object labels (e.g., hand, scooper, pizza) |

    ---
    """

    __tablename__ = "violations"

    id = Column(Integer, primary_key=True)

    # Path to saved violation frame (image or video snapshot)
    frame_path = Column(String(255), nullable=False)

    # Frame metadata
    first_frame_index = Column(Integer, nullable=True) 
    last_frame_index = Column(Integer, nullable=True) 
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Store detection results as JSON
    boxes = Column(JSON, nullable=False)  
    labels = Column(JSON, nullable=False)       


    def __repr__(self):
        return f"<Violation id={self.id} frame={self.last_frame_index}>"


engine = create_engine(cfg.DATABASE_URL)
Base.metadata.create_all(engine)