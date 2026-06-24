
async def get_provisioning_status(nas_identifier: str):
    doc = await ProvisioningRepository.collection().find_one(
        {"nas_identifier": nas_identifier},
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
