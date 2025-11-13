# utils/models.py
"""
Bridges utils with the main database schema.
No duplicate models or engines — all references
point to db/schema.py for a single source of truth.
"""

from db.schema import User, SessionLocal, Base, engine

# Optional: helper to get DB session
def get_db():
    """Provide a database session for utility functions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
