import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.settings import get_settings
from app.workflows.analysis import PreMatchAnalysisWorkflow, execute_analysis_stage


async def run() -> None:
    settings = get_settings()
    client = await Client.connect(settings.TEMPORAL_ADDRESS, namespace=settings.TEMPORAL_NAMESPACE)
    worker = Worker(
        client,
        task_queue="miron-baba-ai",
        workflows=[PreMatchAnalysisWorkflow],
        activities=[execute_analysis_stage],
    )
    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
