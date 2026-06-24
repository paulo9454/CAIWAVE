from backend.database import Base, engine

def init_db():
    """
    Safe DB initialization for CAIWAVE system.
    Creates all tables if they do not exist.
    """
    Base.metadata.create_all(bind=engine)
