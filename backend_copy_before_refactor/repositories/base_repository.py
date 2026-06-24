from backend.core.db import db


class BaseRepository:
    collection_name = None

    @classmethod
    def collection(cls):
        if not cls.collection_name:
            raise ValueError("collection_name not set")
        return getattr(db, cls.collection_name)
