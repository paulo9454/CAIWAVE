from backend.core.database import db


class ProvisioningRepository:
    collection = db.provisioning_logs

    @staticmethod
    def save_sync(record: dict):
        # Motor safe call inside threadpool context already handled by FastAPI
        return db.provisioning_logs.insert_one(record)

    @staticmethod
    def find_one(query: dict):
        return db.provisioning_logs.find_one(query, {"_id": 0})

    @staticmethod
    def find(query: dict, limit: int = 100):
        return db.provisioning_logs.find(query).to_list(limit)


repository = ProvisioningRepository()
