import logging


async def track_event(db, event: dict):
    """
    Store an analytics event in MongoDB.
    """

    logging.warning("========== ANALYTICS ==========")
    logging.warning("%s", event)

    result = await db.analytics_events.insert_one(event)

    logging.warning("Inserted analytics id=%s", result.inserted_id)
