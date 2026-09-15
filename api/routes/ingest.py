from fastapi import APIRouter, BackgroundTasks, Depends

from api.deps import require_admin
from api.schemas import IngestRequest
from core.pipeline import run_ingest

router = APIRouter(tags=["ingest"])


@router.post("/ingest")
def trigger_ingest(
    payload: IngestRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_admin),
):
    background_tasks.add_task(run_ingest, payload.max_results)
    return {"status": "started", "max_results": payload.max_results}
