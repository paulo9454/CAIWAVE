from core.database import db
from core.database import db
from core.database import db
from core.database import db
from core.database import db


class BaseRepository:
    collection_name = None

    @classmethod
    def collection(cls):
        if not cls.collection_name:
            raise ValueError("collection_name not set")
        return db[cls.collection_name]
