import asyncio
from uuid import uuid4

from temporalio.client import Client

from app.settings import get_settings
from app.workflows.analysis import AnalysisWorkflowInput, PreMatchAnalysisWorkflow


async def main() -> None:
    settings = get_settings()
    client = await Client.connect(
        settings.TEMPORAL_ADDRESS,
        namespace=settings.TEMPORAL_NAMESPACE,
    )
    result = await client.execute_workflow(
        PreMatchAnalysisWorkflow.run,
        AnalysisWorkflowInput(
            run_id="temporal-smoke",
            fixture_id="958ca732-f3ed-5782-8cec-97bcedf941e7",
            cutoff_at="2026-08-22T08:00:00Z",
        ),
        id=f"temporal-smoke-{uuid4()}",
        task_queue="miron-baba-ai",
    )
    print(
        result.state,
        len(result.completed_stage_ids),
        result.completed_stage_ids[0],
        result.completed_stage_ids[-1],
    )


if __name__ == "__main__":
    asyncio.run(main())
