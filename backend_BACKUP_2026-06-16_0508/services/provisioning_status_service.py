from backend.core.db import db

async def get_provisioning_status(nas_id: str):
    doc = await db.provisioning_logs.find_one(
        {"nas_id": nas_id},
        sort=[("created_at", -1)]
    )

    if not doc:
        return {
            "status": "not_found",
            "latest_status": "not_found",
            "data": None
        }

    doc["_id"] = str(doc["_id"])

    return {
        "status": "success",
        "latest_status": doc.get("status", "generated"),
        "data": doc
    }
