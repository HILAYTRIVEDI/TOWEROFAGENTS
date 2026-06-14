from dataclasses import asdict
from typing import Any

from band.client import BandMessage
from db.queries import QueryRepository


async def sync_message(
    repository: QueryRepository,
    message: BandMessage,
    workflow_id: str,
    org_id: str,
) -> dict[str, Any]:
    return await repository.save_band_message(
        {
            **asdict(message),
            "workflow_id": workflow_id,
            "org_id": org_id,
        }
    )

