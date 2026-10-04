from backend.services.provisioning_repository import ProvisioningRepository


async def get_provisioning_status(nas_identifier: str):
    doc = await ProvisioningRepository.find_one(
        {"nas_identifier": nas_identifier}
    )

    if not doc:
        return {
            "status": "not_found",
            "latest_status": "not_found",
            "data": None,
        }

    return {
        "status": "success",
        "latest_status": doc.get("status", "generated"),
        "data": doc,
    }
